# -*- coding: utf-8 -*-
"""
示例 4：查询对象描述（字段清单）。

对应文档：references/03_common/系统接口/对象描述/查询对象描述.md
接口：POST /cgi/crm/v2/object/describe

用途：写 create/update 之前，先确认字段的 api_name、类型、是否必填。
比翻文档快，而且**反映的是你租户里的真实字段**（自定义字段也能看到）。

    python 04_object_describe.py --object AccountObj
    python 04_object_describe.py --object AccountObj --grep 电话
    python 04_object_describe.py --object AccountObj --save describe.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxiaoke_client import FxiaokeClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--object", default="AccountObj")
    ap.add_argument("--grep", default="", help="按字段 apiName / 中文名过滤")
    ap.add_argument("--detail", action="store_true", help="包含从对象")
    ap.add_argument("--save", default="")
    ap.add_argument("--limit", type=int, default=60)
    args = ap.parse_args()

    c = FxiaokeClient()
    d = c.call("/cgi/crm/v2/object/describe",
               {"includeNull": True, "includeDetail": args.detail,
                "data": {"apiName": args.object}})
    desc = (d.get("data") or {}).get("describe") or {}

    if args.save:
        with open(args.save, "w", encoding="utf-8", newline="\n") as f:
            json.dump(desc, f, ensure_ascii=False, indent=1)
        print(f"完整描述已存 {args.save}")

    # ⚠️ describe 的响应**没有顶层显示名**，且字段名是 snake_case
    #    （api_name / is_required），与 object/list 的 camelCase 不一致。
    #    中文显示名要从 object/list 拿。
    name = ""
    try:
        name = next((o.get("describeDisplayName", "") for o in c.object_list()
                     if o.get("describeApiName") == args.object), "")
    except Exception:  # noqa: BLE001
        pass

    fields = desc.get("fields") or {}
    print(f"对象 {desc.get('api_name') or args.object}"
          + (f"  显示名「{name}」" if name else "")
          + f"  字段 {len(fields)} 个\n")

    rows = []
    for api, f in fields.items():
        cn = f.get("label") or f.get("display_name") or ""
        if args.grep and args.grep not in api and args.grep not in str(cn):
            continue
        rows.append((api, cn, f.get("type"), f.get("is_required")))

    for api, cn, typ, req in rows[: args.limit]:
        flag = "必填" if req else "  "
        print(f"  {api:32s} {str(cn):20s} {str(typ):16s} {flag}")
    if len(rows) > args.limit:
        print(f"  … 其余 {len(rows) - args.limit} 个（用 --limit 调整）")
    if not rows:
        print("  （没有匹配字段；用 --save 导出完整描述看看结构）")


if __name__ == "__main__":
    main()
