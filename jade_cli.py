#!/usr/bin/env python3
"""
💠 JadeGate CLI — jade command
==============================
Agent-native skill discovery, verification, and execution.

Usage:
  jade help                     Show this help
  jade status                   Show JadeGate status and stats
  jade list [--type mcp|tool]   List all verified skills
  jade search <query>           Search skills by keyword
  jade info <skill_id>          Show skill details
  jade verify <file|dir>        Verify skill(s) against 5 layers
  jade run <skill_id> [params]  Execute a verified skill (dry-run by default)
  jade catalog                  Generate/update CATALOG.md
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Add jade_core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_skill_dirs():
    """Find skill directories relative to this script."""
    base = Path(__file__).parent
    return [base / "jade_skills" / "mcp", base / "jade_skills" / "tools"]


def load_all_skills():
    """Load all skill JSON files."""
    skills = []
    for d in get_skill_dirs():
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix == ".json" and not f.name.endswith(".sig.json"):
                try:
                    with open(f) as fh:
                        s = json.load(fh)
                    s["_path"] = str(f)
                    s["_type"] = "MCP" if "mcp" in str(d) else "Tool"
                    skills.append(s)
                except Exception:
                    pass
    return skills


def cmd_help():
    print("""
💠 JadeGate CLI v1.0.0
======================

Commands:
  jade help                     Show this help
  jade status                   Show JadeGate status and stats
  jade list [--type mcp|tool]   List all verified skills
  jade search <query>           Fuzzy search skills by keyword
  jade info <skill_id>          Show detailed skill info (JSON)
  jade verify <path>            Run 5-layer verification
  jade run <skill_id> [--params '{"key":"val"}']
                                Execute a skill (dry-run by default)

Agent Integration:
  jade search --json <query>    Machine-readable JSON output
  jade info --json <skill_id>   Machine-readable skill details
  jade list --json              Full catalog as JSON array

Examples:
  jade search "web search"
  jade info mcp_brave_search
  jade verify ./my_skill.json
  jade list --type mcp
""")


def cmd_status():
    skills = load_all_skills()
    mcp = sum(1 for s in skills if s["_type"] == "MCP")
    tools = sum(1 for s in skills if s["_type"] == "Tool")
    signed = sum(1 for s in skills if "jade_signature" in s)
    unsigned = len(skills) - signed

    # Collect unique tags
    all_tags = set()
    for s in skills:
        all_tags.update(s.get("metadata", {}).get("tags", []))

    # Collect unique domains
    all_domains = set()
    for s in skills:
        for d in s.get("security", {}).get("network_whitelist", []):
            all_domains.add(d)

    print(f"""
💠 JadeGate Status
==================
Skills:     {len(skills)} total ({mcp} MCP + {tools} Tools)
Signed:     {signed} 💠 sealed
Unsigned:   {unsigned}
Tags:       {len(all_tags)} unique categories
Domains:    {len(all_domains)} whitelisted endpoints
Engine:     5-layer deterministic verification
Crypto:     Ed25519 signature chain
Runtime:    Local (zero cloud dependency)
""")


def cmd_list(args):
    skills = load_all_skills()
    if args.type:
        skills = [s for s in skills if s["_type"].lower() == args.type.lower()]

    if args.json:
        out = []
        for s in skills:
            out.append({
                "skill_id": s["skill_id"],
                "type": s["_type"],
                "name": s.get("metadata", {}).get("name", ""),
                "description": s.get("metadata", {}).get("description", ""),
                "tags": s.get("metadata", {}).get("tags", []),
                "signed": "jade_signature" in s,
            })
        print(json.dumps(out, indent=2))
        return

    print(f"\n💠 {len(skills)} Skills\n")
    for s in skills:
        meta = s.get("metadata", {})
        seal = "💠" if "jade_signature" in s else "  "
        tags = ", ".join(meta.get("tags", [])[:3])
        print(f"  {seal} [{s['_type']:4}] {s['skill_id']:<40} {tags}")
    print()


def cmd_search(args):
    query = args.query.lower()
    skills = load_all_skills()

    results = []
    for s in skills:
        meta = s.get("metadata", {})
        searchable = " ".join([
            s.get("skill_id", ""),
            meta.get("name", ""),
            meta.get("description", ""),
            " ".join(meta.get("tags", [])),
        ]).lower()

        # Simple relevance scoring
        score = 0
        for word in query.split():
            if word in s.get("skill_id", "").lower():
                score += 3
            if word in meta.get("name", "").lower():
                score += 2
            if word in " ".join(meta.get("tags", [])).lower():
                score += 2
            if word in meta.get("description", "").lower():
                score += 1

        if score > 0:
            results.append((score, s))

    results.sort(key=lambda x: -x[0])

    if args.json:
        out = []
        for score, s in results[:20]:
            out.append({
                "skill_id": s["skill_id"],
                "type": s["_type"],
                "name": s.get("metadata", {}).get("name", ""),
                "description": s.get("metadata", {}).get("description", ""),
                "tags": s.get("metadata", {}).get("tags", []),
                "relevance": score,
            })
        print(json.dumps(out, indent=2))
        return

    if not results:
        print(f"\n  No skills found for '{args.query}'")
        return

    print(f"\n💠 {len(results)} results for '{args.query}':\n")
    for score, s in results[:20]:
        meta = s.get("metadata", {})
        seal = "💠" if "jade_signature" in s else "  "
        print(f"  {seal} {s['skill_id']:<40} {meta.get('description', '')[:50]}")
    print()


def cmd_info(args):
    skills = load_all_skills()
    match = [s for s in skills if s["skill_id"] == args.skill_id]

    if not match:
        # Fuzzy match
        match = [s for s in skills if args.skill_id in s["skill_id"]]

    if not match:
        print(f"\n  ❌ Skill '{args.skill_id}' not found")
        return

    s = match[0]
    if args.json:
        print(json.dumps({k: v for k, v in s.items() if not k.startswith("_")}, indent=2))
        return

    meta = s.get("metadata", {})
    sec = s.get("security", {})
    sig = s.get("jade_signature", {})

    print(f"""
💠 Skill: {s['skill_id']}
{'=' * 50}
Name:        {meta.get('name', 'N/A')}
Type:        {s['_type']}
Version:     {meta.get('version', 'N/A')}
Author:      {meta.get('author', 'N/A')}
Description: {meta.get('description', 'N/A')}
Tags:        {', '.join(meta.get('tags', []))}

Security:
  Sandbox:   {sec.get('sandbox_level', 'N/A')}
  Domains:   {', '.join(sec.get('network_whitelist', [])) or 'none'}
  Timeout:   {sec.get('max_execution_time_ms', 'N/A')}ms

Signature:   {'💠 Sealed' if sig else '⚠️ Unsigned'}""")

    if sig:
        print(f"  Signer:    {sig.get('signer_fingerprint', 'N/A')}")
        print(f"  Hash:      {sig.get('content_hash', 'N/A')[:40]}...")
        print(f"  Signed at: {sig.get('signed_at', 'N/A')}")

    # Show DAG
    dag = s.get("execution_dag", {})
    nodes = dag.get("nodes", [])
    edges = dag.get("edges", [])
    print(f"\nExecution DAG: {len(nodes)} nodes, {len(edges)} edges")
    for n in nodes:
        print(f"  → {n['id']} ({n.get('type', 'unknown')})")
    print()


def cmd_verify(args):
    from jade_core.validator import JadeValidator
    v = JadeValidator()

    path = Path(args.path)
    files = []
    if path.is_dir():
        files = sorted(path.glob("**/*.json"))
        files = [f for f in files if not f.name.endswith(".sig.json")]
    elif path.is_file():
        files = [path]
    else:
        print(f"  ❌ Path not found: {args.path}")
        sys.exit(1)

    passed = failed = 0
    for f in files:
        r = v.validate_file(str(f))
        if r.valid:
            passed += 1
            warns = [i for i in r.issues if i.severity.value == "warning"]
            if warns:
                print(f"  ✅ {f.name} (⚠️ {len(warns)} warnings)")
            else:
                print(f"  ✅ {f.name}")
        else:
            failed += 1
            print(f"  ❌ {f.name}")
            for i in r.issues:
                if i.severity.value == "error":
                    print(f"     {i.code}: {i.message}")

    print(f"\n💠 {passed} passed, {failed} failed out of {len(files)}")
    if failed > 0:
        sys.exit(1)


def cmd_run(args):
    skills = load_all_skills()
    match = [s for s in skills if s["skill_id"] == args.skill_id]
    if not match:
        print(f"  ❌ Skill '{args.skill_id}' not found")
        sys.exit(1)

    s = match[0]
    print(f"\n💠 Dry-run: {s['skill_id']}")
    print(f"  Would execute {len(s.get('execution_dag', {}).get('nodes', []))} nodes")

    if args.params:
        params = json.loads(args.params)
        print(f"  Params: {json.dumps(params, indent=2)}")

    print(f"\n  ⚠️ Actual execution not yet implemented.")
    print(f"  Skills define WHAT to do; your agent runtime decides HOW.")
    print()


def main():
    parser = argparse.ArgumentParser(prog="jade", description="💠 JadeGate CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("help", help="Show help")
    sub.add_parser("status", help="Show status")

    p_list = sub.add_parser("list", help="List skills")
    p_list.add_argument("--type", choices=["mcp", "tool"])
    p_list.add_argument("--json", action="store_true")

    p_search = sub.add_parser("search", help="Search skills")
    p_search.add_argument("query")
    p_search.add_argument("--json", action="store_true")

    p_info = sub.add_parser("info", help="Skill details")
    p_info.add_argument("skill_id")
    p_info.add_argument("--json", action="store_true")

    p_verify = sub.add_parser("verify", help="Verify skill(s)")
    p_verify.add_argument("path")

    p_run = sub.add_parser("run", help="Run a skill (dry-run)")
    p_run.add_argument("skill_id")
    p_run.add_argument("--params", default=None)

    args = parser.parse_args()

    if not args.command or args.command == "help":
        cmd_help()
    elif args.command == "status":
        cmd_status()
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
