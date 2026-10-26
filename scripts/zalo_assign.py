#!/usr/bin/env python3
"""Assign (or reassign) a Zalo customer to a sale by setting the sale's OA tag.

Zalo has no per-application conversation scope; ownership in this workflow is the tag
applications[].sale_tag on the user (see scripts/zalo_fetch_daily.py). This script:
  - removes the other sale tags of the same OA from the user (one owner only),
  - adds the target sale's tag (Zalo creates the tag if it does not exist yet),
  - updates config/state/conversation_owners.json and, if present, config/state/customers.json.

Usage:
  python3 scripts/zalo_assign.py <conversation_key> <app_id> --confirm
  python3 scripts/zalo_assign.py check-tags            # sale tags present on each OA?
conversation_key = "<oa_id>:<zalo_user_id>". Uses the OA's reader application to call Zalo.
Prints one JSON line.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zalo_oa import ZaloApp, ZaloError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS = ROOT / "config" / "accounts.json"
OWNERS = ROOT / "config" / "state" / "conversation_owners.json"
CUSTOMERS = ROOT / "config" / "state" / "customers.json"


def read_json(p, default):
    return json.loads(p.read_text()) if p.is_file() else default


def write_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(p)


def active_apps(oa):
    return [{**a, "app_id": str(a["app_id"])} for a in oa.get("applications", []) if a.get("status", "active") == "active"]


def reader(oa):
    apps = active_apps(oa)
    first = str(oa.get("reader_app_id") or "")
    for a in sorted(apps, key=lambda a: a["app_id"] != first):
        return ZaloApp(a["app_id"])
    raise ZaloError("OA không có ứng dụng nào đang hoạt động.")


def check_tags(accounts):
    out = []
    for oa in accounts.get("oa_accounts", []):
        apps = active_apps(oa)
        existing = set(reader(oa).list_tags())
        out.append({"oa_id": str(oa.get("oa_id")), "oa_name": oa.get("oa_name"),
                    "apps": [{"app_id": a["app_id"], "sale": (a.get("sale") or {}).get("name"),
                              "sale_tag": a.get("sale_tag"),
                              "status": "ok" if a.get("sale_tag") in existing else
                              ("missing_in_config" if not a.get("sale_tag") else "not_created_on_oa")}
                             for a in apps]})
    return {"ok": True, "oas": out}


def assign(accounts, key, app_id):
    oa_id, _, user_id = key.partition(":")
    oa = next((o for o in accounts.get("oa_accounts", []) if str(o.get("oa_id")) == oa_id), None)
    if not oa or not user_id:
        raise ZaloError(f"Không tìm thấy OA {oa_id} trong config/accounts.json hoặc conversation_key sai.")
    apps = active_apps(oa)
    target = next((a for a in apps if a["app_id"] == str(app_id)), None)
    if not target:
        raise ZaloError(f"Ứng dụng {app_id} không thuộc OA {oa_id} hoặc không hoạt động.")
    if not target.get("sale_tag"):
        raise ZaloError(f"Ứng dụng {app_id} chưa có sale_tag.", code="missing_sale_tag")
    z = reader(oa)
    current = set(((z.profile(user_id).get("tags_and_notes_info") or {}).get("tag_names")) or [])
    removed = []
    for a in apps:
        if a["app_id"] != target["app_id"] and a.get("sale_tag") in current:
            z.untag_user(user_id, a["sale_tag"])
            removed.append(a["sale_tag"])
    if target["sale_tag"] not in current:
        z.tag_user(user_id, target["sale_tag"])
    sale = target.get("sale") or {}
    owners = read_json(OWNERS, {})
    owners[key] = {**owners.get(key, {}), "app_id": target["app_id"], "sale": sale.get("name"),
                   "assigned_by": "zalo_tag", "checked_at": int(time.time() * 1000)}
    write_json(OWNERS, owners)
    customers = read_json(CUSTOMERS, None)
    if customers and key in customers:
        customers[key].update(owner_app_id=target["app_id"], sale=sale.get("name"))
        write_json(CUSTOMERS, customers)
    return {"ok": True, "conversation_key": key, "app_id": target["app_id"], "sale": sale.get("name"),
            "tag": target["sale_tag"], "removed_tags": removed}


def main():
    accounts = read_json(ACCOUNTS, None)
    if not accounts:
        raise ZaloError("Chưa có config/accounts.json")
    args = [x for x in sys.argv[1:] if x != "--confirm"]
    if args[:1] == ["check-tags"]:
        return check_tags(accounts)
    if len(args) != 2:
        raise ZaloError("usage: zalo_assign.py <conversation_key> <app_id> --confirm | check-tags")
    if "--confirm" not in sys.argv:
        raise ZaloError("Gán khách cần --confirm sau khi người dùng đồng ý.")
    return assign(accounts, args[0], args[1])


if __name__ == "__main__":
    try:
        res = main()
    except ZaloError as e:
        print(json.dumps({"ok": False, "error": str(e), **e.extra}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(res, ensure_ascii=False))
