#!/usr/bin/env python3
"""TinaCRM REST client: the only way this workflow reads and writes TinaCRM.

Reads the API key from config/tinacrm_api_key.txt (never printed) and calls
<base>/rest/... with curl, because Python's SSL stack rejects the current
*.tinacrm.com certificate chain on some machines.

CLI usage:
  python3 scripts/tinacrm_rest.py <base_url> check
  python3 scripts/tinacrm_rest.py <base_url> upsert-company     '<json>'
  python3 scripts/tinacrm_rest.py <base_url> upsert-person      '<json>'
  python3 scripts/tinacrm_rest.py <base_url> upsert-opportunity '<json>'
  python3 scripts/tinacrm_rest.py <base_url> create-task        '<json>'
  python3 scripts/tinacrm_rest.py <base_url> create-note        '<json>'
  python3 scripts/tinacrm_rest.py <base_url> update <object-plural> <id> '<json>'
  python3 scripts/tinacrm_rest.py <base_url> get <object-plural> [filter]
  python3 scripts/tinacrm_rest.py <base_url> members

upsert-company:     {"name", "domain"?, "city"?, "country"?}
  Matches an existing company by domain, then by exact name.
upsert-person:      {"firstName", "lastName"?, "email"?, "phone"?, "jobTitle"?, "city"?,
                     "companyId"?, "id"?, "extra"?: {<custom field>: <value>},
                     "matchField"?: "<custom field>", "matchValue"?: "<value>"}
  Matches by "id" (known from the local ledger), then primary email, then phone,
  then the custom field given in matchField (e.g. the Zalo user id field).
upsert-opportunity: {"name", "id"?, "amount"?, "currency"?, "stage"?, "closeDate"?,
                     "companyId"?, "pointOfContactId"?}
  With "id": updates stage/amount/closeDate. Without: creates.
create-task:        {"title", "body"?, "dueAt"?, "status"?, "assigneeId"?,
                     "personId"?, "companyId"?, "opportunityId"?}
create-note:        {"title", "body"?, "personId"?, "companyId"?, "opportunityId"?}

Field names follow the TinaCRM (Twenty-based) standard schema. Custom fields and
pipeline stages differ per workspace: check <base_url>/rest/open-api/core first.

Output: one JSON object on stdout, {"ok": true, ...} or {"ok": false, "error": ...}.
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

KEY_FILE = Path(__file__).resolve().parent.parent / "config" / "tinacrm_api_key.txt"


class TinaError(Exception):
    def __init__(self, msg, **extra):
        super().__init__(msg)
        self.extra = extra


def load_key():
    if not KEY_FILE.is_file() or not KEY_FILE.read_text().strip():
        raise TinaError("Missing API key in config/tinacrm_api_key.txt; run tinacrm_save_key first.")
    return "".join(KEY_FILE.read_text().split())


def normalize_vn_phone(raw):
    """Returns (national_number_without_leading_zero, calling_code) or (None, None)."""
    if not raw:
        return None, None
    digits = re.sub(r"[^\d+]", "", str(raw))
    if digits.startswith("+84"):
        digits = digits[3:]
    elif digits.startswith("84") and len(digits) >= 11:
        digits = digits[2:]
    digits = digits.lstrip("0")
    if not re.fullmatch(r"\d{8,10}", digits):
        return None, None
    return digits, "+84"


class Client:
    def __init__(self, base):
        base = base.rstrip("/")
        if base.endswith("/mcp"):
            base = base[:-4]
        self.base = base + "/rest"
        self.key = load_key()

    def call(self, method, path, body=None):
        # Header passed via stdin config so the key never shows up in `ps`.
        cfg = f'header = "Authorization: Bearer {self.key}"\n'
        cmd = ["curl", "-s", "-m", "60", "-K", "-", "-X", method,
               "-H", "Content-Type: application/json",
               "-w", "\n%{http_code}", self.base + path]
        if body is not None:
            cmd += ["--data-binary", json.dumps(body, ensure_ascii=False)]
        res = subprocess.run(cmd, input=cfg, capture_output=True, text=True)
        if res.returncode != 0:
            raise TinaError(f"curl exit {res.returncode}", detail=res.stderr.strip()[:300])
        text, _, code = res.stdout.rpartition("\n")
        try:
            data = json.loads(text) if text.strip() else {}
        except json.JSONDecodeError:
            data = {"raw": text[:300]}
        if not code.startswith("2"):
            raise TinaError(f"HTTP {code} on {method} {path}", detail=data)
        return data

    def find(self, plural, flt, limit=5):
        data = self.call("GET", f"/{plural}?limit={limit}&filter={quote(flt)}")
        return data.get("data", {}).get(plural, [])

    def write(self, method, path, body):
        """Workspaces differ (e.g. some have no person.city): drop fields the object lacks and retry."""
        self.dropped = []
        while True:
            try:
                return self.call(method, path, body)
            except TinaError as e:
                msgs = " ".join(str(m) for m in (e.extra.get("detail") or {}).get("messages", []))
                m = re.search(r"doesn't have any \"([^\"]+)\" field", msgs)
                if not m or m.group(1) not in body:
                    raise
                body = {k: v for k, v in body.items() if k != m.group(1)}
                self.dropped.append(m.group(1))

    def create(self, plural, singular, body):
        data = self.write("POST", f"/{plural}", body)
        return data.get("data", {}).get(f"create{singular[0].upper()}{singular[1:]}", data)

    def update(self, plural, singular, rec_id, body):
        data = self.write("PATCH", f"/{plural}/{rec_id}", body)
        return data.get("data", {}).get(f"update{singular[0].upper()}{singular[1:]}", data)


SINGULAR = {"people": "person", "companies": "company", "opportunities": "opportunity",
            "tasks": "task", "notes": "note"}


def link(url):
    return {"primaryLinkUrl": url, "primaryLinkLabel": ""} if url else None


def clean(d):
    return {k: v for k, v in d.items() if v not in (None, "", {}, [])}


def q(value):
    return str(value).replace('"', '\\"')


def upsert_company(c, a):
    if not a.get("name"):
        raise TinaError("name is required")
    domain = a.get("domain")
    if domain and not domain.startswith("http"):
        domain = "https://" + domain
    found = c.find("companies", f'domainName.primaryLinkUrl[eq]:"{q(domain)}"') if domain else []
    if not found:
        found = c.find("companies", f'name[eq]:"{q(a["name"])}"')
    if found:
        return {"ok": True, "action": "existing", "id": found[0]["id"], "name": found[0].get("name")}
    body = clean({
        "name": a["name"],
        "domainName": link(domain),
        "address": clean({"addressCity": a.get("city"), "addressCountry": a.get("country")}),
    })
    rec = c.create("companies", "company", body)
    return {"ok": True, "action": "created", "id": rec.get("id"), "name": rec.get("name")}


def upsert_person(c, a):
    if not a.get("firstName"):
        raise TinaError("firstName is required")
    if a.get("id"):
        return {"ok": True, "action": "existing", "id": a["id"], "matched_by": "ledger"}
    email = a.get("email")
    phone, calling = normalize_vn_phone(a.get("phone"))
    found, matched_by = [], None
    if email:
        found, matched_by = c.find("people", f'emails.primaryEmail[eq]:"{q(email)}"'), "email"
    if not found and phone:
        found, matched_by = c.find("people", f'phones.primaryPhoneNumber[eq]:"{phone}"'), "phone"
    if not found and a.get("matchField") and a.get("matchValue"):
        found = c.find("people", f'{a["matchField"]}[eq]:"{q(a["matchValue"])}"')
        matched_by = a["matchField"]
    if found:
        rec = found[0]
        patch = {}
        if a.get("companyId") and not rec.get("companyId"):
            patch["companyId"] = a["companyId"]
        if a.get("jobTitle") and not rec.get("jobTitle"):
            patch["jobTitle"] = a["jobTitle"]
        for k, v in (a.get("extra") or {}).items():
            if v and not rec.get(k):
                patch[k] = v
        if patch:
            c.update("people", "person", rec["id"], patch)
        return {"ok": True, "action": "updated" if patch else "existing", "id": rec["id"],
                "matched_by": matched_by}
    body = clean({
        "name": {"firstName": a["firstName"], "lastName": a.get("lastName", "")},
        "emails": {"primaryEmail": email, "additionalEmails": []} if email else None,
        "phones": {"primaryPhoneNumber": phone, "primaryPhoneCallingCode": calling,
                   "primaryPhoneCountryCode": "VN"} if phone else None,
        "jobTitle": a.get("jobTitle"),
        "city": a.get("city"),
        "companyId": a.get("companyId"),
        **(a.get("extra") or {}),
    })
    rec = c.create("people", "person", body)
    return {"ok": True, "action": "created", "id": rec.get("id")}


def money(amount, currency):
    if amount in (None, ""):
        return None
    return {"amountMicros": int(round(float(amount) * 1_000_000)), "currencyCode": currency or "VND"}


def upsert_opportunity(c, a):
    if not a.get("name") and not a.get("id"):
        raise TinaError("name is required")
    fields = clean({
        "stage": a.get("stage"),
        "amount": money(a.get("amount"), a.get("currency")),
        "closeDate": a.get("closeDate"),
    })
    if a.get("id"):
        if fields:
            c.update("opportunities", "opportunity", a["id"], fields)
        return {"ok": True, "action": "updated" if fields else "existing", "id": a["id"]}
    body = clean({
        "name": a["name"],
        "companyId": a.get("companyId"),
        "pointOfContactId": a.get("pointOfContactId"),
        **fields,
    })
    rec = c.create("opportunities", "opportunity", body)
    return {"ok": True, "action": "created", "id": rec.get("id")}


TARGET_FIELDS = (("personId", "targetPersonId"), ("companyId", "targetCompanyId"),
                 ("opportunityId", "targetOpportunityId"))


def create_targets(c, plural, singular, parent_key, parent_id, a):
    targets = []
    for key, field in TARGET_FIELDS:
        if a.get(key):
            t = c.create(plural, singular, {parent_key: parent_id, field: a[key]})
            targets.append({field: a[key], "id": t.get("id")})
    return targets


def create_task(c, a):
    if not a.get("title"):
        raise TinaError("title is required")
    body = clean({
        "title": a["title"],
        "bodyV2": {"markdown": a["body"]} if a.get("body") else None,
        "dueAt": a.get("dueAt"),
        "status": a.get("status", "TODO"),
        "assigneeId": a.get("assigneeId"),
    })
    task = c.create("tasks", "task", body)
    targets = create_targets(c, "taskTargets", "taskTarget", "taskId", task["id"], a)
    return {"ok": True, "action": "created", "id": task.get("id"), "targets": targets}


def create_note(c, a):
    if not a.get("title"):
        raise TinaError("title is required")
    body = clean({
        "title": a["title"],
        "bodyV2": {"markdown": a["body"]} if a.get("body") else None,
    })
    note = c.create("notes", "note", body)
    targets = create_targets(c, "noteTargets", "noteTarget", "noteId", note["id"], a)
    return {"ok": True, "action": "created", "id": note.get("id"), "targets": targets}


def list_members(c):
    data = c.call("GET", "/workspaceMembers?limit=200").get("data", {}).get("workspaceMembers", [])
    out = []
    for m in data:
        name = m.get("name") or {}
        out.append({"id": m.get("id"), "name": f'{name.get("firstName", "")} {name.get("lastName", "")}'.strip(),
                    "email": m.get("userEmail")})
    return {"ok": True, "members": out}


def main():
    if len(sys.argv) < 3:
        raise TinaError(__doc__.strip().splitlines()[0])
    c = Client(sys.argv[1])
    cmd = sys.argv[2]
    if cmd == "check":
        n = len(c.call("GET", "/tasks?limit=1").get("data", {}).get("tasks", []))
        return {"ok": True, "rest": "reachable", "sample_tasks": n}
    if cmd == "get":
        plural = sys.argv[3]
        path = f"/{plural}?limit=20" + (f"&filter={quote(sys.argv[4])}" if len(sys.argv) > 4 else "")
        return {"ok": True, "data": c.call("GET", path).get("data", {}).get(plural, [])}
    if cmd == "members":
        return list_members(c)
    if cmd == "update":
        plural, rec_id, body = sys.argv[3], sys.argv[4], json.loads(sys.argv[5])
        rec = c.update(plural, SINGULAR.get(plural, plural.rstrip("s")), rec_id, body)
        return {"ok": True, "action": "updated", "id": rec.get("id", rec_id)}
    arg = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    handlers = {"upsert-company": upsert_company, "upsert-person": upsert_person,
                "upsert-opportunity": upsert_opportunity, "create-task": create_task,
                "create-note": create_note}
    if cmd not in handlers:
        raise TinaError(f"unknown command {cmd}")
    out = handlers[cmd](c, arg)
    if getattr(c, "dropped", None):
        out["dropped_fields"] = c.dropped
    return out


if __name__ == "__main__":
    try:
        result = main()
    except TinaError as e:
        print(json.dumps({"ok": False, "error": str(e), **e.extra}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False))
