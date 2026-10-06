---
title: "BI拼表接口"
path: "/common/system/other/BI/query"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/other/BI/query.html"
block: "通用接口"
module: "系统接口"
object: "其他通用接口"
category: "系统接口 / 其他通用接口 / BI"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# BI拼表接口

## 描述

BI拼表接口

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/v2/bi/lwt/query?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 | 数据集 |
| id | String | 是 | 报表ID |
| filterList | List | 否 |  |
| showMode | String | 否 | 展示模式 |
| pageNumber | Int | 否 | 页码默认为 1 |
| pageSize | Int | 否 | 分页大小默认 20 |

## 请求示例

```json
{
  "data": {
    "pageNumber": 1,
    "pageSize": 20,
    "showMode": "1",
    "id": "BI_lwt_1645436530233",
    "filterList": [
      {
        "filters": []
      }
    ]
  }
}
```

## 返回参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| traceId | string | 请求唯一ID |
| errorDescription | string | 错误描述 |
| errorMessage | string | 错误信息 |
| errorCode | Int | [查看错误码](https://developer.fxiaoke.com/openapi_v2/start/guide/codes.html) |

## 返回示例

```json
{
  "traceId": "E-O.827xxxxxx",
  "errorDescription": "success",
  "errorMessage": "OK",
  "errorCode": 0
}
```

## 注意事项

- 不能使用返回值的message字段做逻辑判断，errorMessage会有变化；
