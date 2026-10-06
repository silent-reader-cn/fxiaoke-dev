# -*- coding: utf-8 -*-
"""
纷享销客 OpenAPI v2 零依赖客户端（仅标准库）。

封装了三件容易踩坑的事：
  1. 客户端凭证模式取 accessToken，并按 6600 秒缓存（官方要求，见下）
  2. 每次请求自动生成唯一 thirdTraceId（UUID v4）
  3. 自动带齐 authorization / x-fs-ea / x-fs-userid 三个请求头

凭据来源（优先级从高到低）：
  1. 环境变量  FX_APP_ID / FX_APP_SECRET / FX_PERMANENT_CODE / FX_USER_ID / FX_DOMAIN
  2. credentials.json（当前目录，或 ../_local/credentials.json）

> ⚠️ 凭据不要写进代码，也不要提交进仓库。示例见 credentials.example.json。

用法：
    from fxiaoke_client import FxiaokeClient

    c = FxiaokeClient()                      # 自动读环境变量 / credentials.json
    print(c.access_token()[:8], "…")
    objs = c.call("/cgi/crm/v2/object/list", {"includeNull": False})
    for o in objs["data"]["objects"][:5]:
        print(o["describeApiName"], o["describeDisplayName"])

命令行自测：
    python fxiaoke_client.py                 # 取 token + 查对象列表前 5 个
"""
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

DEFAULT_DOMAIN = "https://open.fxiaoke.com"

# 官方说明：token 有效期 7200 秒；0–6600 秒内重复调用返回同一个 token，
# 6600–7200 秒之间返回新 token（新旧都可用），7200 秒后旧的失效。
# 所以缓存 6600 秒最稳。另外该接口每分钟不超过 10 次、不可并发调用。
TOKEN_TTL = 6600


class FxiaokeError(Exception):
    """接口返回非 0 errorCode 时抛出。"""

    def __init__(self, code, message, description=None, payload=None, path=None):
        self.code = code
        self.message = message
        self.description = description
        self.payload = payload or {}
        self.path = path
        super().__init__(f"[{code}] {message}"
                         + (f" / {description}" if description else "")
                         + (f"  (path={path})" if path else ""))


class FxiaokeClient:
    def __init__(self, app_id=None, app_secret=None, permanent_code=None,
                 user_id=None, domain=None, cache_dir=None, timeout=30, verbose=False):
        creds = _load_credentials()
        self.app_id = app_id or os.environ.get("FX_APP_ID") or creds.get("appId")
        self.app_secret = app_secret or os.environ.get("FX_APP_SECRET") or creds.get("appSecret")
        self.permanent_code = (permanent_code or os.environ.get("FX_PERMANENT_CODE")
                               or creds.get("permanentCode"))
        self.user_id = str(user_id or os.environ.get("FX_USER_ID")
                           or creds.get("userId") or "")
        self.domain = (domain or os.environ.get("FX_DOMAIN")
                       or creds.get("domain") or DEFAULT_DOMAIN).rstrip("/")
        self.timeout = timeout
        self.verbose = verbose

        missing = [n for n, v in [("appId", self.app_id), ("appSecret", self.app_secret),
                                  ("permanentCode", self.permanent_code)] if not v]
        if missing:
            raise SystemExit(
                "缺少凭据：" + ", ".join(missing)
                + "\n请设置环境变量 FX_APP_ID / FX_APP_SECRET / FX_PERMANENT_CODE，"
                  "或提供 credentials.json（见 credentials.example.json）。")

        self._cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
        self._cache_file = os.path.join(self._cache_dir, f"token_{self.app_id}.json")
        self._token = None
        self._ea = None

    # ---------------------------------------------------------------- token

    def _load_cached_token(self):
        try:
            d = json.load(open(self._cache_file, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None
        if time.time() - d.get("fetchedAt", 0) < TOKEN_TTL and d.get("accessToken"):
            return d
        return None

    def fetch_token(self, force=False):
        """取（或复用缓存的）accessToken。返回 dict。"""
        if not force:
            cached = self._load_cached_token()
            if cached:
                self._token, self._ea = cached["accessToken"], cached.get("ea")
                return cached

        url = f"{self.domain}/oauth2.0/token?thirdTraceId={uuid.uuid4()}"
        body = {
            "appId": self.app_id,
            "appSecret": self.app_secret,
            "permanentCode": self.permanent_code,
            "grantType": "app_secret",
        }
        d = self._http(url, body, headers=None)
        # 实测响应里 camelCase 与 snake_case 两套字段都会返回，统一取一下
        access = d.get("accessToken") or d.get("access_token")
        if d.get("errorCode") not in (0, None) or not access:
            raise FxiaokeError(d.get("errorCode"), d.get("errorMessage"),
                               d.get("errorDescription"), d, "/oauth2.0/token")
        out = {
            "accessToken": access,
            "ea": d.get("ea"),
            "openUserId": d.get("openUserId"),
            "expiresIn": d.get("expiresIn") or d.get("expires_in"),
            "tokenType": d.get("token_type") or "Bearer",
            "fetchedAt": time.time(),
        }
        self._token, self._ea = out["accessToken"], out["ea"]
        os.makedirs(self._cache_dir, exist_ok=True)
        with open(self._cache_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        return out

    @property
    def ea(self):
        if self._ea is None:
            self.fetch_token()
        return self._ea

    def access_token(self):
        if self._token is None:
            self.fetch_token()
        return self._token

    # ---------------------------------------------------------------- 请求

    def headers(self):
        """
        业务接口必带的三个头。

        ⚠️ x-fs-userid 必须是**该应用可见范围内的数字员工ID**：
          - 传 openUserId（FSCID_xxx）→ 10006「X-fs-userId is missing or illegal」
          - 传不在可见范围内的 id   → 20021「userScopeNotSupport」
          - 留空                   → 20017「corpAccessToken为必填项」
        """
        if not self.user_id:
            raise SystemExit(
                "缺少 x-fs-userid。请设置 FX_USER_ID 或 credentials.json 的 userId。\n"
                "取值 = CRM 后台「人员 → 系统名 → 账号信息 → 员工ID」，"
                "且该员工必须在应用的可见范围内。")
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token()}",
            "x-fs-ea": str(self.ea),
            "x-fs-userid": str(self.user_id),
            "User-Agent": "fxiaoke-dev-skill/1.0",
        }

    def call(self, path, body=None, method="POST", raise_on_error=True):
        """
        调一个业务接口。path 形如 /cgi/crm/v2/data/query。
        thirdTraceId 自动生成，无需自己传。
        """
        sep = "&" if "?" in path else "?"
        url = f"{self.domain}{path}{sep}thirdTraceId={uuid.uuid4()}"
        d = self._http(url, body, self.headers(), method=method)
        code = d.get("errorCode")
        if raise_on_error and code not in (0, None):
            raise FxiaokeError(code, d.get("errorMessage"), d.get("errorDescription"), d, path)
        return d

    def _http(self, url, body, headers=None, method="POST"):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        h = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}
        h.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        if self.verbose:
            safe = {k: ("***" if k.lower() in ("authorization",) else v) for k, v in h.items()}
            print(f"  → {method} {url.split('?')[0]}  {safe}", file=sys.stderr)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                text = raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raw = e.read()
            text = raw.decode("utf-8", "replace")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise FxiaokeError("NON_JSON", text[:200], None, None, url) from None

    # ---------------------------------------------------------------- 便捷方法

    def object_list(self):
        """查询对象列表：apiName → 中文显示名。"""
        d = self.call("/cgi/crm/v2/object/list", {"includeNull": False})
        return (d.get("data") or {}).get("objects") or []

    def object_describe(self, api_name, include_detail=False):
        """查询对象描述（字段清单）。"""
        d = self.call("/cgi/crm/v2/object/describe",
                      {"includeNull": True, "includeDetail": include_detail,
                       "data": {"apiName": api_name}})
        return (d.get("data") or {}).get("describe") or {}

    def query(self, api_name, filters=None, limit=20, offset=0,
              field_projection=None, orders=None, return_total_num=1):
        """按条件查询对象列表（POST /cgi/crm/v2/data/query）。"""
        sqi = {
            "offset": offset,
            "limit": min(int(limit), 100),   # 官方上限 100
            "filters": filters or [],
        }
        if field_projection:
            sqi["fieldProjection"] = field_projection
        if orders:
            sqi["orders"] = orders
        return self.call("/cgi/crm/v2/data/query", {
            "returnTotalNum": return_total_num,
            "data": {"search_query_info": sqi, "dataObjectApiName": api_name},
        })

    def create(self, api_name, object_data, **opts):
        """创建对象（POST /cgi/crm/v2/data/create）。"""
        payload = {
            "data": {"object_data": dict(object_data, dataObjectApiName=api_name)},
        }
        for k in ("triggerApprovalFlow", "triggerWorkFlow", "hasSpecifyTime",
                  "hasSpecifyCreatedBy", "includeDetailIds"):
            if k in opts:
                payload[k] = opts[k]
        return self.call("/cgi/crm/v2/data/create", payload)

    def approval_action(self, task_id, opinion, action_type="agree"):
        """审批流流程完成（POST /cgi/crm/approvalTask/action）。"""
        return self.call("/cgi/crm/approvalTask/action", {
            "taskId": task_id, "opinion": opinion, "actionType": action_type,
        })


def _load_credentials():
    """按优先级找 credentials.json。"""
    here = os.path.dirname(os.path.abspath(__file__))
    for p in [os.path.join(os.getcwd(), "credentials.json"),
              os.path.join(here, "credentials.json"),
              os.path.join(here, "..", "_local", "credentials.json")]:
        if os.path.exists(p):
            try:
                return json.load(open(p, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
    return {}


if __name__ == "__main__":
    c = FxiaokeClient(verbose="-v" in sys.argv)
    t = c.fetch_token()
    print(f"domain={c.domain}")
    print(f"ea={t['ea']}  expiresIn={t['expiresIn']}  userid={c.user_id}")
    objs = c.object_list()
    print(f"对象总数 {len(objs)}，前 5 个：")
    for o in objs[:5]:
        print(f"  {o.get('describeApiName'):34s} {o.get('describeDisplayName')}")
