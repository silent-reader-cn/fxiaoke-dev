---
title: "获取文件预签名URL"
path: "/common/system/other/file/get"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/other/file/get.html"
block: "通用接口"
module: "系统接口"
object: "其他通用接口"
category: "系统接口 / 其他通用接口 / 文件"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# 获取文件预签名URL

## 描述

获取文件预签名URL

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/v2/file/getPresignedUrl?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**限制条件：企业需为阿里云或华为云的文件专属企业**

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 | 数据MAP |
| paths | List[String] | 是 | 文件路径 |
| expire | Int | 是 | 过期时间 |

## 请求示例

```json
{
  "includeNull": true,
  "data": {
    "paths": [
      "603dabc14ae65400011aec90"
    ],
    "expire": 1
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
