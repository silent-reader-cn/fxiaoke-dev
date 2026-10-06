# -*- coding: utf-8 -*-
"""
示例 3：按条件查询对象列表。

对应文档：references/02_object/<模块>/<对象>/根据条件查询*对象的列表.md
接口：POST /cgi/crm/v2/data/query

查询条件说明（search_query_info）：
  offset           偏移量，从 0 开始，**必须是 limit 的整数倍**
  limit            分页条数，**最大 100**
  filters          过滤条件列表，每项 {field_name, field_values[], operator}
  orders           排序 [{fieldName, isAsc}]
  fieldProjection  只返回这些字段（不传则返回全部非空字段）

operator 取值：EQ N GT GTE LT LTE LIKE NLIKE IS ISN IN NIN BETWEEN NBETWEEN
               STARTWITH ENDWITH HASANYOF NHASANYOF

    python 03_query_objects.py                                   # 查前 5 条（默认对象）
    python 03_query_objects.py --object AccountObj --limit 10
    python 03_query_objects.py --object AccountObj --filter name EQ 某某公司
    python 03_query_objects.py --object ProductObj --fields name,price --order create_time desc
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxiaoke_client import FxiaokeClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--object", default="AccountObj", help="对象 apiName")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--filter", nargs=3, action="append", metavar=("FIELD", "OP", "VALUE"),
                    help="过滤条件，可重复：--filter name EQ 某某公司")
    ap.add_argument("--fields", default="", help="只返回这些字段，逗号分隔")
    ap.add_argument("--order", nargs=2, action="append", metavar=("FIELD", "ASC|DESC"))
    ap.add_argument("--raw", action="store_true", help="打印原始响应")
    args = ap.parse_args()

    filters = [{"field_name": f, "operator": op, "field_values": [v]}
               for f, op, v in (args.filter or [])]
    orders = [{"fieldName": f, "isAsc": d.lower() != "desc"}
              for f, d in (args.order or [])] or None
    fields = [x.strip() for x in args.fields.split(",") if x.strip()] or None

    body = {"returnTotalNum": 1,
            "data": {"search_query_info": {
                "offset": args.offset, "limit": min(args.limit, 100), "filters": filters},
                "dataObjectApiName": args.object}}
    if orders:
        body["data"]["search_query_info"]["orders"] = orders
    if fields:
        body["data"]["search_query_info"]["fieldProjection"] = fields

    c = FxiaokeClient()
    print(f"POST /cgi/crm/v2/data/query   object={args.object}")
    print(json.dumps(body, ensure_ascii=False)[:400], "\n")

    d = c.call("/cgi/crm/v2/data/query", body)
    if args.raw:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return

    data = d.get("data") or {}
    rows = data.get("dataList") or data.get("list") or []
    total = data.get("total") or data.get("totalNum")
    print(f"errorCode={d.get('errorCode')}  返回 {len(rows)} 条"
          + (f"  总数 {total}" if total is not None else ""))
    for i, r in enumerate(rows, 1):
        if isinstance(r, dict):
            keys = [k for k in ("_id", "name", "create_time") if k in r] or list(r)[:4]
            brief = {k: r[k] for k in keys}
        else:
            brief = r
        print(f"  {i}. {json.dumps(brief, ensure_ascii=False)}")
    print("\n提示：offset 必须是 limit 的整数倍；深翻页见 references/04_faq/深翻页文档.md")


if __name__ == "__main__":
    main()
