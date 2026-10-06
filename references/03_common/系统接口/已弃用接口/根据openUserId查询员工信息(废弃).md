---
title: "根据openUserId查询员工信息(废弃)"
path: "/common/system/offline/info"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/offline/info.html"
block: "通用接口"
module: "系统接口"
object: "已弃用接口"
category: "系统接口 / 已弃用接口"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# 根据openUserId查询员工信息(废弃)

## 不建议继续使用下线接口

## 描述

根据openUserId查询员工信息

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/user/get?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| corpAccessToken | String | 是 | 企业应用访问公司合法性凭证 |
| corpId | String | 是 | 开放平台公司帐号 |
| openUserId | String | 是 | 开放平台员工帐号 |
| showDepartmentIdsDetail | Boolean | 否 | 如果为true，则会返回员工主属部门(mainDepartmentId)与附属部门(attachingDepartmentIds); 默认值为false |

## 请求示例

```json
{
  "corpAccessToken": "{corpAccessToken}",
  "corpId": "{corpId}",
  "openUserId": "{openUserId}",
  "showDepartmentIdsDetail": false
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
