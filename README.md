# fxiaoke-dev

**纷享销客（ShareCRM）开放平台 OpenAPI v2 开发知识库与 AI Skill** —— 对象接口 + 通用接口 + 接入认证，1,307 篇官方文档用一套全文检索脚本统一检索。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Pages](https://img.shields.io/badge/docs-1%2C307-orange.svg)
![Objects](https://img.shields.io/badge/objects-211-blue.svg)
![Modules](https://img.shields.io/badge/modules-41-green.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)

> 语料来自纷享销客开发者手册 `developer.fxiaoke.com/openapi_v2`，抓取于 **2026-10-06**。
> 文档自身的最后更新时间集中在 **2026-01-16**（1,277 篇），少量页面更新至 2026-09-14。

---

## 这是什么

对接纷享销客 CRM 时最常查的三类资料，全部收在一处，**并且都能用同一个命令搜出来**：

| 块 | 内容 | 规模 | 入口 |
| :--- | :--- | :--- | :--- |
| **块一 对象接口** | 41 个业务模块、211 个对象的增删改查与专用动作 | 1,142 篇 | [`references/02_object/`](./references/02_object/) |
| **块二 通用接口** | 流程与规则 / 系统接口 / 通讯录 / 客户端开发 | 146 篇 | [`references/03_common/`](./references/03_common/) |
| **块三 快速开始与接入** | OAuth 认证、免登、公共参数、所在云域名、频次、错误码 | 15 篇 | [`references/01_start/`](./references/01_start/) |
| （附）常见问题 | 查不到数据、数据权限、深翻页、查询条件 | 4 篇 | [`references/04_faq/`](./references/04_faq/) |

覆盖的业务域：商品与产品、库存与仓储、采购、销售与订单、商机与线索、报价与价格、
工单与服务、外勤、会员、促销、返利、合同、供应商、物流与发货、开票与结算、
财务与回款、盘点与调拨、设备与资产、项目、知识、微信生态、互联企业…

---

## 30 秒上手

```bash
git clone https://github.com/silent-reader-cn/fxiaoke-dev.git
cd fxiaoke-dev

# 不知道某个接口怎么调？直接搜，返回请求方式/路径/参数/返回结构
python scripts/search.py 创建产品对象

# 只知道参数名或请求头？搜正文
python scripts/search.py x-fs-userid --brief

# 按业务域浏览
python scripts/search.py --list --category 审批流程

# 精确取一篇（默认输出完整正文）
python scripts/search.py --path /object/CommoditiesAndProducts/ProductObj/add
```

只依赖 Python 3（标准库），无需安装任何第三方包。

---

## 接入速览

纷享销客 OpenAPI v2 采用 **OAuth 2.0 + 三个请求头**：

```bash
# 1) 取 accessToken（客户端凭证模式，有效期 7200 秒，建议缓存 6600 秒）
curl -X POST 'https://open.fxiaoke.com/oauth2.0/token?thirdTraceId=<UUID v4>' \
  -H 'Content-Type: application/json' \
  -d '{"appId":"FSAID_xxx","appSecret":"xxx","permanentCode":"xxx","grantType":"app_secret"}'

# 2) 调业务接口
curl -X POST 'https://open.fxiaoke.com/cgi/crm/v2/data/create?thirdTraceId=<新的 UUID v4>' \
  -H 'authorization: Bearer <accessToken>' \
  -H 'x-fs-ea: <企业 ea>' \
  -H 'x-fs-userid: <员工ID>' \
  -H 'Content-Type: application/json' \
  -d '{"data":{"object_data":{"dataObjectApiName":"ProductObj","name":"hello"}}}'
```

- `authorization` 前缀 `Bearer ` **后面有一个空格**，漏了会 401。
- 每个请求的 `thirdTraceId` 必须**每次不同**，按 RFC 4122 UUID v4 生成。
- 所在云域名：纷享云 `open.fxiaoke.com`、华为云 `open-hwcloud.fxiaoke.com`、
  阿里云 `open-ale.fxiaoke.com`、香港华为 `open-ksc.sharecrm.com`、法兰克福 `open-hws.fxiaoke.com`。

完整接入说明见 [`SKILL.md`](./SKILL.md#二接入必读第一步) 与
[`references/01_start/`](./references/01_start/)。

---

## 可运行示例

[`examples/`](./examples/) 下有一套**只依赖标准库**的最小可用代码（Python + Node），
已用真实租户跑通。写操作**默认 dry-run**，加 `--yes` 才真正提交。

```bash
export FX_APP_ID=... FX_APP_SECRET=... FX_PERMANENT_CODE=... FX_USER_ID=1000
PY="<你的 python3 路径>"

"$PY" examples/01_get_token.py                       # 取 accessToken
"$PY" examples/02_object_list.py --grep 客户           # 对象清单（apiName → 中文名）
"$PY" examples/03_query_objects.py --object AccountObj --limit 5
"$PY" examples/04_object_describe.py --object AccountObj --grep 电话
"$PY" examples/05_create_object.py --object AccountObj --field name=示例客户  # 不发送
```

| 脚本 | 作用 |
| :--- | :--- |
| `fxiaoke_client.py` / `.js` | 客户端封装：token 缓存（6600s）、自动 `thirdTraceId`、三个请求头 |
| `01_get_token.py` | 客户端凭证模式取 accessToken |
| `02_object_list.py` | 查对象列表 |
| `03_query_objects.py` | 按条件查询 |
| `04_object_describe.py` | 查字段清单 |
| `05_create_object.py` | 创建对象（dry-run） |
| `06_approval_action.py` | 审批流动作（dry-run） |
| `07_invalid_and_delete.py` | 作废 → 删除（dry-run） |

**实测踩坑**（文档没写或与文档不符，都是拿真实租户跑出来的）：

- `x-fs-userid` 必须是**应用可见范围内**的数字员工ID。传 `openUserId` 报 `10006`，
  不在范围内报 `20021 userScopeNotSupport`，留空报 `20017`。
- **全局返回码表与实际返回对不上**（10006 / 20017 / 20021 都对不上），
  只认 `errorCode`，具体原因看 `errorMessage`。
- token 响应除 `accessToken` 外还返回 `access_token` / `expires_in` / `token_type`。
- `object/list` 用 camelCase，`object/describe` 用 snake_case。
- `create` 返回的记录 id 在**响应顶层 `dataId`**。
- `data/invalid` **只作废单个 id**；未作废的记录 `data/delete` 会**静默跳过**（返回 0 却没删）。
- **手册的对象清单 ≠ 你租户的对象清单**（实测某租户 176 个 vs 手册 211 个，仅重合 52 个；
  19 个对象中文名不一致，如 `ProductObj` 手册标「商品」、租户实际是「产品」）。

完整清单见 [`examples/README.md`](./examples/README.md#实测踩坑文档没写或与文档不符)。

---

## 检索用法

```bash
PY="<你的 python3 路径>"

# 按标题找接口
"$PY" scripts/search.py 创建产品对象
"$PY" scripts/search.py 审批流流程完成 --full          # 完整正文，不截断
"$PY" scripts/search.py 库存 查询 --all --scope object --brief

# 按对象 apiName 找（path 参与检索，apiName 直接可用）
"$PY" scripts/search.py ProductObj --brief             # 商品对象全部 8 个接口
"$PY" scripts/search.py WorkOrdersAndServices --brief  # 整个模块 90 篇

# 按正文找（参数名、请求头、错误码…）
"$PY" scripts/search.py thirdTraceId --limit 5
"$PY" scripts/search.py 深翻页 --scope faq

# 浏览与精确取用
"$PY" scripts/search.py --list --scope start
"$PY" scripts/search.py --path /common/process/approval/action
```

| 选项 | 说明 |
| :--- | :--- |
| `--scope S` | `start` / `object` / `common` / `faq`，逗号可组合，默认 `all` |
| `--category C` | 分类子串，如 `库存与仓储`、`审批流程` |
| `--brief` | 每条只输出一行 |
| `--full` / `-d` | 输出完整正文，不截断 |
| `--all` | 多个关键词必须全部命中 |
| `--limit N` / `--max N` | 返回条数（默认 20）/ 每条正文上限（默认 1500 字符） |
| `--list` | 只列条目，不输出正文 |
| `--path P` | 按 `path` 或标题精确取一篇（默认输出完整正文） |

> 检索**直接读 Markdown**，不依赖预生成字典，所以不存在「改了文档忘了重建索引就搜不到」的漂移问题。
> 实测检索全部 1,307 篇约 **0.8 秒**。

---

## 目录结构

```
fxiaoke-dev/
├── SKILL.md                       # AI Skill 定义：接入 + 导航 + 检索 + 示例
├── examples/                      # 可运行示例（Python + Node，零依赖）
│   ├── README.md                  #   用法 + 实测踩坑清单
│   ├── fxiaoke_client.py / .js
│   ├── 01_get_token.py … 07_invalid_and_delete.py
│   └── credentials.example.json   #   凭据模板（真实凭据不入库）
├── references/
│   ├── _INDEX.md                  # 1,307 篇总索引
│   ├── 01_start/<分类>/<标题>.md            # 15 篇
│   ├── 02_object/<模块>/<对象>/<标题>.md    # 1,142 篇
│   ├── 03_common/<分类>/<标题>.md           # 146 篇
│   └── 04_faq/<标题>.md                     # 4 篇
├── scripts/
│   ├── search.py                  # 统一检索
│   └── build_index.py             # 从 Markdown 生成各级 _INDEX.md
├── tools/
│   ├── extract_routes.py          # 从站点 app.js 提取全站路由 + 中文层级
│   ├── fetch_manual.py            # 批量抓取 + 转换 + 增量更新
│   ├── html2md.py                 # 零依赖 HTML → Markdown 转换器
│   └── selftest.py                # 完整性自检
└── _source/
    ├── _toc.json                  # 路由清单 + 中文层级映射
    ├── _files.json                # 页面 → 落盘文件清单
    └── _sidebar.json              # 站点 sidebar 配置
```

---

## 语料怎么更新

```bash
# 1) 重新提取路由（站点改版后；会自动下载最新的 app-*.js）
python tools/extract_routes.py

# 2) 增量抓取（已抓过的跳过，只补新页面）
python tools/fetch_manual.py

# 3) 强制重抓全量（改过转换规则后用）
python tools/fetch_manual.py --force --jobs 8

# 4) 重建索引
python scripts/build_index.py

# 5) 自检（--online N 抽样联网核对文本保真与结构守恒）
python tools/selftest.py --online 60

# 6) 查看已下线页面（只列出，不删除）
python tools/fetch_manual.py --prune
```

抓取整站约 **790MB 下行流量 / 35 秒**（8 线程），但页面 600KB 里 97% 是内联侧边栏，
只留正文后落盘仅 **4.2MB**。`references/` 是唯一真相源，索引与检索都从它派生。

---

## 自检结果

`python tools/selftest.py --online 60` 全部通过：

| 检查 | 结果 |
| :--- | :--- |
| A1 路由清单 / 抓取清单 / 磁盘 Markdown 三方条目数一致 | 1307 = 1307 = 1307 |
| A2 文本保真（抽样联网，源页每段可见文本都能在 Markdown 找到） | 60/60 |
| A3 结构守恒（抽样联网，`<table>`/`<pre>` 与 Markdown 表格/围栏数量一致） | 0 处不一致 |
| A4 无残留未转换的 HTML 块级标签（代码块内的 HTML 属正文内容，已排除） | 0 篇 |
| A5 frontmatter 字段齐全 | 0 篇缺失 |
| B1 `--path` 输出完整正文 | 1449/1449 行 |
| B2 截断时打印明确提示（不静默丢内容） | 通过 |
| B3 `--limit` 生效且总命中数口径一致 | 通过 |
| B4 索引内链接全部可达、叶子目录条目数一致 | 0 死链 / 0 不一致 |
| B5 正文深处关键词可召回（全库唯一探针） | 8/8 |

---

## 已知数据特征（上游如此，非管道问题）

- 有 **6 个对象**（`PreventiveMaintenanceObj`、`SOPInstanceObj`、`ServiceFaultRecordObj`、
  `ServiceLogObj`、`ServiceReportObj`、`PreventiveMaintenanceDetailObj`）**未登记在站点 sidebar**，
  页面面包屑只有「模块 / 标题」两级。这些对象的目录用**英文对象名**兜底 ——
  它们的正文是**逐字节相同的模板占位**（标题也是未定制的「创建工单对象」，
  请求示例里的 `dataObjectApiName` 甚至填的是 `CasesObj`），**上游文档本身就没给出中文名**，
  所以不做猜测。用 `search.py PreventiveMaintenanceObj` 可直接定位这 8 个接口。
- 有 **3 处页面标题在同一目录内重复**（如审批流的 `before` 与 `reject` 都叫
  「审批流当前任务驳回到前面的某个节点」），落盘时补 `-<action>` 后缀区分。
- 对象页正文高度模板化：`描述 / 请求说明 / 请求参数 / 请求示例 / 返回参数 / 返回示例 / 注意事项`，
  且「注意事项」多为跨页共用的样板句。按正文搜索时注意排序会受此影响。

---

## 免责声明

内容整理自纷享销客官方公开文档，仅供学习、对接与二次开发参考。
接口名称、参数、返回结构及字段说明等版权归纷享销客所有。
示例中的真实凭据均已脱敏，使用前请替换为你自己的值。请遵守纷享销客相关许可与数据合规要求。

## License

[MIT](./LICENSE)
