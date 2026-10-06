# -*- coding: utf-8 -*-
"""
示例 1：取 accessToken（客户端凭证模式）。

对应文档：references/01_start/OAuth授权认证/客户端凭证模式.md

关键点（实测）：
  * 有效期 7200 秒，但**必须缓存 6600 秒**再刷新，否则可能拿到即将过期的 token
  * 0–6600 秒内重复调用返回同一个 token；6600–7200 秒之间返回新的（新旧都可用）
  * 该接口**每分钟不超过 10 次、不可并发调用**，建议按错误码 20016 加重试
  * 响应同时返回 camelCase 与 snake_case 两套字段（accessToken / access_token）

    python 01_get_token.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxiaoke_client import FxiaokeClient  # noqa: E402


def main():
    c = FxiaokeClient()
    t = c.fetch_token()

    def mask(v, keep=6):
        v = str(v or "")
        return v[:keep] + "*" * max(0, len(v) - keep)

    print("域名      :", c.domain)
    print("accessToken:", mask(t["accessToken"]), "(已按 6600 秒缓存)")
    print("ea        :", t["ea"], " ← 后面要放进 x-fs-ea 请求头")
    print("openUserId:", mask(t["openUserId"]))
    print("expiresIn :", t["expiresIn"], "秒")
    print("tokenType :", t["tokenType"])
    print()
    print("注意：openUserId（FSCID_xxx）**不能**当 x-fs-userid 用，")
    print("      x-fs-userid 要填应用可见范围内的数字员工ID。")


if __name__ == "__main__":
    main()
