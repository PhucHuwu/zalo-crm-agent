#!/usr/bin/env python3
"""Build the audience of a sales / customer-care campaign from config/state/customers.json.

Reads the filter from campaigns/<slug>/campaign.json -> "audience":
  {"segments": [...], "lifecycle_stages": [...], "intents": [...], "interests_any": [...],
   "tags_any": [...], "sales": [...], "app_ids": [...], "oa_ids": [...],
   "last_message_within_days": N, "last_message_older_than_days": N, "max_size": N}
Every key is optional; lists match if the customer has any of the values.

Always excluded: do_not_contact, spam, customers already in another *running* campaign.
Each row gets "zalo_window": whether a free-form OA message can still be sent
(customer wrote within the configured window), otherwise the campaign needs an approved
template message (ZNS) or a manual call by the sale.

Writes campaigns/<slug>/outputs/audience.json and audience.csv, prints a JSON summary.

Usage: python3 scripts/build_audience.py <slug> [--dry-run]
"""
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUSTOMERS = ROOT / "config" / "state" / "customers.json"
BUSINESS = ROOT / "config" / "business.json"


def read_json(p, default):
    return json.loads(p.read_text()) if p.is_file() else default


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=None)
    except ValueError:
        return None


def any_match(values, wanted):
    return not wanted or bool(set(values or []) & set(wanted))


def in_other_running_campaign(key, slug):
    for camp in (ROOT / "campaigns").glob("*/campaign.json"):
        if camp.parent.name == slug:
            continue
        c = read_json(camp, {})
        if c.get("status") != "running":
            continue
        aud = read_json(camp.parent / "outputs" / "audience.json", {})
        if key in {r["conversation_key"] for r in aud.get("members", [])}:
            return camp.parent.name
    return None


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: build_audience.py <slug>"}))
        sys.exit(1)
    slug = sys.argv[1]
    camp_dir = ROOT / "campaigns" / slug
    camp = read_json(camp_dir / "campaign.json", None)
    if camp is None:
        print(json.dumps({"ok": False, "error": f"Không có campaigns/{slug}/campaign.json"}, ensure_ascii=False))
        sys.exit(1)
    f = camp.get("audience", {})
    window_h = read_json(BUSINESS, {}).get("zalo", {}).get("free_message_window_hours", 48)
    now = datetime.now()
    members, excluded = [], {"do_not_contact": 0, "spam": 0, "other_campaign": 0}

    for key, c in read_json(CUSTOMERS, {}).items():
        if c.get("do_not_contact"):
            excluded["do_not_contact"] += 1
            continue
        if c.get("is_spam"):
            excluded["spam"] += 1
            continue
        if f.get("segments") and c.get("segment") not in f["segments"]:
            continue
        if f.get("lifecycle_stages") and c.get("lifecycle_stage") not in f["lifecycle_stages"]:
            continue
        if f.get("intents") and c.get("intent") not in f["intents"]:
            continue
        if not any_match(c.get("interests"), f.get("interests_any")):
            continue
        if not any_match(c.get("tags"), f.get("tags_any")):
            continue
        if f.get("sales") and c.get("sale") not in f["sales"]:
            continue
        if f.get("app_ids") and str(c.get("owner_app_id")) not in map(str, f["app_ids"]):
            continue
        if f.get("oa_ids") and str(c.get("oa_id")) not in map(str, f["oa_ids"]):
            continue
        last = parse_dt(c.get("last_customer_message_at"))
        if f.get("last_message_within_days") and (not last or now - last > timedelta(days=f["last_message_within_days"])):
            continue
        if f.get("last_message_older_than_days") and last and now - last < timedelta(days=f["last_message_older_than_days"]):
            continue
        other = in_other_running_campaign(key, slug)
        if other:
            excluded["other_campaign"] += 1
            continue
        members.append({
            "conversation_key": key, "zalo_user_id": c.get("zalo_user_id"), "oa_id": c.get("oa_id"),
            "name": c.get("name"), "phone": c.get("phone"), "company": c.get("company"),
            "sale": c.get("sale"), "owner_app_id": c.get("owner_app_id"), "segment": c.get("segment"),
            "lifecycle_stage": c.get("lifecycle_stage"), "interests": c.get("interests"),
            "summary": c.get("summary"), "next_best_action": c.get("next_best_action"),
            "last_customer_message_at": c.get("last_customer_message_at"),
            "zalo_window": bool(last and now - last <= timedelta(hours=window_h)),
            "crm_person_id": (c.get("crm") or {}).get("person_id"),
        })

    members.sort(key=lambda m: m.get("last_customer_message_at") or "", reverse=True)
    if f.get("max_size"):
        members = members[: int(f["max_size"])]
    by_sale = {}
    for m in members:
        by_sale[m.get("sale") or "?"] = by_sale.get(m.get("sale") or "?", 0) + 1
    summary = {"ok": True, "campaign": slug, "size": len(members), "by_sale": by_sale,
               "in_zalo_window": sum(m["zalo_window"] for m in members), "excluded": excluded}
    if "--dry-run" not in sys.argv:
        out = camp_dir / "outputs"
        out.mkdir(parents=True, exist_ok=True)
        (out / "audience.json").write_text(json.dumps({"built_at": now.isoformat(timespec="seconds"),
                                                       "filter": f, "members": members}, ensure_ascii=False, indent=2))
        cols = ["conversation_key", "name", "phone", "company", "sale", "segment", "lifecycle_stage",
                "last_customer_message_at", "zalo_window", "next_best_action"]
        with open(out / "audience.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(members)
        summary["files"] = [f"campaigns/{slug}/outputs/audience.json", f"campaigns/{slug}/outputs/audience.csv"]
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
