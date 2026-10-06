---
title: "批量查询网盘文件/文件夹的ID"
path: "/common/system/other/file/queryFileIdsByPaths"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/other/file/queryFileIdsByPaths.html"
block: "通用接口"
module: "系统接口"
object: "其他通用接口"
category: "系统接口 / 其他通用接口 / 文件"
updatedAt: "2026-07-30"
fetchedAt: "2026-10-06 09:54:52"
---

# 批量查询网盘文件/文件夹的ID

## 描述

批量根据网盘路径（nPath）查询文件/文件夹的节点 ID，返回「路径 → 节点ID」映射。

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/v2/queryFileIdsByPaths?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 | 数据MAP |
| paths | List[String] | 是 | 网盘路径列表（nPath），不能为空 |

## 请求示例

```json
{
  "data": {
    "paths": [
      "N_202607_19_cxxx593.xlsx",
      "N_202601_22_xxxx.xlsx"
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
| data | object | 返回数据 |
| pathNodeIdMap | Map[String, String] | 路径 → 节点ID 的映射；未查询到的路径不会出现在 map 中 |

## 返回示例

```json
{
  "traceId": "E-O.fktest4234.1000-20260730175300-xxxxxx",
  "data": {
    "pathNodeIdMap": {
      "N_202601_22_b22f64c8cf004a78ae8809dded4f5fe1.xlsx": "5777625dd85c4bce97043df105c6c315",
      "N_202607_19_ca3b63b4e1964a3ab69f5da8b1c67593.xlsx": "2d885fe1cf4e4454af940dc39e3bcbed"
    }
  },
  "errorDescription": "success",
  "errorMessage": "success",
  "errorCode": 0
}
```

## 注意事项

- 查询不到的路径不会出现在 pathNodeIdMap 中，调用方需自行比对传入 paths 与返回 key 的差异。
- 不能使用返回值的message字段做逻辑判断，errorMessage会有变化；
