#!/usr/bin/env python3
"""Daily pull of Zalo OA conversation history, assigned to sales by Zalo tag.

Zalo facts this script is built on (developers.zalo.me, Official Account docs):
  - listrecentchat / conversation have no application or staff filter: every application
    authorized on an OA reads the same conversations. So each OA is read ONCE per run,
    through its first working application (oa_accounts[].reader_app_id, else any active app).
  - Ownership comes from OA tags: each application/sale has a "sale_tag" (e.g. "Sale: Minh").
    The tag is set by the sale in OA Manager or by scripts/zalo_assign.py, and is read back
    from /v3.0/oa/user/detail -> tags_and_notes_info.tag_names.

For each OA:
  1. Page through listrecentchat (newest first) until chats are older than the OA cursor.
  2. For every user with new messages, page through the conversation (new messages plus up to
     CONTEXT_MESSAGES older ones as context) and read the user profile (tags).
  3. Owner = the application whose sale_tag the user carries. No tag -> owner null
     ("unassigned" queue for the manager). Several sale tags -> owner null + owner_conflict.
  4. Write one file per conversation to outputs/01_daily_extractions/<date>/conversations/
     and an index.json the analyst works from.
  5. Advance the OA cursor in config/state/zalo_cursors.json only after the OA finished cleanly.

--app <app_id>: only that sale's customers, found with /v3.0/oa/user/getlist?tag_name=<sale_tag>
and last_interaction_period; window = --since-hours (default fetch.first_run_hours), ignores and
does not move the OA cursor.

Usage:
  python3 scripts/zalo_fetch_daily.py [--date YYYY-MM-DD] [--oa <oa_id>] [--app <app_id>]
                                      [--since-hours N] [--fixture tests/fixtures/zalo_sample.json]
--since-hours: window when there is no cursor yet (or with --app), default fetch.first_run_hours (48).
--fixture: read chats from a local JSON file instead of Zalo (for testing the pipeline).

Prints one JSON summary line.
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zalo_oa import ZaloApp, ZaloError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS = ROOT / "config" / "accounts.json"
STATE_DIR = ROOT / "config" / "state"
CURSORS = STATE_DIR / "zalo_cursors.json"
OWNERS = STATE_DIR / "conversation_owners.json"
OUT_ROOT = ROOT / "outputs" / "01_daily_extractions"
CONTEXT_MESSAGES = 20
MAX_RECENT_PAGES = 100
MAX_CONV_PAGES = 30
MAX_TAG_PAGES = 200


def read_json(path, default):
    return json.loads(path.read_text()) if path.is_file() else default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(path)


def peer_of(msg, oa_id):
    """User id of the customer in a message (src 1 = user -> OA, 0 = OA -> user)."""
    if str(msg.get("src")) == "1":
        return str(msg.get("from_id")), msg.get("from_display_name"), msg.get("from_avatar")
    if oa_id and str(msg.get("from_id")) != str(oa_id):
        return str(msg.get("from_id")), msg.get("from_display_name"), msg.get("from_avatar")
    return str(msg.get("to_id")), msg.get("to_display_name"), msg.get("to_avatar")


def slim(msg):
    out = {
        "message_id": msg.get("message_id"),
        "time": msg.get("time"),
        "time_iso": datetime.fromtimestamp(int(msg.get("time", 0)) / 1000).astimezone().isoformat(timespec="seconds"),
        "from": "customer" if str(msg.get("src")) == "1" else "oa",
        "type": msg.get("type"),
        "text": msg.get("message"),
    }
    for k in ("url", "thumb", "description", "links", "location"):
        if msg.get(k):
            out[k] = msg[k]
    return out


def tag_period(since_ms):
    """last_interaction_period covering since_ms .. today, in Zalo's 'YYYY_MM_DD:YYYY_MM_DD' form."""
    start = datetime.fromtimestamp(since_ms / 1000).strftime("%Y_%m_%d")
    return f"{start}:{datetime.now().strftime('%Y_%m_%d')}"


class FixtureSource:
    """Same interface as ZaloApp, backed by a JSON file:
    {"oa_id", "oa_name", "users": {"<user_id>": {"tag_names": [...]}}, "messages": [...]}.

    A message may use "minutes_ago" instead of "time" so the sample stays inside the fetch window.
    """

    def __init__(self, path):
        data = json.loads(Path(path).read_text())
        self.oa_id = str(data["oa_id"])
        self.oa_name = data.get("oa_name")
        self.users = data.get("users", {})
        now_ms = int(time.time() * 1000)
        for m in data["messages"]:
            if "time" not in m:
                m["time"] = now_ms - int(m.pop("minutes_ago")) * 60_000
        self.messages = sorted(data["messages"], key=lambda m: -int(m["time"]))

    def oa_info(self):
        return {"oa_id": self.oa_id, "name": self.oa_name}

    def recent_chats(self, offset=0, count=10):
        latest = {}
        for m in self.messages:
            latest.setdefault(peer_of(m, self.oa_id)[0], m)
        return list(latest.values())[offset:offset + count]

    def conversation(self, user_id, offset=0, count=10):
        conv = [m for m in self.messages if peer_of(m, self.oa_id)[0] == str(user_id)]
        return conv[offset:offset + count]

    def profile(self, user_id):
        tags = self.users.get(str(user_id), {}).get("tag_names", [])
        return {"tags_and_notes_info": {"tag_names": tags, "notes": []}}

    def users_by_tag(self, tag_name, period=None, offset=0, count=50):
        ids = [u for u, v in self.users.items() if tag_name in v.get("tag_names", [])]
        return ids[offset:offset + count], len(ids)


def tags_of(profile):
    return list(((profile or {}).get("tags_and_notes_info") or {}).get("tag_names") or [])


def resolve_owner(tags, apps):
    """apps: active applications of this OA. Returns (owner|None, assignment info)."""
    hits = [a for a in apps if a.get("sale_tag") and a["sale_tag"] in tags]
    if len(hits) == 1:
        a = hits[0]
        return {"app_id": a["app_id"], "sale": a.get("sale", {})}, {"by": "zalo_tag", "tag": a["sale_tag"]}
    if len(hits) > 1:
        return None, {"by": "conflict", "tags": [a["sale_tag"] for a in hits]}
    return None, {"by": "none"}


def collect_user(src, uid, since_ms):
    new, context = [], []
    for page in range(MAX_CONV_PAGES):
        msgs = src.conversation(uid, page * 10, 10)
        if not msgs:
            break
        for m in msgs:
            (new if int(m.get("time", 0)) > since_ms else context).append(m)
        if len(context) >= CONTEXT_MESSAGES:
            break
    return new, context


def write_conversation(src, oa_id, uid, meta, new, context, apps, date_dir, owners, run_ms):
    try:
        profile = src.profile(uid) or {}
    except ZaloError:
        profile = {}
    tags = tags_of(profile)
    owner, assignment = resolve_owner(tags, apps)
    key = f"{oa_id}:{uid}"
    prev = owners.get(key)
    owners[key] = {"app_id": owner["app_id"] if owner else None,
                   "sale": (owner or {}).get("sale", {}).get("name"),
                   "assigned_by": assignment["by"], "checked_at": run_ms,
                   "first_seen": (prev or {}).get("first_seen", run_ms)}
    conv_path = date_dir / "conversations" / f"{oa_id}_{uid}.json"
    existing = read_json(conv_path, None)
    new_slim = [slim(m) for m in sorted(new, key=lambda m: int(m["time"]))]
    if existing:  # second run the same day: append only unseen messages
        ids = {m["message_id"] for m in existing["new_messages"]}
        new_slim = existing["new_messages"] + [m for m in new_slim if m["message_id"] not in ids]
        context_slim = existing["context_messages"]
    else:
        context_slim = [slim(m) for m in sorted(context, key=lambda m: int(m["time"]))[-CONTEXT_MESSAGES:]]
    doc = {
        "conversation_key": key,
        "oa_id": oa_id,
        "zalo_user_id": uid,
        "display_name": profile.get("display_name") or meta.get("display_name") or (existing or {}).get("display_name"),
        "avatar": profile.get("avatar") or meta.get("avatar"),
        "zalo_profile": {k: profile.get(k) for k in ("user_gender", "user_id_by_app", "shared_info",
                                                      "tags_and_notes_info", "user_is_follower") if k in profile},
        "owner": owner,
        "assignment": assignment,
        "owner_changed": bool(prev and prev.get("app_id") != (owner or {}).get("app_id")),
        "context_messages": context_slim,
        "new_messages": new_slim,
    }
    write_json(conv_path, doc)
    return {"conversation_key": key, "file": str(conv_path.relative_to(ROOT)),
            "owner_app": (owner or {}).get("app_id"), "sale": (owner or {}).get("sale", {}).get("name"),
            "assignment": assignment["by"], "new_messages": len(new)}


def fetch_oa(src, oa_id, apps, since_ms, date_dir, owners, run_ms):
    users, max_ms = {}, since_ms
    for page in range(MAX_RECENT_PAGES):
        chats = src.recent_chats(page * 10, 10)
        if not chats:
            break
        for m in chats:
            if int(m.get("time", 0)) <= since_ms:
                continue
            uid, name, avatar = peer_of(m, oa_id)
            users.setdefault(uid, {"display_name": name, "avatar": avatar})
        if int(chats[-1].get("time", 0)) <= since_ms:
            break
    results = []
    for uid, meta in users.items():
        new, context = collect_user(src, uid, since_ms)
        if not new:
            continue
        max_ms = max(max_ms, max(int(m.get("time", 0)) for m in new))
        results.append(write_conversation(src, oa_id, uid, meta, new, context, apps, date_dir, owners, run_ms))
    return results, max_ms


def fetch_one_sale(src, oa_id, app, apps, since_ms, date_dir, owners, run_ms):
    if not app.get("sale_tag"):
        raise ZaloError(f"Ứng dụng {app['app_id']} chưa có sale_tag trong config/accounts.json.", code="missing_sale_tag")
    ids, period = [], tag_period(since_ms)
    for page in range(MAX_TAG_PAGES):
        batch, total = src.users_by_tag(app["sale_tag"], period, page * 50, 50)
        ids += batch
        if not batch or len(ids) >= total:
            break
    results = []
    for uid in ids:
        new, context = collect_user(src, uid, since_ms)
        if new:
            results.append(write_conversation(src, oa_id, uid, {}, new, context, apps, date_dir, owners, run_ms))
    return results


def reader_candidates(oa, apps, only_app):
    if only_app:
        return [a for a in apps if a["app_id"] == only_app]
    first = str(oa.get("reader_app_id") or "")
    return sorted(apps, key=lambda a: a["app_id"] != first)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--oa")
    ap.add_argument("--app")
    ap.add_argument("--since-hours", type=float)
    ap.add_argument("--fixture")
    a = ap.parse_args()

    accounts = read_json(ACCOUNTS, None)
    if not accounts:
        print(json.dumps({"ok": False, "error": "Chưa có config/accounts.json"}, ensure_ascii=False))
        sys.exit(1)
    first_run_hours = a.since_hours or accounts.get("fetch", {}).get("first_run_hours", 48)
    cursors = read_json(CURSORS, {})
    owners = read_json(OWNERS, {})
    date_dir = OUT_ROOT / a.date
    index_path = date_dir / "index.json"
    index = read_json(index_path, {"date": a.date, "runs": [], "conversations": []})
    by_key = {c["conversation_key"]: c for c in index["conversations"]}
    run_ms = int(time.time() * 1000)
    summary = {"ok": True, "date": a.date, "oas": []}

    for oa in accounts.get("oa_accounts", []):
        oa_id = str(oa.get("oa_id") or "")
        if a.oa and oa_id != a.oa:
            continue
        apps = [{**x, "app_id": str(x["app_id"])} for x in oa.get("applications", [])
                if x.get("status", "active") == "active"]
        if a.app and a.app not in {x["app_id"] for x in apps}:
            continue
        cursor_key = oa_id or f"app:{apps[0]['app_id'] if apps else '?'}"
        window_ms = run_ms - int(first_run_hours * 3600_000)
        # --app is an on-demand look at one sale's customers: use the time window, not the OA cursor.
        since_ms = window_ms if a.app else (cursors.get(cursor_key, {}).get("last_message_ms") or window_ms)
        entry = {"oa_id": oa_id, "oa_name": oa.get("oa_name"), "ok": False}
        errors = []
        for reader in reader_candidates(oa, apps, a.app):
            try:
                src = FixtureSource(a.fixture) if a.fixture else ZaloApp(reader["app_id"])
                real_oa = str(src.oa_info().get("oa_id") or oa_id)
                if oa_id and real_oa != oa_id:
                    raise ZaloError(f"Ứng dụng {reader['app_id']} đang trỏ tới OA {real_oa}, khác cấu hình {oa_id}.",
                                    code="wrong_oa")
                oa_id = real_oa
                if a.app:
                    results, max_ms = fetch_one_sale(src, oa_id, reader, apps, since_ms, date_dir, owners, run_ms), None
                else:
                    results, max_ms = fetch_oa(src, oa_id, apps, since_ms, date_dir, owners, run_ms)
            except ZaloError as e:
                errors.append({"app_id": reader["app_id"], "error": str(e), **e.extra})
                continue
            entry.update(ok=True, reader_app_id=reader["app_id"], conversations=len(results),
                         new_messages=sum(r["new_messages"] for r in results),
                         unassigned=sum(1 for r in results if not r["owner_app"]),
                         per_sale={})
            for r in results:
                name = r["sale"] or "(chưa phân công)"
                entry["per_sale"][name] = entry["per_sale"].get(name, 0) + 1
                row = by_key.get(r["conversation_key"])
                if row is None:
                    row = {**r, "status": "pending_analysis"}
                    index["conversations"].append(row)
                    by_key[r["conversation_key"]] = row
                else:  # new messages later the same day -> analyse again with the merged file
                    row.update({**r, "status": "pending_analysis",
                                "new_messages": row.get("new_messages", 0) + r["new_messages"]})
            if max_ms is not None:
                cursors[oa_id or cursor_key] = {"last_message_ms": max_ms, "reader_app_id": reader["app_id"],
                                                "last_run": datetime.now().isoformat(timespec="seconds")}
            break
        if errors:
            entry["reader_errors"] = errors
        if not entry["ok"]:
            summary["ok"] = False
        summary["oas"].append(entry)

    index["runs"].append({"at": datetime.now().isoformat(timespec="seconds"), "only_app": a.app, "oas": summary["oas"]})
    write_json(index_path, index)
    write_json(OWNERS, owners)
    write_json(CURSORS, cursors)
    summary["index"] = str(index_path.relative_to(ROOT))
    summary["pending_analysis"] = sum(1 for c in index["conversations"] if c["status"] == "pending_analysis")
    summary["unassigned"] = sum(1 for c in index["conversations"] if not c.get("owner_app"))
    print(json.dumps(summary, ensure_ascii=False))
    sys.exit(0 if summary["ok"] else 2)


if __name__ == "__main__":
    main()
