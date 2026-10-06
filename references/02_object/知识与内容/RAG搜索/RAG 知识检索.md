---
title: "RAG 知识检索"
path: "/object/KnowledgeAndContent/rag/search"
url: "https://developer.fxiaoke.com/openapi_v2/object/KnowledgeAndContent/rag/search.html"
block: "对象接口"
module: "知识与内容"
object: "RAG搜索"
category: "知识与内容 / RAG搜索"
updatedAt: "2026-09-14"
fetchedAt: "2026-10-06 09:54:53"
---

# RAG 知识检索

## 描述

基于语义对知识库进行 RAG 检索，返回命中的知识条目或问答对分段内容，适用于智能问答、客服辅助等 AI 场景。

## 请求说明

**请求方式** ：POST + application/json

**请求路径** ：https://[${填入所在云的域名}](https://developer.fxiaoke.com/openapi_v2/start/guide/cloud.html)/cgi/crm/v2/knowledge/rag/search?thirdTraceId=[${随机字符串}](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

**请求头填写** ：参考[公共参数填写](https://developer.fxiaoke.com/openapi_v2/start/example/public.html)

## 请求参数

| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| data | Map | 是 | 数据 |
| content | String | 是 | 检索文本 |
| scenes | List[String] | 否 | 检索场景标识列表，取值需为企业知识库中已配置的场景标识；传入 `all`（不区分大小写）表示全场景 |
| folders | List[String] | 否 | 知识文件夹 code 列表，限定检索范围 |

## 请求示例

```json
{
  "data": {
    "content": "设备怎么安装",
    "scenes": ["wechat"],
    "folders": ["16", "17"]
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
| knowledgeList | Array | 命中列表，可为空数组；无可检索范围等降级场景下可能不返回该字段 |
| knowledgeList[].id | String | 知识条目或问答对 ID |
| knowledgeList[].objectApiName | String | 命中对象类型：`ServiceKnowledgeObj` 知识条目、`QuestionAnswerPairObj` 问答对 |
| knowledgeList[].title | String | 标题 |
| knowledgeList[].content | String | 命中内容分段；问答对命中时首条为答案文本 |
| knowledgeList[].url | String | 命中内容的站内链接，可能为空 |
| knowledgeList[].score | Float | 相关度得分，可能为空，仅供参考 |
| knowledgeList[].chunkId | String | 内容分段 ID，可能为空 |
| knowledgeList[].type | String | 结果类型，当前固定为 `url` |
| knowledgeList[].index | Int | 序号，可能为空 |

## 返回示例

```json
{
  "traceId": "E-O.fktest4234.1000-20260914111000-xxxxxx",
  "errorDescription": "success",
  "errorMessage": "success",
  "errorCode": 0,
  "data": {
    "knowledgeList": [
      {
        "id": "68c1a0f0abcd0001",
        "objectApiName": "ServiceKnowledgeObj",
        "title": "设备安装说明",
        "type": "url",
        "content": "安装步骤",
        "score": 0.92,
        "chunkId": "chunk-001",
        "index": 0
      }
    ]
  }
}
```

## 注意事项

- scenes 与 folders 同时传入时取并集；两者都不传时默认按全场景（相当于 scenes=["all"] ）检索。
- 传入 folders 时服务端会自动展开其子文件夹，并与当前用户的授权可见范围取交集；超出权限范围的内容不会被检索到。
- 传入 folders 展开交集后无有效文件夹时，返回成功且结果为空（ knowledgeList 缺失或为空数组），不会退化为全库检索。
- 企业未初始化知识库或当前用户无任何可见范围时，返回成功且命中列表为空（ knowledgeList 为空数组或缺失），不会报错。
- 命中结果中 url 、 score 、 chunkId 、 index 等字段可能为空或缺失，请按字段缺失兼容。
- 本接口为语义检索计算，响应时间相对较长，建议调用超时时间设置为 60 秒。
- 返回的 url 为站内链接，不保证在外部网络可直接访问。
- 不能使用返回值的message字段做逻辑判断，errorMessage会有变化；
