# -*- coding: utf-8 -*-
"""
示例 5：创建对象。

对应文档：references/02_object/<模块>/<对象>/创建*对象.md
接口：POST /cgi/crm/v2/data/create

⚠️ 这会**真的写数据**。所以默认只做 dry-run（打印将要发送的报文，不发出）。
   确认无误后加 --yes 才会真正创建。

请求体结构：
  {
    "triggerApprovalFlow": true,     # 是否触发审批流，不传默认 true
    "triggerWorkFlow": true,         # 是否触发工作流，不传默认 true
    "data": {
      "object_data": {
        "dataObjectApiName": "AccountObj",
        "name": "示例客户",
        ...其他字段
      }
    }
  }

    python 05_create_object.py --object AccountObj --field name=示例客户
    python 05_create_object.py --object AccountObj --field name=示例客户 --yes
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
    ap.add_argument("--field", action="append", metavar="K=V",
                    help="字段，可重复：--field name=示例客户 --field phone=13800000000")
    ap.add_argument("--no-approval", action="store_true", help="不触发审批流")
    ap.add_argument("--no-workflow", action="store_true", help="不触发工作流")
    ap.add_argument("--yes", action="store_true", help="确认真的写数据")
    args = ap.parse_args()

    object_data = {"dataObjectApiName": args.object}
    for kv in (args.field or []):
        if "=" not in kv:
            raise SystemExit(f"--field 需要 K=V 形式，收到：{kv}")
        k, v = kv.split("=", 1)
        object_data[k.strip()] = v

    payload = {"data": {"object_data": object_data},
               "triggerApprovalFlow": not args.no_approval,
               "triggerWorkFlow": not args.no_workflow}

    print("POST /cgi/crm/v2/data/create")
    print(json.dumps(payload, ensure_ascii=False, indent=1))

    if not args.yes:
        print("\n[DRY-RUN] 未发送。确认后加 --yes 真正创建。")
        return

    d = FxiaokeClient().call("/cgi/crm/v2/data/create", payload)
    print("\n结果：", json.dumps(
        {k: v for k, v in d.items()
         if k in ("errorCode", "errorMessage", "errorDescription", "traceId", "dataId")},
        ensure_ascii=False))
    if d.get("errorCode") == 0:
        # ⚠️ 新建记录的 id 在**响应的顶层** `dataId`，不在 data 里
        print("新建记录 id：", d.get("dataId"))


if __name__ == "__main__":
    main()
