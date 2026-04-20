"""
JadeGate MCP Proxy — Transparent MCP stdio/SSE proxy with tool call interception.

Sits between an MCP client and server, intercepting JSON-RPC messages:
- tools/list: runs TOFU check on every tool, annotates with live security profile
- tools/call: validates calls through the interceptor before forwarding
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional

from .base import JadeTransport
from ..runtime.interceptor import ToolCallInterceptor, CallVerdict, InterceptResult
from ..trust import TrustOnFirstUse, TOFUAlert

logger = logging.getLogger(__name__)


class JadeMCPProxy(JadeTransport):
    """
    MCP stdio transparent proxy.

    Reads JSON-RPC from stdin, intercepts tools/call and tools/list,
    forwards allowed calls to the upstream MCP server process.

    Accepts either a raw ``interceptor`` or a ``session`` (preferred).
    When a ``session`` is supplied the interceptor is extracted from it.
    """

    def __init__(
        self,
        interceptor: Optional[ToolCallInterceptor] = None,
        upstream_command: Optional[List[str]] = None,
        session=None,           # JadeSession (accepts to avoid circular import)
        server_id: str = "",
    ):
        # Accept session or bare interceptor
        if interceptor is None:
            if session is not None:
                interceptor = session.interceptor
            else:
                # Fallback: build a minimal interceptor with default policy
                from ..policy.policy import JadePolicy
                interceptor = ToolCallInterceptor(policy=JadePolicy.default())

        super().__init__(interceptor)
        self.upstream_command = upstream_command
        self._upstream_process: Optional[subprocess.Popen] = None
        self._running = False
        self._tool_profiles: Dict[str, Dict[str, Any]] = {}

        # Derive a stable server_id from the upstream command when not supplied
        if not server_id and upstream_command:
            # Use the last path component of the first non-flag argument
            for part in reversed(upstream_command):
                if not part.startswith("-"):
                    server_id = part.replace("\\", "/").split("/")[-1]
                    break
        self._server_id = server_id or "unknown_server"

        # TOFU: each proxy instance gets its own manager backed by the shared store
        self._tofu = TrustOnFirstUse()

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Start the proxy and upstream MCP server."""
        if self.upstream_command:
            self._upstream_process = subprocess.Popen(
                self.upstream_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info("Started upstream MCP server: %s", " ".join(self.upstream_command))
        self._running = True
        logger.info("JadeMCPProxy started (server_id=%s)", self._server_id)

    def stop(self) -> None:
        """Stop the proxy and upstream server."""
        self._running = False
        if self._upstream_process:
            self._upstream_process.terminate()
            try:
                self._upstream_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._upstream_process.kill()
            self._upstream_process = None
        logger.info("JadeMCPProxy stopped")

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------ #
    #  Message routing                                                     #
    # ------------------------------------------------------------------ #

    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a single JSON-RPC message.

        Returns:
            Response dict to send back to the client.
        """
        method = message.get("method", "")
        msg_id = message.get("id")

        if method == "tools/list":
            return self._handle_tools_list(message)
        elif method == "tools/call":
            return self._handle_tools_call(message, msg_id)
        else:
            return self._forward_to_upstream(message)

    # ------------------------------------------------------------------ #
    #  tools/list — TOFU check + annotation                               #
    # ------------------------------------------------------------------ #

    def _handle_tools_list(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward tools/list upstream, then run TOFU on every tool in the response.

        First encounter  → baseline recorded, new_tool alert logged at INFO.
        Subsequent calls → description compared against baseline.
                           risk_escalation / capability_change alerts logged at WARNING.
        """
        upstream_response = self._forward_to_upstream(message)

        if "result" not in upstream_response or "tools" not in upstream_response["result"]:
            return upstream_response

        for tool in upstream_response["result"]["tools"]:
            tool_name = tool.get("name", "")
            description = tool.get("description", "")
            input_schema = tool.get("inputSchema")
            tool_id = f"{self._server_id}::{tool_name}"

            # --- TOFU check -------------------------------------------------
            alerts: List[TOFUAlert] = self._tofu.check_tool(
                tool_id=tool_id,
                name=tool_name,
                description=description,
                input_schema=input_schema,
                server_id=self._server_id,
            )

            for alert in alerts:
                if alert.alert_type == "new_tool":
                    logger.info(
                        "[JadeGate] %s  risk=%s",
                        alert.message,
                        alert.new_value,
                    )
                else:
                    logger.warning(
                        "[JadeGate] TOFU ALERT [%s] %s",
                        alert.alert_type.upper(),
                        alert.message,
                    )

            # --- Build jade_security from TOFU cert -------------------------
            cert = self._tofu.get_baseline(tool_id)
            if cert:
                risk_level = cert.risk_profile.level
                capabilities = cert.risk_profile.capabilities
            else:
                risk_level = "unknown"
                capabilities = []

            profile: Dict[str, Any] = {
                "tool_name": tool_name,
                "risk_level": risk_level,
                "capabilities": capabilities,
                "jade_verified": True,
                "tofu_alerts": [a.to_dict() for a in alerts],
            }

            tool["jade_security"] = profile
            self._tool_profiles[tool_name] = profile

        return upstream_response

    # ------------------------------------------------------------------ #
    #  tools/call — intercept + forward                                   #
    # ------------------------------------------------------------------ #

    def _handle_tools_call(
        self, message: Dict[str, Any], msg_id: Any
    ) -> Dict[str, Any]:
        """Intercept, validate, then forward or reject a tool call."""
        params = message.get("params", {})
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        result = self.intercept_call(tool_name, tool_args)

        if result.verdict == CallVerdict.DENY:
            logger.warning("Tool call DENIED: %s — %s", tool_name, result.reason)
            self.report_result(tool_name, tool_args, success=False, error=result.reason)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32600,
                    "message": f"JadeGate: call denied — {result.reason}",
                    "data": result.to_dict(),
                },
            }

        if result.verdict == CallVerdict.NEED_APPROVAL:
            logger.info("Tool call NEEDS APPROVAL: %s", tool_name)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32001,
                    "message": f"JadeGate: human approval required for '{tool_name}'",
                    "data": result.to_dict(),
                },
            }

        # ALLOW — forward to upstream
        upstream_response = self._forward_to_upstream(message)
        success = "error" not in upstream_response
        error_msg = upstream_response.get("error", {}).get("message") if not success else None
        self.report_result(
            tool_name, tool_args,
            result=upstream_response.get("result"),
            success=success, error=error_msg,
        )
        return upstream_response

    # ------------------------------------------------------------------ #
    #  Upstream I/O                                                        #
    # ------------------------------------------------------------------ #

    def _forward_to_upstream(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Forward a message to the upstream MCP server via stdio."""
        if (
            not self._upstream_process
            or not self._upstream_process.stdin
            or not self._upstream_process.stdout
        ):
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": "No upstream MCP server connected"},
            }

        try:
            msg_bytes = (json.dumps(message) + "\n").encode("utf-8")
            self._upstream_process.stdin.write(msg_bytes)
            self._upstream_process.stdin.flush()

            line = self._upstream_process.stdout.readline()
            if not line:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {"code": -32603, "message": "Upstream server closed"},
                }
            return json.loads(line.decode("utf-8"))
        except Exception as e:
            logger.error("Upstream communication error: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"Upstream error: {e}"},
            }

    # ------------------------------------------------------------------ #
    #  Standalone stdin loop                                               #
    # ------------------------------------------------------------------ #

    def process_stdin_loop(self) -> None:
        """
        Main loop: read JSON-RPC from stdin, process, write to stdout.
        Used when running as a standalone proxy process.
        """
        logger.info("Starting stdin processing loop")
        while self._running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                message = json.loads(line.strip())
                response = self.handle_message(message)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON from stdin: %s", e)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Error in stdin loop: %s", e)
        self.stop()

    # ------------------------------------------------------------------ #
    #  Accessors                                                           #
    # ------------------------------------------------------------------ #

    @property
    def tofu_alerts(self) -> List[TOFUAlert]:
        """All TOFU alerts raised during this proxy session."""
        return self._tofu.alerts

    @property
    def server_id(self) -> str:
        return self._server_id
