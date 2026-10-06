# -*- coding: utf-8 -*-
"""
示例 6：审批流流程完成（同意 / 拒绝）。

对应文档：references/03_common/流程与规则/审批流程/审批流流程完成.md
接口：POST /cgi/crm/approvalTask/action

请求参数：
  taskId      流程任务 Id（从待办列表或审批流实例里取）
  opinion     意见内容
  actionType  agree（同意）| reject（拒绝）

⚠️ 这会**真的推进审批流**。默认 dry-run，加 --yes 才发送。

    python 06_approval_action.py --task-id <taskId> --opinion 同意
    python 06_approval_action.py --task-id <taskId> --opinion 不同意 --action reject --yes

找不到 taskId？审批流实例查询见：
  references/03_common/流程与规则/审批流程/根据条件查询审批流实例数据列表.md
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxiaoke_client import FxiaokeClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--opinion", required=True)
    ap.add_argument("--action", choices=["agree", "reject"], default="agree")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    payload = {"taskId": args.task_id, "opinion": args.opinion, "actionType": args.action}
    print("POST /cgi/crm/approvalTask/action")
    print(json.dumps(payload, ensure_ascii=False, indent=1))

    if not args.yes:
        print("\n[DRY-RUN] 未发送。确认后加 --yes 真正提交审批动作。")
        return

    d = FxiaokeClient().call("/cgi/crm/approvalTask/action", payload)
    print("\n结果：", json.dumps(
        {k: v for k, v in d.items()
         if k in ("errorCode", "errorMessage", "errorDescription", "traceId")},
        ensure_ascii=False))
    print("\n注意：返回的 errorMessage 不要拿来做逻辑判断（官方说明，措辞会变），"
          "只认 errorCode。")


if __name__ == "__main__":
    main()
