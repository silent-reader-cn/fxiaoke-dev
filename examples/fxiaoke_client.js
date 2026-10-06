/**
 * 纷享销客 OpenAPI v2 零依赖客户端（Node.js，仅用内置模块）。
 *
 * 与 fxiaoke_client.py 能力对齐：token 缓存、自动 thirdTraceId、三个请求头。
 * 凭据来源：环境变量 FX_APP_ID / FX_APP_SECRET / FX_PERMANENT_CODE / FX_USER_ID / FX_DOMAIN，
 *           或 credentials.json（当前目录 / ../_local/）。
 *
 * 用法：
 *   const { FxiaokeClient } = require('./fxiaoke_client');
 *   const c = new FxiaokeClient();
 *   const objs = await c.objectList();
 *   console.log(objs.slice(0, 5));
 *
 * 命令行自测： node fxiaoke_client.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const https = require('https');
const crypto = require('crypto');

const DEFAULT_DOMAIN = 'https://open.fxiaoke.com';
const TOKEN_TTL = 6600; // 官方：token 有效期 7200 秒，缓存 6600 秒后刷新最稳

function loadCredentials() {
  const here = __dirname;
  const candidates = [
    path.join(process.cwd(), 'credentials.json'),
    path.join(here, 'credentials.json'),
    path.join(here, '..', '_local', 'credentials.json'),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { /* ignore */ }
    }
  }
  return {};
}

class FxiaokeError extends Error {
  constructor(code, message, description, path_) {
    super(`[${code}] ${message}${description ? ' / ' + description : ''}`);
    this.code = code;
    this.description = description;
    this.path = path_;
  }
}

class FxiaokeClient {
  constructor(opts = {}) {
    const creds = loadCredentials();
    this.appId = opts.appId || process.env.FX_APP_ID || creds.appId;
    this.appSecret = opts.appSecret || process.env.FX_APP_SECRET || creds.appSecret;
    this.permanentCode = opts.permanentCode || process.env.FX_PERMANENT_CODE || creds.permanentCode;
    this.userId = String(opts.userId || process.env.FX_USER_ID || creds.userId || '');
    this.domain = (opts.domain || process.env.FX_DOMAIN || creds.domain || DEFAULT_DOMAIN).replace(/\/$/, '');
    this.timeout = opts.timeout || 30000;
    this.cacheFile = opts.cacheFile
      || path.join(__dirname, '.cache', `token_${this.appId}.json`);
    this._token = null;
    this._ea = null;

    const missing = [['appId', this.appId], ['appSecret', this.appSecret], ['permanentCode', this.permanentCode]]
      .filter(([, v]) => !v).map(([k]) => k);
    if (missing.length) {
      throw new Error(`缺少凭据：${missing.join(', ')}。请设环境变量或提供 credentials.json`);
    }
  }

  // ------------------------------------------------------------- 内部 HTTP
  _request(url, body, headers = {}) {
    const u = new URL(url);
    const data = body === undefined || body === null ? null : Buffer.from(JSON.stringify(body), 'utf8');
    const h = Object.assign({
      'Content-Type': 'application/json',
      'Accept-Encoding': 'identity',
    }, headers);
    if (data) h['Content-Length'] = data.length;

    return new Promise((resolve, reject) => {
      const req = https.request({
        hostname: u.hostname,
        port: u.port || 443,
        path: u.pathname + u.search,
        method: 'POST',
        headers: h,
        timeout: this.timeout,
      }, (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          try { resolve(JSON.parse(text)); }
          catch (e) { reject(new FxiaokeError('NON_JSON', text.slice(0, 200))); }
        });
      });
      req.on('timeout', () => req.destroy(new Error('请求超时')));
      req.on('error', reject);
      if (data) req.write(data);
      req.end();
    });
  }

  // ------------------------------------------------------------- token
  async fetchToken(force = false) {
    if (!force) {
      try {
        const d = JSON.parse(fs.readFileSync(this.cacheFile, 'utf8'));
        if (Date.now() / 1000 - (d.fetchedAt || 0) < TOKEN_TTL && d.accessToken) {
          this._token = d.accessToken;
          this._ea = d.ea;
          return d;
        }
      } catch (e) { /* 没缓存 */ }
    }
    const url = `${this.domain}/oauth2.0/token?thirdTraceId=${crypto.randomUUID()}`;
    const r = await this._request(url, {
      appId: this.appId,
      appSecret: this.appSecret,
      permanentCode: this.permanentCode,
      grantType: 'app_secret',
    });
    const access = r.accessToken || r.access_token; // 实测两套字段都会返回
    if ((r.errorCode !== 0 && r.errorCode !== undefined) || !access) {
      throw new FxiaokeError(r.errorCode, r.errorMessage, r.errorDescription, '/oauth2.0/token');
    }
    const out = {
      accessToken: access,
      ea: r.ea,
      openUserId: r.openUserId,
      expiresIn: r.expiresIn || r.expires_in,
      tokenType: r.token_type || 'Bearer',
      fetchedAt: Date.now() / 1000,
    };
    this._token = out.accessToken;
    this._ea = out.ea;
    fs.mkdirSync(path.dirname(this.cacheFile), { recursive: true });
    fs.writeFileSync(this.cacheFile, JSON.stringify(out, null, 1), 'utf8');
    return out;
  }

  async accessToken() {
    if (!this._token) await this.fetchToken();
    return this._token;
  }

  async headers() {
    // ⚠️ x-fs-userid 必须是该应用**可见范围内**的数字员工ID。
    //    传 openUserId → 10006；不在范围内 → 20021 userScopeNotSupport；留空 → 20017。
    if (!this.userId) throw new Error('缺少 FX_USER_ID（应用可见范围内的数字员工ID）');
    return {
      authorization: `Bearer ${await this.accessToken()}`,
      'x-fs-ea': String(this._ea),
      'x-fs-userid': String(this.userId),
      'User-Agent': 'fxiaoke-dev-skill/1.0',
    };
  }

  async call(apiPath, body = null) {
    const sep = apiPath.includes('?') ? '&' : '?';
    const url = `${this.domain}${apiPath}${sep}thirdTraceId=${crypto.randomUUID()}`;
    const r = await this._request(url, body, await this.headers());
    if (r.errorCode !== 0 && r.errorCode !== undefined) {
      throw new FxiaokeError(r.errorCode, r.errorMessage, r.errorDescription, apiPath);
    }
    return r;
  }

  // ------------------------------------------------------------- 便捷方法
  async objectList() {
    const r = await this.call('/cgi/crm/v2/object/list', { includeNull: false });
    return (r.data && r.data.objects) || [];
  }

  async objectDescribe(apiName, includeDetail = false) {
    const r = await this.call('/cgi/crm/v2/object/describe', {
      includeNull: true, includeDetail, data: { apiName },
    });
    return (r.data && r.data.describe) || {};
  }

  async query(apiName, { filters = [], limit = 20, offset = 0, fieldProjection, orders } = {}) {
    const sqi = { offset, limit: Math.min(limit, 100), filters };
    if (fieldProjection) sqi.fieldProjection = fieldProjection;
    if (orders) sqi.orders = orders;
    return this.call('/cgi/crm/v2/data/query', {
      returnTotalNum: 1,
      data: { search_query_info: sqi, dataObjectApiName: apiName },
    });
  }

  async create(apiName, objectData) {
    // 新建记录的 id 在**响应顶层** dataId
    return this.call('/cgi/crm/v2/data/create', {
      data: { object_data: Object.assign({}, objectData, { dataObjectApiName: apiName }) },
    });
  }

  async approvalAction(taskId, opinion, actionType = 'agree') {
    return this.call('/cgi/crm/approvalTask/action', { taskId, opinion, actionType });
  }
}

module.exports = { FxiaokeClient, FxiaokeError };

if (require.main === module) {
  (async () => {
    const c = new FxiaokeClient();
    const t = await c.fetchToken();
    console.log(`domain=${c.domain}  ea=${t.ea}  expiresIn=${t.expiresIn}  userid=${c.userId}`);
    const objs = await c.objectList();
    console.log(`对象总数 ${objs.length}，前 5 个：`);
    objs.slice(0, 5).forEach((o) => console.log(`  ${o.describeApiName.padEnd(34)} ${o.describeDisplayName}`));
  })().catch((e) => { console.error('失败：', e.message); process.exit(1); });
}
