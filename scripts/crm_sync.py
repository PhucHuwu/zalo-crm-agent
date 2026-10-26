#!/usr/bin/env python3
"""Push the agent's conversation analyses for one day into TinaCRM.

Input:  outputs/01_daily_extractions/<date>/analysis/*.json   (schema: rules/data_schemas.md §2)
State:  config/state/crm_ledger.json      conversation_key -> CRM ids + pushed task/note hashes
        config/state/customers.json       local customer index used for campaigns (§4)
Output: outputs/02_crm_sync/<date>.json   per-conversation result, plus one JSON summary line

Order per conversation: company -> person -> opportunity -> notes -> tasks.
Idempotent: re-running the same day never creates the same note/task twice (content hash),
and a person/opportunity already in the ledger is updated instead of created.
Skipped (only indexed locally): flags.is_spam, or confidence below sync.min_confidence.
flags.needs_human_review: synced only with --include-review.
--index-only: no CRM calls; only refresh customers.json (e.g. before TinaCRM is connected).

Usage:
  python3 scripts/crm_sync.py --date YYYY-MM-DD [--dry-run | --index-only] [--only <conversation_key>] [--include-review]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUSINESS = ROOT / "config" / "business.json"
ACCOUNTS = ROOT / "config" / "accounts.json"
STATE = ROOT / "config" / "state"
LEDGER = STATE / "crm_ledger.json"
CUSTOMERS = STATE / "customers.json"
TINA = ROOT / "scripts" / "tinacrm_rest.py"


def read_json(p, default):
    return json.loads(p.read_text()) if p.is_file() else default


def write_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(p)


def digest(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


class Tina:
    def __init__(self, base_url, dry_run):
        self.base, self.dry = base_url, dry_run

    def run(self, cmd, payload):
        if self.dry:
            return {"ok": True, "action": "dry_run", "id": f"dry-{cmd}-{digest(json.dumps(payload, sort_keys=True))}"}
        res = subprocess.run([sys.executable, str(TINA), self.base, cmd, json.dumps(payload, ensure_ascii=False)],
                             capture_output=True, text=True)
        try:
            out = json.loads(res.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            out = {"ok": False, "error": res.stderr.strip()[:300] or "no output"}
        if not out.get("ok"):
            raise RuntimeError(f"{cmd}: {out.get('error')} {out.get('detail', '')}".strip())
        return out


def split_name(full):
    parts = (full or "").strip().split()
    if not parts:
        return "Khách Zalo", ""
    if len(parts) == 1:
        return parts[0], ""
    # Vietnamese order: family name first, given name last. TinaCRM shows "firstName lastName".
    return parts[-1], " ".join(parts[:-1])


def due_iso(task, tz_offset):
    if task.get("due_at"):
        return task["due_at"]
    days = int(task.get("due_in_days", 1))
    d = (datetime.now() + timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0)
    return d.strftime("%Y-%m-%dT%H:%M:%S") + tz_offset


def sale_member_id(app_id, accounts):
    for oa in accounts.get("oa_accounts", []):
        for app in oa.get("applications", []):
            if str(app["app_id"]) == str(app_id):
                return (app.get("sale") or {}).get("crm_member_id")
    return None


def sync_one(t, a, ledger, cfg, accounts):
    key = a["conversation_key"]
    entry = ledger.setdefault(key, {"pushed": []})
    mapping = cfg.get("field_mapping", {})
    stage_map = cfg.get("stage_mapping", {})
    owner_app = (a.get("owner") or {}).get("app_id")
    # No owner tag yet: give tasks to the manager so the customer is not dropped.
    assignee = sale_member_id(owner_app, accounts) or (accounts.get("assignment") or {}).get("manager_crm_member_id")
    out = {"conversation_key": key, "actions": []}

    company_id = entry.get("company_id")
    comp = a.get("company") or {}
    if comp.get("name") and not company_id:
        r = t.run("upsert-company", {"name": comp["name"], "domain": comp.get("domain"),
                                     "city": comp.get("city"), "country": comp.get("country", "Vietnam")})
        company_id = entry["company_id"] = r["id"]
        out["actions"].append({"company": r["action"], "id": r["id"]})

    p = a.get("person") or {}
    first, last = (p.get("first_name"), p.get("last_name") or "") if p.get("first_name") else split_name(
        p.get("full_name") or a.get("display_name"))
    extra = {}
    for local, crm_field in (("zalo_user_id", mapping.get("zalo_user_id")), ("oa_id", mapping.get("zalo_oa_id")),
                             ("sale", mapping.get("owner_sale")), ("segment", mapping.get("segment"))):
        if not crm_field:
            continue
        value = {"zalo_user_id": a.get("zalo_user_id"), "oa_id": a.get("oa_id"),
                 "sale": ((a.get("owner") or {}).get("sale") or {}).get("name"),
                 "segment": (a.get("care") or {}).get("segment")}[local]
        if value:
            extra[crm_field] = value
    payload = {"firstName": first, "lastName": last, "email": p.get("email"), "phone": p.get("phone"),
               "jobTitle": p.get("job_title"), "city": p.get("city"), "companyId": company_id,
               "id": entry.get("person_id"), "extra": extra}
    if mapping.get("zalo_user_id"):
        payload.update(matchField=mapping["zalo_user_id"], matchValue=a.get("zalo_user_id"))
    r = t.run("upsert-person", payload)
    person_id = entry["person_id"] = r["id"]
    out["actions"].append({"person": r["action"], "id": person_id})

    opp = a.get("opportunity") or {}
    opp_id = entry.get("opportunity_id")
    if opp.get("action") in ("create", "update") and opp.get("confidence", 0) >= cfg.get("min_confidence", 0.6):
        stage = stage_map.get(opp.get("stage")) if opp.get("stage") else None
        body = {"name": opp.get("name") or f"{first} {last} – {opp.get('product') or 'Zalo'}".strip(),
                "amount": opp.get("amount"), "currency": opp.get("currency", "VND"), "stage": stage,
                "closeDate": opp.get("close_date"), "companyId": company_id, "pointOfContactId": person_id,
                "id": opp_id}
        r = t.run("upsert-opportunity", body)
        opp_id = entry["opportunity_id"] = r["id"]
        out["actions"].append({"opportunity": r["action"], "id": opp_id})

    targets = {"personId": person_id, "companyId": company_id, "opportunityId": opp_id}
    targets = {k: v for k, v in targets.items() if v}
    for n in a.get("notes") or []:
        h = digest("note", n.get("title"), n.get("body"))
        if h in entry["pushed"]:
            continue
        r = t.run("create-note", {"title": n["title"], "body": n.get("body"), **targets})
        entry["pushed"].append(h)
        out["actions"].append({"note": r["action"], "id": r["id"]})
    for tk in a.get("tasks") or []:
        h = digest("task", tk.get("title"), tk.get("due_at") or tk.get("due_in_days"))
        if h in entry["pushed"]:
            continue
        body = tk.get("body") or ""
        if tk.get("priority"):
            body = f"**Ưu tiên:** {tk['priority']}\n\n{body}"
        r = t.run("create-task", {"title": tk["title"], "body": body, "dueAt": due_iso(tk, cfg.get("tz_offset", "+07:00")),
                                  "assigneeId": assignee, **targets})
        entry["pushed"].append(h)
        out["actions"].append({"task": r["action"], "id": r["id"]})
    entry["last_synced"] = datetime.now().isoformat(timespec="seconds")
    return out


def update_customer_index(customers, a, ledger_entry):
    key = a["conversation_key"]
    c = customers.setdefault(key, {"first_seen": a.get("analyzed_at")})
    sig, care, p = a.get("signals") or {}, a.get("care") or {}, a.get("person") or {}
    c.update({
        "conversation_key": key, "oa_id": a.get("oa_id"), "zalo_user_id": a.get("zalo_user_id"),
        "display_name": a.get("display_name"), "name": p.get("full_name") or a.get("display_name"),
        "phone": p.get("phone") or c.get("phone"), "email": p.get("email") or c.get("email"),
        "company": (a.get("company") or {}).get("name") or c.get("company"),
        "owner_app_id": (a.get("owner") or {}).get("app_id"),
        "sale": ((a.get("owner") or {}).get("sale") or {}).get("name"),
        "intent": sig.get("intent"), "lifecycle_stage": sig.get("lifecycle_stage"),
        "sentiment": sig.get("sentiment"),
        "interests": sorted(set(c.get("interests", [])) | set(sig.get("interests", []))),
        "objections": sig.get("objections", []), "tags": sorted(set(c.get("tags", [])) | set(sig.get("tags", []))),
        "segment": care.get("segment"), "next_best_action": care.get("next_best_action"),
        "last_customer_message_at": a.get("last_customer_message_at") or c.get("last_customer_message_at"),
        "last_analyzed": a.get("analyzed_at"), "summary": a.get("summary"),
        "do_not_contact": bool((a.get("flags") or {}).get("do_not_contact")) or c.get("do_not_contact", False),
        "is_spam": bool((a.get("flags") or {}).get("is_spam")),
        "crm": {k: ledger_entry.get(k) for k in ("person_id", "company_id", "opportunity_id")} if ledger_entry else {},
    })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--include-review", action="store_true")
    ap.add_argument("--index-only", action="store_true")
    args = ap.parse_args()

    business = read_json(BUSINESS, {})
    crm = business.get("crm", {})
    if not crm.get("base_url") and not (args.dry_run or args.index_only):
        print(json.dumps({"ok": False, "error": "Chưa có crm.base_url trong config/business.json"}, ensure_ascii=False))
        sys.exit(1)
    cfg = {**crm, **business.get("sync", {})}
    accounts = read_json(ACCOUNTS, {})
    analysis_dir = ROOT / "outputs" / "01_daily_extractions" / args.date / "analysis"
    files = sorted(analysis_dir.glob("*.json"))
    ledger = read_json(LEDGER, {})
    customers = read_json(CUSTOMERS, {})
    t = Tina(crm.get("base_url"), args.dry_run)
    if not analysis_dir.is_dir():
        print(json.dumps({"ok": False, "error": f"Chưa có thư mục phân tích {analysis_dir.relative_to(ROOT)}"},
                         ensure_ascii=False))
        sys.exit(1)
    report = {"ok": True, "date": args.date, "dry_run": args.dry_run, "index_only": args.index_only, "results": [],
              "counts": {"synced": 0, "skipped": 0, "review": 0, "failed": 0, "indexed": 0}}

    for f in files:
        a = json.loads(f.read_text())
        key = a.get("conversation_key")
        if args.only and key != args.only:
            continue
        flags = a.get("flags") or {}
        if flags.get("is_spam") or (a.get("confidence", 1) < cfg.get("min_confidence", 0.6) and not flags.get("needs_human_review")):
            update_customer_index(customers, a, ledger.get(key))
            report["results"].append({"conversation_key": key, "status": "skipped",
                                      "reason": "spam" if flags.get("is_spam") else "low_confidence"})
            report["counts"]["skipped"] += 1
            continue
        if args.index_only:
            update_customer_index(customers, a, ledger.get(key))
            report["results"].append({"conversation_key": key, "status": "indexed"})
            report["counts"]["indexed"] += 1
            continue
        if flags.get("needs_human_review") and not args.include_review:
            update_customer_index(customers, a, ledger.get(key))
            report["results"].append({"conversation_key": key, "status": "needs_review",
                                      "reason": flags.get("review_reason")})
            report["counts"]["review"] += 1
            continue
        try:
            res = sync_one(t, a, ledger, cfg, accounts)
            res["status"] = "synced"
            report["counts"]["synced"] += 1
        except RuntimeError as e:
            res = {"conversation_key": key, "status": "failed", "error": str(e)}
            report["counts"]["failed"] += 1
            report["ok"] = False
        report["results"].append(res)
        update_customer_index(customers, a, ledger.get(key))
        if not args.dry_run:
            write_json(LEDGER, ledger)  # save after every conversation so a crash loses nothing

    if args.index_only:
        write_json(CUSTOMERS, customers)
    elif not args.dry_run:
        write_json(CUSTOMERS, customers)
        write_json(ROOT / "outputs" / "02_crm_sync" / f"{args.date}.json", report)
    print(json.dumps({k: report[k] for k in ("ok", "date", "dry_run", "index_only", "counts")} |
                     {"failed": [r for r in report["results"] if r["status"] == "failed"],
                      "needs_review": [r["conversation_key"] for r in report["results"] if r["status"] == "needs_review"]},
                     ensure_ascii=False))
    sys.exit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
