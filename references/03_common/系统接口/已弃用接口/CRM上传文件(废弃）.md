---
title: "CRM上传文件(废弃）"
path: "/common/system/offline/crm"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/offline/crm.html"
block: "通用接口"
module: "系统接口"
object: "已弃用接口"
category: "系统接口 / 已弃用接口"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# CRM上传文件(废弃）

## 描述

CRM上传文件(废弃）,请使用[上传文件接口](https://developer.fxiaoke.com/openapi_v2/common/system/other/file/upload.html))

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/media/upload?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

调用示例（使用curl命令，用FORM表单方式上传一个多媒体文件）： curl -F "media=@test.jpg" http://open.fxiaoke.com/media/upload?corpAccessToken=xxx&corpId=xxx&type=image

上传的文件限制:

image类型，最大20M，支持jpg, png, gif, bmp, jpeg格式

document类型，最大100M

请注意，mediaId是可复用的，同一个mediaId可用于CRM对象的图片、文件类型字段。

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| type | String | 是 | 素材文件类型，目前支持image（CRM素材）, document（文档类型，支持审批素材, CRM素材） |
| igonreMediaIdConvert | Boolean | 是 | mediaId类型，当为true时返回值中的mediaId值为npath；当为false时返回值中的mediaId为mediaId;上传和下载应设置为同一值（推荐传值true） |
| media |  | 是 | 二进制流，包含form-data中媒体文件标识，有filename、filelength、content-type等信息 |
| corpAccessToken | String | 是 | 企业应用访问公司合法性凭证 |
| corpId | String | 是 | 开放平台公司帐号 |

## 请求示例

```json
{
  "media": "hello",
  "type": 1,
  "igonreMediaIdConvert": 1
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
