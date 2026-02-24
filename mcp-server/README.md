<div align="center">

# 💠 @jadegate/mcp-server

**JadeGate MCP Server — Deterministic security verification for AI agent skills.**

[![npm](https://img.shields.io/npm/v/@jadegate/mcp-server)](https://www.npmjs.com/package/@jadegate/mcp-server)
[![License: BSL-1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](https://github.com/JadeGate/jade-core/blob/main/LICENSE)

[中文文档](./README_CN.md)

</div>

## What is this?

An MCP (Model Context Protocol) server that exposes [JadeGate](https://github.com/JadeGate/jade-core) security verification capabilities to AI agents and IDEs like Claude Desktop and Cursor.

JadeGate provides 5-layer deterministic verification for AI agent skills — no cloud, no LLM, no token cost.

## Quick Start

```bash
npx @jadegate/mcp-server
```

Or install globally:

```bash
npm install -g @jadegate/mcp-server
jadegate-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `jade_verify` | Verify a skill JSON — returns 5-layer validation results with pass/fail and confidence score |
| `jade_search` | Search the skill registry by keyword, category, or trust level |
| `jade_info` | Get detailed info for a specific skill by ID |
| `jade_list` | List all registered skills with optional category filter |
| `jade_stats` | Get registry statistics (total skills, categories, trust distribution) |
| `jade_dag` | Generate a dependency graph for a skill in Mermaid, D3, or DOT format |

## Resources

| URI | Description |
|-----|-------------|
| `jadegate://registry` | Full skill registry (JSON) |
| `jadegate://ca` | JadeGate Root CA certificate |

## IDE Integration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jadegate": {
      "command": "npx",
      "args": ["-y", "@jadegate/mcp-server"]
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "jadegate": {
      "command": "npx",
      "args": ["-y", "@jadegate/mcp-server"]
    }
  }
}
```

## Python Alternative

```bash
pip install jadegate
jade mcp-serve
```

Same MCP protocol, same tools — just runs via the Python package instead.

## How It Works

1. AI agent calls `jade_verify` with a skill JSON
2. MCP server invokes JadeGate's 5-layer verification pipeline
3. Returns deterministic pass/fail with detailed layer results
4. Agent decides whether to trust and execute the skill

All verification runs locally. No network calls. No LLM inference. Pure mathematical checks:
- Schema validation
- Signature & provenance verification
- Permission boundary analysis
- Dependency chain audit
- Behavioral constraint checking

## Requirements

- Node.js >= 18
- JadeGate Python package (`pip install jadegate`) must be available in PATH

## License

[BSL-1.1](https://github.com/JadeGate/jade-core/blob/main/LICENSE) — See [jade-core](https://github.com/JadeGate/jade-core) for details.
