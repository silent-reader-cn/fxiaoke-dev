---
name: fxiaoke-dev
summary: 纷享销客（ShareCRM / Fxiaoke）开放平台 OpenAPI v2 开发知识库 —— 对象接口 + 通用接口 + 接入认证，内置统一全文检索。
description: >-
  纷享销客开放平台（developer.fxiaoke.com/openapi_v2）OpenAPI v2 开发指南，覆盖三大块内容：
  (1) 对象接口 —— 41 个业务模块、211 个对象的增删改查与专用动作（商品与产品、库存与仓储、
  财务与回款、商机与线索、客户与联系人、工单与服务、采购管理、物流发运、会员管理、促销、
  返利、合同、供应商、备件、项目、互联企业…）；
  (2) 通用接口 —— 审批流程与业务流程（审批流完成/驳回/终止、阶段推进器）、系统接口
  （对象描述、自定义函数、币种、加解锁、相关团队、文件、消息、考勤、ERP、BI、已弃用接口）、
  通讯录（人员/角色/用户组）、客户端开发（JavaScript 与 UI 组件）；
  (3) 快速开始与接入 —— OAuth 2.0 认证（客户端凭证模式 / 授权码模式）、免登、
  公共参数与请求头、所在云域名、频次限制、全局返回码。
  当需要调用纷享销客 OpenAPI（/cgi/crm/v2/data/...、/cgi/crm/approvalTask/...、/oauth2.0/token）、
  对接纷享 CRM、构造 accessToken 与请求头（authorization / x-fs-ea / x-fs-userid）、
  查询某个对象的接口参数与字段说明、发起审批流操作、同步通讯录、
  或排错（错误码、token 过期、深翻页、频次限制）时使用。
  接口参数与返回结构均可用内置统一检索脚本按关键词定位，无需逐个打开文档。
---

# 纷享销客 OpenAPI v2 开发指南

本 skill 是**纷享销客开放平台开发者手册**（`developer.fxiaoke.com/openapi_v2`）的完整离线版：
全站 1,307 篇中文文档已批量抓取并转换为 Markdown，配一套统一全文检索脚本。

> 语料来源：官方开发者手册（VuePress SSG 站点），抓取于 **2026-10-06**。
> 文档自身的最后更新时间集中在 **2026-01-16**（1,277 篇），少量页面更新至 2026-09-14。
> 上游若改版，重跑 `tools/fetch_manual.py` 即可增量更新。

---

## 一、何时用本 skill

| 场景 | 去哪一块 |
| :--- | :--- |
| 取 accessToken、搞清认证流程与请求头 | 块三 快速开始与接入（第二节） |
| 调某对象的增删改查（商品/库存/商机/工单…） | 块一 对象接口 |
| 审批流完成/驳回/终止、阶段推进 | 块二 通用接口 · 流程与规则 |
| 对象描述、文件上传下载、消息、考勤、ERP 对接 | 块二 通用接口 · 系统接口 |
| 同步人员/角色/用户组 | 块二 通用接口 · 通讯录接口 |
| 错误码、token 过期、深翻页、频次限制排错 | 块三 + 第四节排错 |

---

## 二、接入（必读，第一步）

纷享销客 OpenAPI v2 采用 **OAuth 2.0 + 三个请求头**：

```
取 accessToken  →  拼三个请求头  →  调业务接口（URL 带 thirdTraceId）
```

### 2.1 第 1 步：取 accessToken

**客户端凭证模式**（服务端对服务端，无用户参与，可用任意员工 id 访问）：

- **请求**：`POST https://<所在云域名>/oauth2.0/token?thirdTraceId=<随机UUID>`
- **Body（application/json）**：

| 参数 | 必选 | 说明 |
| :--- | :--- | :--- |
| `appId` | 是 | 自建应用的 appId（`FSAID_xxx`） |
| `appSecret` | 是 | 自建应用的 appSecret |
| `permanentCode` | 是 | 永久授权码 |
| `grantType` | 是 | 固定 `app_secret` |

- **返回**：`accessToken`（有效期 **7200 秒**）、`expiresIn`、`openUserId`、`ea`、`appId`

> ⚠️ **token 缓存红线**：0–6600 秒内调用返回**同一个** token；6600–7200 秒之间调用返回新 token，
> 新旧都可用；7200 秒后旧 token 失效。建议**缓存 6600 秒**再刷新。
> 本接口**每分钟不超过 10 次、不可并发调用**，建议按错误码 `20016` 加重试。

另有**授权码模式**（需用户参与，换取用户级 token），见
[`references/01_start/OAuth授权认证/授权码模式.md`](./references/01_start/OAuth授权认证/授权码模式.md)。

### 2.2 第 2 步：拼请求头（每个业务接口都要）

| Header | 必填 | 说明 |
| :--- | :--- | :--- |
| `authorization` | 是 | 固定前缀 `Bearer ` **（注意有一个空格）** + accessToken |
| `x-fs-ea` | 是 | 企业账号 `ea`，从取 token 的返回结果中获取 |
| `x-fs-userid` | 是 | 员工 ID（CRM 后台「人员 → 系统名 → 账号信息 → 员工ID」） |

> 新版传参下**不需要**把员工 ID 转成 FSUID；确实要转就在 body 最外层加
> `{"convertUserId": true}`。文件参数同理用 `convertMediaId`。

### 2.3 第 3 步：调业务接口

- **URL**：`https://<所在云域名>/cgi/crm/v2/data/<action>?thirdTraceId=<随机UUID>`
- **`thirdTraceId`**：每次请求都要带、且**每次都不同**的随机字符串，按 **RFC 4122 UUID v4** 生成。
- **平台公共参数**（body 最外层）：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `convertUserId` | boolean | 是否转换用户 ID，新版参默认 `false` |
| `convertMediaId` | boolean | 是否转换媒体 ID，新版参默认 `false` |

### 2.4 所在云域名

| 云 | 域名 |
| :--- | :--- |
| 纷享云 | `open.fxiaoke.com` |
| 华为云 | `open-hwcloud.fxiaoke.com` |
| 阿里云 | `open-ale.fxiaoke.com` |
| 香港华为 | `open-ksc.sharecrm.com` |
| 法兰克福 | `open-hws.fxiaoke.com` |

其他云：`open-${当前云登录域名}`。详见
[`references/01_start/基础说明/所在云域名.md`](./references/01_start/基础说明/所在云域名.md)。

### 2.5 最小调用示例

```bash
# 1) 取 token
curl -X POST 'https://open.fxiaoke.com/oauth2.0/token?thirdTraceId=5ea0422d-98e3-49e0-a3cb-9bd5517d1f30' \
  -H 'Content-Type: application/json' \
  -d '{"appId":"FSAID_xxx","appSecret":"xxx","permanentCode":"xxx","grantType":"app_secret"}'
# → {"accessToken":"BC...","expiresIn":7084,"ea":"fxxx1","openUserId":"FSCID_xxx",...}

# 2) 调业务接口
curl -X POST 'https://open.fxiaoke.com/cgi/crm/v2/data/create?thirdTraceId=<新UUID>' \
  -H 'authorization: Bearer BC...' \
  -H 'x-fs-ea: fxxx1' \
  -H 'x-fs-userid: 12345' \
  -H 'Content-Type: application/json' \
  -d '{"data":{"object_data":{"dataObjectApiName":"ProductObj","name":"hello"}}}'
```

---

## 三、三大块导航

| 块 | 内容 | 规模 | 入口 |
| :--- | :--- | :--- | :--- |
| **块一 对象接口** | 41 个业务模块、211 个对象的增删改查与专用动作 | 1,142 篇 | [`references/02_object/`](./references/02_object/) |
| **块二 通用接口** | 流程与规则 / 系统接口 / 通讯录 / 客户端开发 | 146 篇 | [`references/03_common/`](./references/03_common/) |
| **块三 快速开始与接入** | OAuth 认证、免登、公共参数、频次、错误码 | 15 篇 | [`references/01_start/`](./references/01_start/) |
| （附）常见问题 | 查不到数据、数据权限、深翻页、查询条件 | 4 篇 | [`references/04_faq/`](./references/04_faq/) |

**块一 对象接口** 的 41 个模块（按业务域）：

商品与产品 · 产品约束与属性 · 库存与仓储 · 库存批次与序列号 · 盘点与调拨 · 领料与退料 ·
个人库管理 · 财务与回款 · 开票与结算 · 返利管理 · 客户与联系人 · 商机与线索 · 销售与订单 ·
报价与价格 · 工单与服务 · 备件管理 · 外勤管理 · 服务技能 · 采购管理 · 供应商管理 ·
物流与发货 · 退款管理 · 合同管理 · 会员管理 · 促销管理 · 优惠券管理 · 营销与活动 ·
微信生态 · 互联企业 · 企业库 · 项目管理 · 目标规则 · 阶段推进器 · 审批与业务流程 ·
组织与人员 · 设备与资产 · 知识与内容 · 行为与访客 · 通信与记录 · 日程与日志 · 自定义能力

**块二 通用接口** 的 4 个大类：

- **流程与规则** —— 审批流程（完成/驳回/终止/查询定义）、业务流程、阶段推进器
- **系统接口** —— 对象描述、自定义函数、加解锁、相关团队、币种、产品分类、
  其他通用接口（审批/BI/互联/ERP/文件/物料/消息/任务/考勤）、已弃用接口
- **通讯录接口** —— 人员、人员角色、用户组
- **客户端开发** —— JavaScript API、UI 组件、开发指南、工单

各块都有 `_INDEX.md` 总索引（由 `scripts/build_index.py` 从 Markdown 自动生成）。

---

## 四、统一检索（核心用法）

**三大块全部内容用同一个脚本检索**，直接返回命中条目的正文，无需再打开 `.md` 文件。

```bash
PY="<你的 python3 路径>"
"$PY" "$SKILL_DIR/scripts/search.py" <关键词...> [选项]
```

`$SKILL_DIR` 指本 skill 根目录。常用示例：

```bash
# 按标题找接口
"$PY" scripts/search.py 创建产品对象                          # 命中 1 条，直接给正文
"$PY" scripts/search.py 审批流流程完成 --full                 # 完整正文（不截断）
"$PY" scripts/search.py 库存 查询 --all --scope object --brief  # 多词全命中 + 精简
"$PY" scripts/search.py 商品 --scope object --limit 10

# 按对象 apiName 找（path 也参与检索，apiName 直接可用）
"$PY" scripts/search.py ProductObj --brief                   # 商品对象全部 8 个接口
"$PY" scripts/search.py WorkOrdersAndServices --brief        # 整个模块
"$PY" scripts/search.py PreventiveMaintenanceObj --brief     # 未登记 sidebar 的对象也能查到

# 按正文找（参数名、请求头、错误码…）
"$PY" scripts/search.py thirdTraceId --limit 5
"$PY" scripts/search.py x-fs-userid --brief

# 按分类浏览
"$PY" scripts/search.py --list --category 审批流程
"$PY" scripts/search.py --list --scope start

# 精确取一篇（默认输出完整正文）
"$PY" scripts/search.py --path /object/CommoditiesAndProducts/ProductObj/add
```

**选项**：`--scope S`（`start`/`object`/`common`/`faq`，可逗号组合，默认 `all`）·
`--category C`（分类子串，如 `库存与仓储`）· `--brief`（每条一行）·
`--full` / `-d`（完整正文，不截断）· `--all`（多词全命中）·
`--limit N`（默认 20）· `--max N`（非 `--full` 时每条正文上限，默认 1500 字符）·
`--list`（只列条目）· `--path P`（按 path 或标题精确取一篇）

> 检索**直接读 Markdown**，不依赖预生成字典，因此不存在「改了文档忘了重建索引导致搜不到」的漂移问题。
> 实测检索全部 1,307 篇约 **0.8 秒**。
> 修改过文档后，可用 `python scripts/build_index.py` 重新生成各级 `_INDEX.md`。

---

## 五、可运行示例（`examples/`）

`examples/` 下有一套**只依赖标准库**的最小可用代码，已用真实租户跑通：

| 脚本 | 作用 |
| :--- | :--- |
| `fxiaoke_client.py` / `fxiaoke_client.js` | 客户端封装：token 缓存（6600s）、自动 `thirdTraceId`、三个请求头 |
| `01_get_token.py` | 客户端凭证模式取 accessToken |
| `02_object_list.py` | 查对象列表（apiName → 中文显示名） |
| `03_query_objects.py` | 按条件查询对象列表 |
| `04_object_describe.py` | 查对象描述（字段清单） |
| `05_create_object.py` | 创建对象（**默认 dry-run**） |
| `06_approval_action.py` | 审批流完成/拒绝（**默认 dry-run**） |
| `07_invalid_and_delete.py` | 作废 → 删除（**默认 dry-run**） |

```bash
export FX_APP_ID=... FX_APP_SECRET=... FX_PERMANENT_CODE=... FX_USER_ID=1000
PY="<你的 python3 路径>"
"$PY" examples/01_get_token.py
"$PY" examples/02_object_list.py --grep 客户
"$PY" examples/05_create_object.py --object AccountObj --field name=示例客户   # 不加 --yes 不发送
```

**写操作默认只打印报文不发送**，加 `--yes` 才真正提交。凭据走环境变量或
`credentials.json`（已被 `.gitignore` 覆盖），**不要写进代码**。

> 📌 **实测踩坑清单见 [`examples/README.md`](./examples/README.md#实测踩坑文档没写或与文档不符)**。
> 其中几条比较关键：`x-fs-userid` 必须是**应用可见范围内**的数字员工ID
> （传 `openUserId` 报 10006，不在范围报 `20021 userScopeNotSupport`）；
> **全局返回码表与实际返回对不上**（只认 `errorCode`，原因看 `errorMessage`）；
> 手册的对象中文名未必等于你租户里的显示名，对接前先跑 `02_object_list.py`。

---

## 六、常见排错速查

| 现象 | 原因与处理 |
| :--- | :--- |
| `10006` 缺参数 | 实测多为 `X-fs-userId` 缺失或格式非法（**别照文档表理解成缺 scope**）；`openUserId` 不能当 `x-fs-userid` |
| `20021 userScopeNotSupport` | 该员工不在**应用的可见范围**内。换一个范围内的员工ID（文档表格把 20021 写成「app 停用」，与实际不符） |
| `20017 corpAccessToken为必填项` | `x-fs-userid` 传了空值，网关退回旧版校验。补上员工ID |
| `20016` / token 失效 | token 有效期 7200 秒，**缓存 6600 秒后必须刷新**；该接口不可并发调用 |
| 401 / 鉴权失败 | 检查 `authorization` 是否漏了 `Bearer ` 后的**空格**；`x-fs-ea`、`x-fs-userid` 是否齐全 |
| 员工 ID 对不上 | 新版传参默认不做 FSUID 转换；要转则 body 加 `{"convertUserId": true}` |
| 请求被拒 / 限流 | 每个 URL 必须带**唯一**的 `thirdTraceId`（UUID v4）；查频次限制说明 |
| 删除返回 0 却没删掉 | `data/invalid` **只作废单个 id**（传数组只生效第一个），未作废的记录 `data/delete` 会**静默跳过**。逐个作废后再删，删完再查一次 |
| 查不到数据 | 见 [`references/04_faq/人员对象查不到数据.md`](./references/04_faq/人员对象查不到数据.md) |
| 无此操作的数据权限 | 见 [`references/04_faq/无此操作的数据权限.md`](./references/04_faq/无此操作的数据权限.md) |
| 列表翻页翻不到底 | 见 [`references/04_faq/深翻页文档.md`](./references/04_faq/深翻页文档.md) |

> ⚠️ **不要照 `references/01_start/基础说明/全局返回码.md` 的表反推原因** ——
> 实测该表与线上返回多处不符（10006 / 20017 / 20021 都对不上）。
> 以响应里的 `errorMessage` / `errorDescription` 为准，代码里只判 `errorCode`。

---

## 七、目录结构

```
fxiaoke-dev/
├── SKILL.md                       # 本文件：接入 + 三块导航 + 检索 + 示例
├── README.md
├── examples/                      # 可运行示例（Python + Node，零依赖）
│   ├── README.md                  #   用法 + 实测踩坑清单
│   ├── fxiaoke_client.py / .js    #   客户端封装
│   ├── 01_get_token.py            #   取 token
│   ├── 02_object_list.py          #   对象列表（apiName → 中文名）
│   ├── 03_query_objects.py        #   条件查询
│   ├── 04_object_describe.py      #   字段清单
│   ├── 05_create_object.py        #   创建（dry-run）
│   ├── 06_approval_action.py      #   审批动作（dry-run）
│   ├── 07_invalid_and_delete.py   #   作废→删除（dry-run）
│   └── credentials.example.json   #   凭据模板（真实凭据不入库）
├── references/
│   ├── _INDEX.md                  # 1,307 篇总索引
│   ├── 01_start/                  # 【块三】快速开始与接入（15 篇）
│   │   └── <分类>/<标题>.md
│   ├── 02_object/                 # 【块一】对象接口（1,142 篇）
│   │   └── <模块>/<对象>/<标题>.md
│   ├── 03_common/                 # 【块二】通用接口（146 篇）
│   │   └── <分类>/<标题>.md
│   └── 04_faq/                    # 常见问题（4 篇）
├── scripts/
│   ├── search.py                  # 统一检索（三大块）
│   └── build_index.py             # 从 Markdown 生成各级 _INDEX.md
├── tools/
│   ├── extract_routes.py          # 从站点 app.js 提取全站路由 + 中文层级
│   ├── fetch_manual.py            # 批量抓取 + 转换 + 增量更新
│   ├── html2md.py                 # 零依赖 HTML → Markdown 转换器
│   └── selftest.py                # 完整性自检（抓取有没有丢 / 检索会不会静默截断）
└── _source/
    ├── _toc.json                  # 路由清单 + 中文层级映射
    ├── _files.json                # 页面 → 落盘文件清单（增量与清理的依据）
    └── _sidebar.json              # 站点 sidebar 配置（中文分类来源）
```

---

## 八、语料怎么更新

```bash
# 1) 重新提取路由（站点改版后必做；会自动下载最新的 app-*.js）
python tools/extract_routes.py

# 2) 增量抓取（已抓过的页面会跳过，只补新的）
python tools/fetch_manual.py

# 3) 强制重抓全量（转换规则改动后用）
python tools/fetch_manual.py --force --jobs 8

# 4) 重建索引
python scripts/build_index.py

# 5) 自检（--online N 会抽样联网核对文本保真）
python tools/selftest.py --online 60

# 6) 查看已下线页面（只列出，不删除）
python tools/fetch_manual.py --prune
```

---

## 九、免责声明

本 skill 内容整理自纷享销客（ShareCRM）官方公开文档，仅供学习、对接与二次开发参考。
接口名称、参数、返回结构及字段说明等版权归纷享销客所有。
示例中的真实凭据（appId / appSecret / permanentCode / accessToken / 企业 ea / 员工 id）均已脱敏，
使用前请替换为你自己的值。请遵守纷享销客相关许可与数据合规要求。
