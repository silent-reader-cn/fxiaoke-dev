# examples —— 可运行示例

对接纷享销客 OpenAPI v2 的最小可用代码。**只依赖 Python 3 / Node.js 内置模块**，无需装任何包。

## 先配凭据（重要）

凭据**不要写进代码、不要提交**。两种方式任选：

**方式一：环境变量**（推荐）

```bash
export FX_APP_ID="FSAID_xxxxxxx"
export FX_APP_SECRET="<自建应用的 appSecret>"
export FX_PERMANENT_CODE="<永久授权码>"
export FX_USER_ID="1000"                 # 应用可见范围内的数字员工ID
export FX_DOMAIN="https://open.fxiaoke.com"
```

**方式二：credentials.json**

把 `credentials.example.json` 复制成 `credentials.json` 填好，放在当前目录或 `../_local/` 下。
仓库的 `.gitignore` 已覆盖 `credentials.json` 与 `_local/`，不会误提交。

> `FX_USER_ID` 必须是**该应用可见范围内的数字员工ID**，不是 `openUserId`。
> 取值 = CRM 后台「人员 → 系统名 → 账号信息 → 员工ID」。
> 填错的表现见下方"实测踩坑"。

## 示例清单

| 脚本 | 作用 | 对应文档 |
| :--- | :--- | :--- |
| `fxiaoke_client.py` / `fxiaoke_client.js` | 客户端封装（token 缓存、自动 thirdTraceId、三个请求头） | — |
| `01_get_token.py` | 客户端凭证模式取 accessToken | [`01_start/OAuth授权认证/客户端凭证模式.md`](../references/01_start/OAuth授权认证/客户端凭证模式.md) |
| `02_object_list.py` | 查对象列表（apiName → 中文显示名） | [`03_common/系统接口/对象描述/查询对象列表.md`](../references/03_common/系统接口/对象描述/查询对象列表.md) |
| `03_query_objects.py` | 按条件查询对象列表 | [`02_object/.../根据条件查询*对象的列表.md`](../references/02_object/) |
| `04_object_describe.py` | 查对象描述（字段清单） | [`03_common/系统接口/对象描述/查询对象描述.md`](../references/03_common/系统接口/对象描述/查询对象描述.md) |
| `05_create_object.py` | 创建对象（默认 dry-run） | [`02_object/.../创建*对象.md`](../references/02_object/) |
| `06_approval_action.py` | 审批流完成/拒绝（默认 dry-run） | [`03_common/流程与规则/审批流程/审批流流程完成.md`](../references/03_common/流程与规则/审批流程/审批流流程完成.md) |
| `07_invalid_and_delete.py` | 作废 → 删除（默认 dry-run） | [`02_object/.../作废*对象信息.md`](../references/02_object/) |

```bash
PY="<你的 python3 路径>"

"$PY" 01_get_token.py                       # 先确认能拿到 token
"$PY" 02_object_list.py --grep 客户           # 看看你租户里有哪些对象
"$PY" 03_query_objects.py --object AccountObj --limit 5
"$PY" 04_object_describe.py --object AccountObj --grep 电话
"$PY" 05_create_object.py --object AccountObj --field name=示例客户   # 默认不发送

node fxiaoke_client.js                      # Node 版
```

**写操作默认 dry-run**（`05` / `06` / `07` 只打印报文不发送），确认无误后加 `--yes`。

## 实测踩坑（文档没写，或与文档不符）

以下都是拿真实租户跑出来的，不是推测：

1. **`x-fs-userid` 有可见范围限制**
   - 传 `openUserId`（`FSCID_xxx`）→ `10006 the parameter [X-fs-userId] is missing or illegal`
   - 传不在应用可见范围内的员工ID → `20021 userScopeNotSupport`
   - 留空 → `20017 corpAccessToken为必填项，不能为空`（网关退回了旧版校验）
   - 文档的「公共参数填写」只说了去哪找员工ID，**没提可见范围**，容易卡住。

2. **全局返回码表与实际返回对不上**（`references/01_start/基础说明/全局返回码.md`）

   | 错误码 | 文档说 | 实测返回 |
   | :--- | :--- | :--- |
   | 10006 | 缺少参数 scope | the parameter [X-fs-userId] is missing or illegal |
   | 20017 | corpId 未找到 | corpAccessToken为必填项，不能为空 |
   | 20021 | 该 app 的状态为停用 | userScopeNotSupport |

   → **只认 `errorCode`，具体原因看 `errorMessage` / `errorDescription`**，别照文档表反推。

3. **token 响应有两套字段名**：除文档写的 `accessToken` / `expiresIn`，还返回
   `access_token` / `expires_in` / `token_type`。`ea` 也可能是带后缀的字符串
   （实测形如 `<企业号>_sandbox`），别假定是纯数字。

4. **同一平台两套命名风格**：`/cgi/crm/v2/object/list` 用 camelCase
   （`describeApiName` / `describeDisplayName`），`/cgi/crm/v2/object/describe`
   用 snake_case（`api_name` / `is_required`）。写通用解析时要注意。

5. **`describe` 响应没有顶层显示名**，中文名要从 `object/list` 取。
   字段结构是 `fields.<apiName>.{label, type, is_required, options}`。

6. **`create` 返回的记录 id 在响应顶层 `dataId`**，不在 `data` 里。

7. **`data/invalid` 只接受单个 id**（文档写「数据id列表」，示例却是字符串）；
   传数组不报错，但**只作废第一个**。而 `data/delete` 对**未作废**的记录会
   返回 `errorCode: 0` 却**不删**（静默部分失败）。
   → 必须逐个作废，作废完再批量删除，删完**再查一次确认**。

8. **手册的对象清单 ≠ 你租户的对象清单**。实测某租户 176 个对象，与手册收录的
   211 个只重合 52 个；且有 19 个对象的中文名与手册 sidebar 不一致
   （例：`ProductObj` 手册标「商品」，租户实际显示「产品」）。
   → 手册的对象中文名是**手册作者的标签**，对接前先用 `02_object_list.py`
     拉一份自己租户的清单，以它为准。

## 免责声明

示例中的凭据均为占位符。请使用你自己的应用凭据，并遵守纷享销客相关许可与数据合规要求。
