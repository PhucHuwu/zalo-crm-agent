#!/usr/bin/env python3
"""Assign (or reassign) Zalo customers to a sale by setting the sale's OA tag.

Zalo has no per-application conversation scope; ownership in this workflow is the tag
applications[].sale_tag on the user (see scripts/zalo_fetch_daily.py). Assigning:
  - removes the other sale tags of the same OA from the user (one owner only),
  - adds the target sale's tag (Zalo creates the tag if it does not exist yet),
  - updates config/state/conversation_owners.json and config/state/customers.json,
  - on TinaCRM (if connected): moves the workflow's open tasks of that customer to the sale
    (ids from config/state/crm_ledger.json) and sets the owner_sale field if mapped.

Usage (used by the assistant when the manager asks, e.g. "Giao chị Hoa cho Minh"):
  python3 scripts/zalo_assign.py unassigned               # customers without (or with conflicting) sale tags
  python3 scripts/zalo_assign.py sales                    # sales that can receive customers
  python3 scripts/zalo_assign.py find "<tên/SĐT/công ty>"  # resolve a customer to its conversation_key
  python3 scripts/zalo_assign.py to "<sale>" <conversation_key> [<conversation_key> ...] --dry-run
  python3 scripts/zalo_assign.py to "<sale>" <conversation_key> [<conversation_key> ...] --confirm [--no-crm]
  python3 scripts/zalo_assign.py <conversation_key> <app_id> --confirm      # older single form
  python3 scripts/zalo_assign.py check-tags               # sale tags present on each OA?
<sale> = app_id, sale name (or given name, e.g. "Minh"), or tag name; must match exactly one sale.
conversation_key = "<oa_id>:<zalo_user_id>". Uses the OA's reader application to call Zalo.
Prints one JSON line.
"""
import json
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zalo_oa import ZaloApp, ZaloError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS = ROOT / "config" / "accounts.json"
BUSINESS = ROOT / "config" / "business.json"
STATE = ROOT / "config" / "state"
OWNERS = STATE / "conversation_owners.json"
CUSTOMERS = STATE / "customers.json"
LEDGER = STATE / "crm_ledger.json"
EXTRACTIONS = ROOT / "outputs" / "01_daily_extractions"


def read_json(p, default):
    return json.loads(p.read_text()) if p.is_file() else default


def write_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(p)


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
    return " ".join("".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower().split())


def active_apps(oa):
    return [{**a, "app_id": str(a["app_id"])} for a in oa.get("applications", []) if a.get("status", "active") == "active"]


def reader(oa):
    apps = active_apps(oa)
    first = str(oa.get("reader_app_id") or "")
    for a in sorted(apps, key=lambda a: a["app_id"] != first):
        return ZaloApp(a["app_id"])
    raise ZaloError("OA không có ứng dụng nào đang hoạt động.")


def oa_of(accounts, key):
    oa_id, _, user_id = key.partition(":")
    oa = next((o for o in accounts.get("oa_accounts", []) if str(o.get("oa_id")) == oa_id), None)
    if not oa or not user_id:
        raise ZaloError(f"Không tìm thấy OA {oa_id} trong config/accounts.json hoặc conversation_key sai.",
                        code="bad_key")
    return oa, user_id


def all_sales(accounts):
    return [{"oa_id": str(oa.get("oa_id")), "oa_name": oa.get("oa_name"), "app_id": a["app_id"],
             "label": a.get("label"), "sale": (a.get("sale") or {}).get("name"), "sale_tag": a.get("sale_tag"),
             "crm_member_id": (a.get("sale") or {}).get("crm_member_id")}
            for oa in accounts.get("oa_accounts", []) for a in active_apps(oa)]


def resolve_sale(accounts, text, oa_id=None):
    """Match an app_id, full sale name, given name, tag or label. Exactly one match or an error."""
    sales = [s for s in all_sales(accounts) if not oa_id or s["oa_id"] == oa_id]
    q = norm(text)
    tiers = [
        lambda s: s["app_id"] == str(text).strip(),
        lambda s: q in (norm(s["sale"]), norm(s["sale_tag"]), norm(s["label"])),
        lambda s: norm(s["sale"]).split()[-1:] == [q] or norm(s["sale_tag"]).endswith(" " + q),
        lambda s: q and (q in norm(s["sale"]) or q in norm(s["label"])),
    ]
    for match in tiers:
        hits = [s for s in sales if match(s)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise ZaloError(f"“{text}” khớp nhiều sale, cần chọn rõ.", code="ambiguous_sale",
                            candidates=[{k: h[k] for k in ("app_id", "sale", "sale_tag", "oa_name")} for h in hits])
    raise ZaloError(f"Không tìm thấy sale “{text}”.", code="sale_not_found",
                    sales=[{k: s[k] for k in ("app_id", "sale", "sale_tag", "oa_name")} for s in sales])


def directory():
    """conversation_key -> what we know about the customer (index first, then recent conversation files)."""
    out = {k: dict(v) for k, v in read_json(CUSTOMERS, {}).items()}
    days = sorted((d for d in EXTRACTIONS.glob("*") if d.is_dir()), reverse=True)[:14] if EXTRACTIONS.is_dir() else []
    for d in days:
        for f in (d / "conversations").glob("*.json"):
            try:
                c = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            entry = out.setdefault(c["conversation_key"], {})
            entry.setdefault("name", c.get("display_name"))
            entry.setdefault("display_name", c.get("display_name"))
            if not entry.get("last_customer_message_at"):
                times = [m.get("time") for m in c.get("new_messages", []) if m.get("from") == "customer"]
                if times:
                    entry["last_customer_message_ms"] = max(times)
    return out


def brief(key, info, owner=None):
    return {"conversation_key": key, "name": info.get("name") or info.get("display_name"),
            "company": info.get("company"), "phone": info.get("phone"),
            "sale": (owner or {}).get("sale") if owner is not None else info.get("sale"),
            "summary": info.get("summary"), "interests": info.get("interests"),
            "next_best_action": info.get("next_best_action"),
            "last_customer_message_at": info.get("last_customer_message_at") or info.get("last_customer_message_ms"),
            "do_not_contact": info.get("do_not_contact") or None, "is_spam": info.get("is_spam") or None}


def list_unassigned():
    owners, info = read_json(OWNERS, {}), directory()
    rows = []
    for key, o in owners.items():
        if o.get("app_id"):
            continue
        row = brief(key, info.get(key, {}), o)
        row["reason"] = "conflict" if o.get("assigned_by") == "conflict" else "no_tag"
        if not row["is_spam"]:
            rows.append(row)
    rows.sort(key=lambda r: str(r["last_customer_message_at"] or ""), reverse=True)
    return {"ok": True, "count": len(rows), "customers": rows}


def find(text):
    q = norm(text)
    digits = "".join(ch for ch in text if ch.isdigit())
    owners, hits = read_json(OWNERS, {}), []
    for key, c in directory().items():
        hay = " | ".join(norm(c.get(k)) for k in ("name", "display_name", "company"))
        phone = "".join(ch for ch in str(c.get("phone") or "") if ch.isdigit())
        if (q and q in hay) or (len(digits) >= 6 and digits[-9:] in phone) or text.strip() == key:
            hits.append(brief(key, c, owners.get(key, {"sale": c.get("sale")})))
    return {"ok": True, "count": len(hits), "customers": hits[:20]}


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


def crm_reassign(key, target):
    """Move the workflow's open CRM tasks of this customer to the new sale; set owner_sale if mapped."""
    business = read_json(BUSINESS, {})
    crm = business.get("crm", {})
    entry = read_json(LEDGER, {}).get(key)
    if not crm.get("base_url"):
        return {"status": "skipped", "reason": "crm_not_connected"}
    if not entry:
        return {"status": "skipped", "reason": "not_synced_yet"}
    import tinacrm_rest as tr
    try:
        c = tr.Client(crm["base_url"])
    except tr.TinaError as e:
        return {"status": "failed", "error": str(e)}
    out = {"status": "ok", "tasks_moved": 0, "tasks_skipped_done": 0}
    try:
        field = (crm.get("field_mapping") or {}).get("owner_sale")
        if field and entry.get("person_id") and target["sale"]:
            c.update("people", "person", entry["person_id"], {field: target["sale"]})
            out["person_owner_sale"] = target["sale"]
        member = target.get("crm_member_id")
        if not member:
            out["tasks_note"] = "Sale chưa có crm_member_id; task giữ nguyên người được giao."
            return out
        for tid in entry.get("task_ids", []):
            try:
                task = c.call("GET", f"/tasks/{tid}").get("data", {}).get("task") or {}
            except tr.TinaError:
                continue  # deleted on CRM
            if task.get("status") == "DONE" or task.get("assigneeId") == member:
                out["tasks_skipped_done"] += task.get("status") == "DONE"
                continue
            c.update("tasks", "task", tid, {"assigneeId": member})
            out["tasks_moved"] += 1
        if not entry.get("task_ids") and entry.get("pushed"):
            out["tasks_note"] = "Task tạo trước khi có lưu ID; đổi người được giao trên TinaCRM nếu cần."
    except tr.TinaError as e:
        out.update(status="failed", error=str(e), **e.extra)
    return out


def assign_one(accounts, key, target, dry_run=False, crm=True):
    oa, user_id = oa_of(accounts, key)
    if str(oa.get("oa_id")) != target["oa_id"]:
        raise ZaloError(f"Sale {target['sale']} thuộc OA khác với khách {key}.", code="wrong_oa")
    if not target.get("sale_tag"):
        raise ZaloError(f"Ứng dụng {target['app_id']} chưa có sale_tag.", code="missing_sale_tag")
    apps = active_apps(oa)
    z = reader(oa)
    current = set(((z.profile(user_id).get("tags_and_notes_info") or {}).get("tag_names")) or [])
    remove = [a["sale_tag"] for a in apps if a["app_id"] != target["app_id"] and a.get("sale_tag") in current]
    add = target["sale_tag"] not in current
    res = {"ok": True, "conversation_key": key, "app_id": target["app_id"], "sale": target["sale"],
           "tag": target["sale_tag"], "removed_tags": remove, "already_assigned": not add and not remove}
    if dry_run:
        return {**res, "dry_run": True}
    for tag in remove:
        z.untag_user(user_id, tag)
    if add:
        z.tag_user(user_id, target["sale_tag"])
    owners = read_json(OWNERS, {})
    owners[key] = {**owners.get(key, {}), "app_id": target["app_id"], "sale": target["sale"],
                   "assigned_by": "zalo_tag", "checked_at": int(time.time() * 1000)}
    write_json(OWNERS, owners)
    customers = read_json(CUSTOMERS, None)
    if customers and key in customers:
        customers[key].update(owner_app_id=target["app_id"], sale=target["sale"])
        write_json(CUSTOMERS, customers)
    if crm:
        res["crm"] = crm_reassign(key, target)
    return res


def assign_many(accounts, sale_text, keys, dry_run, crm):
    if not keys:
        raise ZaloError("Thiếu conversation_key.")
    oa_ids = {k.partition(":")[0] for k in keys}
    target = resolve_sale(accounts, sale_text, next(iter(oa_ids)) if len(oa_ids) == 1 else None)
    results = []
    for key in keys:
        try:
            results.append(assign_one(accounts, key, target, dry_run, crm))
        except ZaloError as e:
            results.append({"ok": False, "conversation_key": key, "error": str(e), **e.extra})
    return {"ok": all(r["ok"] for r in results), "dry_run": dry_run, "sale": target["sale"],
            "app_id": target["app_id"], "tag": target["sale_tag"],
            "assigned": sum(1 for r in results if r["ok"] and not dry_run),
            "failed": sum(1 for r in results if not r["ok"]), "results": results}


def main():
    accounts = read_json(ACCOUNTS, None)
    if not accounts:
        raise ZaloError("Chưa có config/accounts.json")
    flags = {x for x in sys.argv[1:] if x.startswith("--")}
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    dry_run, confirm, crm = "--dry-run" in flags, "--confirm" in flags, "--no-crm" not in flags
    cmd = args[0] if args else ""
    if cmd == "check-tags":
        return check_tags(accounts)
    if cmd == "unassigned":
        return list_unassigned()
    if cmd == "sales":
        return {"ok": True, "sales": all_sales(accounts)}
    if cmd == "find" and len(args) == 2:
        return find(args[1])
    if cmd == "to" and len(args) >= 3:
        sale_text, keys = args[1], args[2:]
    elif len(args) == 2 and ":" in args[0]:
        sale_text, keys = args[1], [args[0]]
    else:
        raise ZaloError("usage: zalo_assign.py unassigned | sales | find <text> | check-tags | "
                        "to <sale> <conversation_key>... --dry-run|--confirm [--no-crm]")
    if not (dry_run or confirm):
        raise ZaloError("Gán khách cần --dry-run để xem trước, hoặc --confirm sau khi người dùng đồng ý.")
    res = assign_many(accounts, sale_text, keys, dry_run, crm)
    if len(keys) == 1 and cmd != "to":  # older single form keeps its flat output
        return res["results"][0]
    return res


if __name__ == "__main__":
    try:
        res = main()
    except ZaloError as e:
        print(json.dumps({"ok": False, "error": str(e), **e.extra}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if res.get("ok") else 2)
