#!/usr/bin/env python3
"""
💠 JadeGate Community Signer
=============================
任何人都可以用自己的密钥给 skill 盖章。
社区签名不等于官方认证，但积累足够多 = 社区认证。

信任层级:
  💠 Root Seal      — 项目创始人，最高权威
  🔷 Org Seal       — Root 授权的组织
  🔹 Community Seal — 任何人，积累 5+ 个 = Community Verified
  ❌ Revoked        — 被 Root 撤销的签名者

用法:
  # 第一次：生成你的社区密钥对
  python jade_community_sign.py keygen

  # 给 skill 盖章
  python jade_community_sign.py sign jade_skills/mcp/mcp_brave_search.json

  # 查看一个 skill 的所有签名
  python jade_community_sign.py check jade_skills/mcp/mcp_brave_search.json
"""

import os
import sys
import json
import hashlib
import base64
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jade_keygen_root import _publickey, _signature, _checkvalid


def cmd_keygen():
    """Generate a community keypair."""
    print("\n  💠 生成社区签名密钥\n")
    
    name = input("  你的名字/昵称: ").strip()
    if not name:
        print("  ❌ 名字不能为空")
        sys.exit(1)
    
    email = input("  邮箱 (可选，直接回车跳过): ").strip()
    
    # Generate keypair
    seed = os.urandom(32)
    pk = _publickey(seed)
    
    sk_b64 = base64.b64encode(seed).decode()
    pk_b64 = base64.b64encode(pk).decode()
    fp = base64.b64encode(hashlib.sha256(pk).digest()).decode()
    
    private_key = f"jade-sk-community-{sk_b64}"
    public_key = f"jade-pk-community-{pk_b64}"
    
    # Save public key profile
    profile = {
        "jade_signer": "community",
        "version": "1.0.0",
        "name": name,
        "email": email or None,
        "public_key": public_key,
        "fingerprint": f"SHA256:{fp}",
        "created": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trust_level": "community",
        "skills_signed": 0
    }
    
    # Save to community_signers/
    os.makedirs("community_signers", exist_ok=True)
    safe_name = name.lower().replace(" ", "_")[:20]
    profile_path = f"community_signers/{safe_name}.json"
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)
    
    print(f"\n  ✅ 密钥已生成！")
    print(f"\n  ╔══════════════════════════════════════════════════════╗")
    print(f"  ║  🔑 你的私钥（保存好，不要分享！）                  ║")
    print(f"  ╚══════════════════════════════════════════════════════╝")
    print(f"  {private_key}")
    print(f"\n  指纹: SHA256:{fp}")
    print(f"  档案: {profile_path}")
    print(f"\n  下一步:")
    print(f"  1. 保存好你的私钥")
    print(f"  2. 提交 {profile_path} 到仓库（PR）")
    print(f"  3. 用 jade_community_sign.py sign <skill.json> 给 skill 盖章")
    print()


def cmd_sign(skill_path):
    """Sign a skill with community key."""
    if not os.path.exists(skill_path):
        print(f"  ❌ 文件不存在: {skill_path}")
        sys.exit(1)
    
    private_key = input("  输入你的社区私钥 (jade-sk-community-...): ").strip()
    if not private_key.startswith("jade-sk-community-"):
        print("  ❌ 无效的社区私钥格式")
        sys.exit(1)
    
    seed = base64.b64decode(private_key.split("-", 3)[3])
    pk = _publickey(seed)
    pk_b64 = base64.b64encode(pk).decode()
    fp = base64.b64encode(hashlib.sha256(pk).digest()).decode()
    
    # Load skill
    with open(skill_path) as f:
        skill = json.load(f)
    
    # Compute content hash (exclude signatures)
    content = {k: v for k, v in skill.items() if k not in ("jade_signature", "community_signatures")}
    content_bytes = json.dumps(content, sort_keys=True, separators=(',', ':')).encode()
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    
    # Sign
    sig = _signature(content_bytes, seed, pk)
    sig_b64 = base64.b64encode(sig).decode()
    
    # Verify our own signature
    assert _checkvalid(sig, content_bytes, pk)
    
    # Add to community_signatures
    new_sig = {
        "signer_fingerprint": f"SHA256:{fp}",
        "public_key": f"jade-pk-community-{pk_b64}",
        "content_hash": f"sha256:{content_hash}",
        "signature": sig_b64,
        "signed_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trust_level": "community"
    }
    
    if "community_signatures" not in skill:
        skill["community_signatures"] = []
    
    # Check if already signed by this key
    existing = [s for s in skill["community_signatures"] if s["signer_fingerprint"] == f"SHA256:{fp}"]
    if existing:
        print(f"  ⚠️ 你已经签过这个 skill 了")
        return
    
    skill["community_signatures"].append(new_sig)
    
    with open(skill_path, 'w') as f:
        json.dump(skill, f, indent=2)
    
    total = len(skill["community_signatures"])
    verified = "✅ Community Verified!" if total >= 5 else f"({total}/5 toward Community Verified)"
    
    print(f"\n  🔹 已签名: {skill.get('skill_id', 'unknown')}")
    print(f"  签名者: SHA256:{fp}")
    print(f"  社区签名数: {total} {verified}")
    print()


def cmd_check(skill_path):
    """Check all signatures on a skill."""
    with open(skill_path) as f:
        skill = json.load(f)
    
    sid = skill.get("skill_id", "unknown")
    print(f"\n  💠 签名状态: {sid}\n")
    
    # Root/official signature
    if "jade_signature" in skill:
        sig = skill["jade_signature"]
        print(f"  💠 Root Seal")
        print(f"     Hash: {sig.get('content_hash', 'N/A')[:40]}...")
        print(f"     Signed: {sig.get('signed_at', 'N/A')}")
    else:
        print(f"  ⬜ No Root Seal")
    
    # Community signatures
    community = skill.get("community_signatures", [])
    if community:
        verified = len(community) >= 5
        status = "✅ Community Verified" if verified else f"🔹 {len(community)}/5"
        print(f"\n  {status} Community Signatures:")
        
        # Load known signers
        known = {}
        if os.path.exists("community_signers"):
            for f in os.listdir("community_signers"):
                if f.endswith(".json"):
                    with open(f"community_signers/{f}") as fh:
                        p = json.load(fh)
                    known[p.get("fingerprint", "")] = p.get("name", "Unknown")
        
        for s in community:
            fp = s["signer_fingerprint"]
            name = known.get(fp, "Unknown")
            print(f"     🔹 {name} ({fp[:20]}...) — {s.get('signed_at', 'N/A')}")
    else:
        print(f"\n  ⬜ No Community Signatures")
    
    # Revocation check
    revoked_path = "jade_schema/revoked_signers.json"
    if os.path.exists(revoked_path):
        with open(revoked_path) as f:
            revoked = json.load(f)
        revoked_fps = set(revoked.get("revoked", []))
        for s in community:
            if s["signer_fingerprint"] in revoked_fps:
                print(f"\n  ❌ REVOKED: {s['signer_fingerprint']}")
    
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "keygen":
        cmd_keygen()
    elif cmd == "sign" and len(sys.argv) >= 3:
        cmd_sign(sys.argv[2])
    elif cmd == "check" and len(sys.argv) >= 3:
        cmd_check(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
