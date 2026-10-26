#!/usr/bin/env python3
"""Zalo Official Account API client for this workflow.

Each Zalo application (app_id) authorized on an OA has its own secret key and token pair,
stored in config/secrets/zalo/<app_id>.json (gitignored, never printed):
  {"secret_key": "...", "refresh_token": "...", "access_token": "...", "expires_at": <epoch s>}

Zalo refresh tokens are single-use: every refresh returns a new refresh token that must be
saved before anything else, otherwise the application must be re-authorized. Refreshing is
therefore guarded by a lock file so two runs never use the same refresh token.

CLI usage:
  python3 scripts/zalo_oa.py <app_id> auth-url <redirect_uri>  # PKCE link for the OA admin to open
  python3 scripts/zalo_oa.py <app_id> init < secret.json      # stdin: {"secret_key", "refresh_token"}
                                                              #     or {"secret_key", "code"} after auth-url
  python3 scripts/zalo_oa.py <app_id> check                 # refresh if needed + read OA info
  python3 scripts/zalo_oa.py <app_id> recent [offset] [count]
  python3 scripts/zalo_oa.py <app_id> conversation <user_id> [offset] [count]
  python3 scripts/zalo_oa.py <app_id> profile <user_id>
  python3 scripts/zalo_oa.py <app_id> tags                  # tag names of the OA
  python3 scripts/zalo_oa.py <app_id> send-text <user_id> '<text>' --confirm

Output: one JSON object on stdout, {"ok": true, ...} or {"ok": false, "error": ...}.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = ROOT / "config" / "secrets" / "zalo"
OAUTH_URL = "https://oauth.zaloapp.com/v4/oa/access_token"
API = "https://openapi.zalo.me"
REFRESH_MARGIN_S = 30 * 60
# Error codes Zalo returns when the access token is invalid or expired.
TOKEN_ERRORS = {-216, -124, -14002, -14014}


class ZaloError(Exception):
    def __init__(self, msg, **extra):
        super().__init__(msg)
        self.extra = extra


def secret_path(app_id):
    return SECRETS_DIR / f"{app_id}.json"


def load_secret(app_id):
    p = secret_path(app_id)
    if not p.is_file():
        raise ZaloError(f"Chưa có khóa cho ứng dụng {app_id}; chạy scripts/zalo_save_app trước.",
                        code="missing_secret")
    return json.loads(p.read_text())


def save_secret(app_id, data):
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    p = secret_path(app_id)
    tmp = p.with_suffix(".tmp")
    old_umask = os.umask(0o077)
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        os.replace(tmp, p)
    finally:
        os.umask(old_umask)


class Lock:
    """Cross-platform lock file (O_EXCL), stale after 120 s."""

    def __init__(self, path, timeout=90):
        self.path, self.timeout = Path(path), timeout

    def __enter__(self):
        deadline = time.time() + self.timeout
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 120:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    raise ZaloError("Một tiến trình khác đang làm mới token Zalo; thử lại sau.", code="busy")
                time.sleep(1)

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def http(method, url, headers=None, data=None, timeout=60):
    body = None
    headers = dict(headers or {})
    if data is not None:
        if headers.get("Content-Type") == "application/x-www-form-urlencoded":
            body = urllib.parse.urlencode(data).encode()
        else:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        if not text.strip().startswith("{"):
            raise ZaloError(f"HTTP {e.code} từ Zalo", detail=text[:300])
    except urllib.error.URLError as e:
        raise ZaloError("Không kết nối được tới Zalo", detail=str(e.reason)[:300])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ZaloError("Zalo trả về dữ liệu không đọc được", detail=text[:300])


def oauth_request(app_id, secret_key, params):
    res = http("POST", OAUTH_URL,
               headers={"secret_key": secret_key, "Content-Type": "application/x-www-form-urlencoded"},
               data={"app_id": app_id, **params})
    if not res.get("access_token"):
        raise ZaloError("Zalo từ chối cấp token", detail={k: res.get(k) for k in ("error", "error_name",
                                                                                    "error_reason", "error_description")},
                        code="oauth_rejected")
    return res


def store_tokens(app_id, secret, res):
    secret["access_token"] = res["access_token"]
    secret["refresh_token"] = res.get("refresh_token") or secret.get("refresh_token")
    secret["expires_at"] = int(time.time()) + int(res.get("expires_in", 3600))
    secret["refreshed_at"] = int(time.time())
    save_secret(app_id, secret)


class ZaloApp:
    def __init__(self, app_id):
        self.app_id = str(app_id)

    def _refresh(self, force=False):
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        with Lock(SECRETS_DIR / f"{self.app_id}.lock"):
            secret = load_secret(self.app_id)  # re-read: another run may have refreshed already
            fresh = secret.get("access_token") and secret.get("expires_at", 0) - time.time() > REFRESH_MARGIN_S
            if fresh and not force:
                return secret["access_token"]
            if force and time.time() - secret.get("refreshed_at", 0) < 60:
                return secret["access_token"]
            if not secret.get("refresh_token"):
                raise ZaloError("Thiếu refresh token; cần ủy quyền lại ứng dụng.", code="reauthorize")
            try:
                res = oauth_request(self.app_id, secret["secret_key"],
                                    {"refresh_token": secret["refresh_token"], "grant_type": "refresh_token"})
            except ZaloError as e:
                if e.extra.get("code") == "oauth_rejected":
                    e.extra["code"] = "reauthorize"
                raise
            store_tokens(self.app_id, secret, res)
            return secret["access_token"]

    def token(self):
        secret = load_secret(self.app_id)
        if secret.get("access_token") and secret.get("expires_at", 0) - time.time() > REFRESH_MARGIN_S:
            return secret["access_token"]
        return self._refresh()

    def call(self, method, path, params=None, body=None, _retry=True):
        url = API + path
        if params is not None:
            url += "?data=" + urllib.parse.quote(json.dumps(params, ensure_ascii=False))
        res = http(method, url, headers={"access_token": self.token()}, data=body)
        err = res.get("error", 0)
        if err in TOKEN_ERRORS and _retry:
            self._refresh(force=True)
            return self.call(method, path, params, body, _retry=False)
        if err not in (0, None):
            raise ZaloError(f"Zalo lỗi {err}: {res.get('message')}", zalo_error=err)
        time.sleep(0.15)  # stay well below Zalo's per-app rate limit
        return res

    def oa_info(self):
        return self.call("GET", "/v2.0/oa/getoa").get("data", {})

    def recent_chats(self, offset=0, count=10):
        return self.call("GET", "/v2.0/oa/listrecentchat",
                         {"offset": int(offset), "count": min(int(count), 10)}).get("data", []) or []

    def conversation(self, user_id, offset=0, count=10):
        return self.call("GET", "/v2.0/oa/conversation",
                         {"user_id": int(user_id), "offset": int(offset),
                          "count": min(int(count), 10)}).get("data", []) or []

    def profile(self, user_id):
        return self.call("GET", "/v3.0/oa/user/detail", {"user_id": str(user_id)}).get("data", {})

    def users_by_tag(self, tag_name, period=None, offset=0, count=50):
        """User ids carrying an OA tag; period: TODAY, YESTERDAY, L7D, L30D or 'YYYY_MM_DD:YYYY_MM_DD'."""
        params = {"offset": int(offset), "count": min(int(count), 50), "tag_name": tag_name}
        if period:
            params["last_interaction_period"] = period
        data = self.call("GET", "/v3.0/oa/user/getlist", params).get("data", {}) or {}
        return [str(u["user_id"]) for u in data.get("users", [])], int(data.get("total", 0))

    def list_tags(self):
        return self.call("GET", "/v2.0/oa/tag/gettagsofoa").get("data", []) or []

    def tag_user(self, user_id, tag_name):
        return self.call("POST", "/v2.0/oa/tag/tagfollower", body={"user_id": int(user_id), "tag_name": tag_name})

    def untag_user(self, user_id, tag_name):
        return self.call("POST", "/v2.0/oa/tag/rmfollowerfromtag", body={"user_id": int(user_id), "tag_name": tag_name})

    def send_text(self, user_id, text):
        return self.call("POST", "/v3.0/oa/message/cs",
                         body={"recipient": {"user_id": str(user_id)}, "message": {"text": text}})


def auth_url(app_id, redirect_uri):
    import base64
    import hashlib
    import secrets as pysecrets
    verifier = pysecrets.token_urlsafe(32)[:43]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = pysecrets.token_urlsafe(8)
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    pending = SECRETS_DIR / f"{app_id}.pkce.json"
    old_umask = os.umask(0o077)
    try:
        pending.write_text(json.dumps({"code_verifier": verifier, "state": state, "created_at": int(time.time())}))
    finally:
        os.umask(old_umask)
    query = urllib.parse.urlencode({"app_id": app_id, "redirect_uri": redirect_uri,
                                    "code_challenge": challenge, "state": state})
    return {"ok": True, "url": f"https://oauth.zaloapp.com/v4/oa/permission?{query}", "state": state}


def init_app(app_id, payload):
    secret_key = (payload.get("secret_key") or "").strip()
    if not secret_key:
        raise ZaloError("Thiếu secret key của ứng dụng.")
    if payload.get("refresh_token"):
        params = {"refresh_token": payload["refresh_token"].strip(), "grant_type": "refresh_token"}
    elif payload.get("code"):
        pending = SECRETS_DIR / f"{app_id}.pkce.json"
        if not pending.is_file():
            raise ZaloError("Không tìm thấy phiên ủy quyền; chạy auth-url lại.")
        params = {"code": payload["code"].strip(), "grant_type": "authorization_code",
                  "code_verifier": json.loads(pending.read_text())["code_verifier"]}
    else:
        raise ZaloError("Cần refresh_token hoặc code.")
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    with Lock(SECRETS_DIR / f"{app_id}.lock"):
        res = oauth_request(app_id, secret_key, params)
        store_tokens(app_id, {"secret_key": secret_key}, res)
    (SECRETS_DIR / f"{app_id}.pkce.json").unlink(missing_ok=True)
    info = ZaloApp(app_id).oa_info()
    return {"ok": True, "saved": str(secret_path(app_id).relative_to(ROOT)),
            "oa_id": str(info.get("oa_id", "")), "oa_name": info.get("name")}


def main():
    args = [a for a in sys.argv[1:] if a != "--confirm"]
    if len(args) < 2:
        raise ZaloError(__doc__.strip().splitlines()[0])
    app = ZaloApp(args[0])
    cmd, rest = args[1], args[2:]
    if cmd == "auth-url":
        return auth_url(app.app_id, rest[0])
    if cmd == "init":
        return init_app(app.app_id, json.loads(sys.stdin.read() or "{}"))
    if cmd == "check":
        info = app.oa_info()
        secret = load_secret(app.app_id)
        return {"ok": True, "oa_id": str(info.get("oa_id", "")), "oa_name": info.get("name"),
                "token_expires_at": secret.get("expires_at")}
    if cmd == "recent":
        return {"ok": True, "data": app.recent_chats(*(rest or [0, 10]))}
    if cmd == "conversation":
        return {"ok": True, "data": app.conversation(*rest)}
    if cmd == "profile":
        return {"ok": True, "data": app.profile(rest[0])}
    if cmd == "tags":
        return {"ok": True, "data": app.list_tags()}
    if cmd == "send-text":
        if "--confirm" not in sys.argv:
            raise ZaloError("send-text cần --confirm sau khi người dùng duyệt nội dung.")
        res = app.send_text(rest[0], rest[1])
        return {"ok": True, "message_id": (res.get("data") or {}).get("message_id")}
    raise ZaloError(f"unknown command {cmd}")


if __name__ == "__main__":
    try:
        out = main()
    except ZaloError as e:
        print(json.dumps({"ok": False, "error": str(e), **e.extra}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(out, ensure_ascii=False))
