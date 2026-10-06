---
title: "获取 JsapiTicket"
path: "/common/client/guide/ticket"
url: "https://developer.fxiaoke.com/openapi_v2/common/client/guide/ticket.html"
block: "通用接口"
module: "客户端开发"
object: "接入指南"
category: "客户端开发 / 接入指南"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# 获取 JsapiTicket

## 描述

JsapiTicket是纷享应用调用纷享JS API的临时票据，在签名计算中使用。正常情况下，JsapiTicket的有效期为7200秒（2小时）。

## 请求说明

**请求方式** ：POST + application/json

**请求路径** ：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/jsApiTicket/get?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| corpAccessToken | String | 是 | 企业应用访问公司合法性凭证 |
| corpId | String | 是 | 开放平台公司账号 |

## 请求示例

```json
{
    "corpAccessToken": "APP_ACCESS_TOKEN",
    "corpId":"CORP_ID"
}
```

## 返回参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| errorMessage | string | 错误信息 |
| errorCode | Int | [查看错误码](https://developer.fxiaoke.com/openapi_v2/start/guide/codes.html) |
| ticket | string | 临时票据 |
| expiresIn | string | ticket有效时间,以秒为单位 |

## 返回示例

```json
{
    "errorCode": 0,
    "errorMessage": "success",
    "ticket":"",
    "expiresIn":7200
}
```

## 注意事项

- 不能使用返回值的message字段做逻辑判断，errorMessage会有变化；
