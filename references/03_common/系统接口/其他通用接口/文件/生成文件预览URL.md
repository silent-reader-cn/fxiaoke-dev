---
title: "生成文件预览URL"
path: "/common/system/other/file/view"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/other/file/view.html"
block: "通用接口"
module: "系统接口"
object: "其他通用接口"
category: "系统接口 / 其他通用接口 / 文件"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# 生成文件预览URL

## 描述

生成文件预览URL

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/v2/generatorPreviewUrl?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 | 数据MAP |
| expireTime | Int | 是 | 链接有效期，单位秒。最小值60秒最大值：604800秒 |
| globalAcceleration | Boolean | 否 | 是否开启全球加速，默认false |
| fileInfo | Map | 是 | 文件基本信息 |
| path | String | 是 | 文件ID，必须以N_、TN_、C_、TC_开头，长度不超过48 |
| filename | String | 是 | 文件名，最长120字符 |
| extension | String | 是 | 文件扩展名，不带点号。支持预览类型：png,webp,jpeg,jpg,bmp,gif,txt,sql,js,css,csv,json,md,xml,py,java |

```
                             |
```

## 请求示例

```json
{
  "data": {
    "expireTime": "",
    "globalAcceleration": "",
    "fileInfo": {
      "path": "",
      "extension": "",
      "filename": ""
    }
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
