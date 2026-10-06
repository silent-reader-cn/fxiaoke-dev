# -*- coding: utf-8 -*-
"""
示例 7：作废 → 删除（纷享销客没有直接硬删除）。

对应文档：
  references/02_object/<模块>/<对象>/作废*对象信息.md      → POST /cgi/crm/v2/data/invalid
  references/02_object/<模块>/<对象>/删除已作废的*对象信息.md → POST /cgi/crm/v2/data/delete

两步走：
  1) data/invalid  作废（软删）  参数 data.object_data_id
  2) data/delete   删除已作废    参数 data.idList（数组）

⚠️ 不可逆。默认 dry-run，加 --yes 才发送。

    python 07_invalid_and_delete.py --object AccountObj --id 6ac45f8e402caf00071ae0f3
    python 07_invalid_and_delete.py --object AccountObj --id <id> --yes
    python 07_invalid_and_delete.py --object AccountObj --id <id> --yes --only-invalid
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
    ap.add_argument("--id", action="append", required=True, help="记录 id，可重复")
    ap.add_argument("--only-invalid", action="store_true", help="只作废，不删除")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    ids = args.id
    # ⚠️ 实测两个坑（文档没说清）：
    #   1) data/invalid 的 object_data_id 只认**单个 id**。文档写的是「数据id列表」，
    #      但示例给的是字符串；传数组不报错、也**只作废第一个**。
    #   2) data/delete 对**未作废**的记录会返回 errorCode=0 但**不删**（静默部分失败）。
    #      所以必须逐个作废，作废完再批量删除。
    invalid_bodies = [{"data": {"object_data_id": i, "dataObjectApiName": args.object}}
                      for i in ids]
    delete_body = {"data": {"idList": ids, "dataObjectApiName": args.object}}

    print(f"① POST /cgi/crm/v2/data/invalid   （逐个作废 {len(ids)} 条）")
    print(json.dumps(invalid_bodies[0], ensure_ascii=False, indent=1))
    if not args.only_invalid:
        print(f"\n② POST /cgi/crm/v2/data/delete   （批量删除 {len(ids)} 条）")
        print(json.dumps(delete_body, ensure_ascii=False, indent=1))

    if not args.yes:
        print("\n[DRY-RUN] 未发送。确认后加 --yes。")
        return

    c = FxiaokeClient()
    bad = []
    for body in invalid_bodies:
        r = c.call("/cgi/crm/v2/data/invalid", body)
        if r.get("errorCode") != 0:
            bad.append((body["data"]["object_data_id"], r.get("errorCode"),
                        r.get("errorMessage")))
    print(f"\n作废：成功 {len(ids) - len(bad)}/{len(ids)}"
          + (f"，失败 {bad}" if bad else ""))
    if args.only_invalid:
        return

    d2 = c.call("/cgi/crm/v2/data/delete", delete_body)
    print("删除：", json.dumps(
        {k: d2.get(k) for k in ("errorCode", "errorMessage", "errorDescription")},
        ensure_ascii=False))
    print("\n⚠️ 删除返回 0 不代表全删了。请再查一次确认（未作废的记录会被静默跳过）。")


if __name__ == "__main__":
    main()
