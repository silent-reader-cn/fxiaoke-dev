---
title: "审批流当前任务驳回到前面的某个节点"
path: "/common/process/approval/reject"
url: "https://developer.fxiaoke.com/openapi_v2/common/process/approval/reject.html"
block: "通用接口"
module: "流程与规则"
object: "审批流程"
category: "流程与规则 / 审批流程"
updatedAt: "2026-01-16"
fetchedAt: "2026-10-06 09:54:52"
---

# 审批流当前任务驳回到前面的某个节点

## 描述

审批流当前任务驳回到前面的某个节点

## 请求说明

**请求方式**：POST + application/json

**请求路径**：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/v2/special/approval/rejectToBeforeTask?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 |  |
| currentTaskId | String | 是 | 当前任务id |
| rejectToTaskId | String | 是 | 驳回到某个任务的id |
| rejectOpinion | String | 是 | 驳回意见 |
| moveToCurrentActivityWhenReject | String | 否 | 该审批再申请时是否跳到当前节点 |

## 请求示例

```json
{
  "data": {
    "rejectOpinion": "驳回意见",
    "currentTaskId": "6183b1b622794e6865bca8ce",
    "rejectToTaskId": "6183b1b0b89d061cf7fbac1f",
    "moveToCurrentActivityWhenReject": true
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
