---
title: "刷新 accessToken"
path: "/start/auth/refresh"
url: "https://developer.fxiaoke.com/openapi_v2/start/auth/refresh.html"
block: "快速开始与接入"
module: "OAuth授权认证"
object: "刷新 accessToken"
category: "OAuth授权认证"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:53"
---

# 刷新 accessToken

access_token 是调用授权关系接口的调用凭证，由于 access_token 有效期较短，当 accessToken 超时后，可以使用 refreshToken 进行刷新。

refresh_token 拥有较长的有效期（2 个月），当 refresh_token 失效后，需要用户重新授权。

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/oauth2.0/token?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 参数类型 | 必须 | 说明 |
| --- | --- | --- | --- |
| grantType | String | 是 | 授权模式，固定值为：refresh_token |
| appId | String | 是 | 自建应用的 appId |
| appSecret | String | 是 | 自建应用的 appSecret |
| refreshToken | String | 是 | 获取 token 接口返回的 refreshToken |

## 请求示例

```json
{
    "grantType": "refresh_token",
    "appId": "FSAID_xxxxx",
    "appSecret": "982axxxxx",
    "refreshToken": "xxxxxx"
}
```

## 返回参数

| 参数 | 必须 | 说明 |
| --- | --- | --- |
| accessToken | 是 | 授权凭证 token，有效期两个小时 |
| refreshToken | 是 | 用于刷新 accessToken，有效期两个月 |
| expiresIn | 是 | 过期时间 |

## 返回示例

```json
{
    "accessToken": "FSTOK_xxxxx",
    "refreshToken": "FSREFTOK_xxxxx",
    "expiresIn": 7200,
    "errorCode": 0,
    "errorMessage": "success",
    "traceId": "E-O.fkxxxxxx8bd6"
}
```
