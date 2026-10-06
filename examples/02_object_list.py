# -*- coding: utf-8 -*-
"""
示例 2：查询对象列表 —— 拿到「apiName → 中文显示名」的全量对照。

对应文档：references/03_common/系统接口/对象描述/查询对象列表.md
接口：POST /cgi/crm/v2/object/list

为什么这个接口值得第一个跑：
  * 文档里的对象中文名是**手册作者写的标签**，未必等于你租户里的实际显示名
    （实测同一个对象在两处可以叫不同名字）
  * 所以对接前先拉一份自己租户的清单，后续写代码以它为准

    python 02_object_list.py                 # 打印前 30 个
    python 02_object_list.py --all           # 全部
    python 02_object_list.py --grep 服务      # 按中文名/接口名过滤
    python 02_object_list.py --save objects.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxiaoke_client import FxiaokeClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="打印全部")
    ap.add_argument("--grep", default="", help="按中文名或 apiName 过滤")
    ap.add_argument("--save", default="", help="把全量清单存成 JSON")
    args = ap.parse_args()

    objs = FxiaokeClient().object_list()
    print(f"共 {len(objs)} 个对象\n")

    rows = objs
    if args.grep:
        rows = [o for o in objs
                if args.grep in (o.get("describeDisplayName") or "")
                or args.grep.lower() in (o.get("describeApiName") or "").lower()]
        print(f"匹配「{args.grep}」的 {len(rows)} 个：")

    show = rows if (args.all or args.grep) else rows[:30]
    for o in show:
        active = "" if o.get("isActive", True) else "  (停用)"
        print(f"  {o.get('describeApiName'):36s} {o.get('describeDisplayName')}{active}")
    if len(rows) > len(show):
        print(f"  … 其余 {len(rows) - len(show)} 个（加 --all 看全部）")

    if args.save:
        with open(args.save, "w", encoding="utf-8", newline="\n") as f:
            json.dump(objs, f, ensure_ascii=False, indent=1)
        print(f"\n已存 {args.save}")


if __name__ == "__main__":
    main()
