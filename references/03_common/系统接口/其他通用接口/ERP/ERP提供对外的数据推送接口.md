---
title: "ERP提供对外的数据推送接口"
path: "/common/system/other/ERP/push"
url: "https://developer.fxiaoke.com/openapi_v2/common/system/other/ERP/push.html"
block: "通用接口"
module: "系统接口"
object: "其他通用接口"
category: "系统接口 / 其他通用接口 / ERP"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# ERP提供对外的数据推送接口

## 描述

ERP提供对外的数据推送接口

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/erp/syncdata/objdata/push?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 | 数据集 |
| objAPIName | String | 否 | erp的对象apiName |
| dataCenterId | String | 否 | 数据中心id（可以在crm管理后台-连接器-连接对象-生成api的推送接口，找到dataCenterId） |
| id | String | 否 | id传值的时候，表示数据体是完全按照标准的erp集成平台定义的数据格式。id不传值表示非标准的格式，需要在推送接口设置函数 |
| masterFieldVal | Map | 否 | 主对象数据 |
| detailFieldVals | Map | 否 | 从对象数据列表 |
| directSync | Boolean | 否 | 是否实时同步 |
| destObjectApiName | String | 否 | 目标对象apiName：如果是实时同步必须要填目标对象 |

## 请求示例

```json
{
  "data": {
    "detailFieldVals": {
      "erpSalesOrderProductObj": [
        {
          "number": "04270002-0001",
          "product_id": "000",
          "product_price": "100",
          "sales_price": "100"
        }
      ]
    },
    "directSync": false,
    "destObjectApiName": "erpSalesOrderProductObj",
    "objAPIName": "erpSalesOrderObj",
    "dataCenterId": "63f82854a8bd974420925e83",
    "masterFieldVal": {
      "number": "04270002",
      "order_account_id": "042700001",
      "order_origin_price": "100",
      "sales_order_discount_price": "100",
      "receiver_phone": "1900901091021"
    },
    "id": "111"
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
