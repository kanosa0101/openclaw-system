#!/usr/bin/env python3
"""脱敏处理 openclaw.json 中的 token 和密钥"""
import json, sys, re

src = sys.argv[1]
dst = sys.argv[2]

with open(src) as f:
    data = json.load(f)

def sanitize(obj):
    if isinstance(obj, dict):
        return {k: "***REDACTED***" if any(s in k.lower() for s in ["token","secret","key","password","pat"]) else sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(i) for i in obj]
    return obj

sanitized = sanitize(data)
with open(dst, "w") as f:
    json.dump(sanitized, f, indent=2, ensure_ascii=False)
print(f"✅ 脱敏完成: {dst}")
