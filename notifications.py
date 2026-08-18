# -*- coding: utf-8 -*-
"""FitPulse notifications: in-app center + browser/web push (best effort)."""
import database as db

DEFAULT_ICON = "/static/icons/icon-192.png"


def notify(uid, title, body, ntype="info", icon=None, url=None):
    """Insert an in-app notification and try to deliver a push notification."""
    try:
        db.execute("INSERT INTO notifications (user_id, title, body, ntype, icon, created_at) "
                   "VALUES (?,?,?,?,?,?)",
                   (uid, title, body, ntype, icon or DEFAULT_ICON, db.now()))
    except Exception:
        return
    push_to_user(uid, title, body, icon or DEFAULT_ICON, url)


def unread_count(uid):
    row = db.query_one("SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND read=0", (uid,))
    return row["c"] if row else 0


def mark_read(uid, nid=None):
    if nid:
        db.execute("UPDATE notifications SET read=1 WHERE user_id=? AND id=?", (uid, nid))
    else:
        db.execute("UPDATE notifications SET read=1 WHERE user_id=? AND read=0", (uid,))


def push_to_user(uid, title, body, icon=None, url=None):
    """Send a Web Push to all saved subscriptions (best effort, never crashes)."""
    try:
        sub_rows = db.query("SELECT endpoint, p256dh, auth FROM push_subs WHERE user_id=?", (uid,))
        if not sub_rows:
            return
        from webpush_lib import send_push
        for s in sub_rows:
            try:
                send_push(s["endpoint"], s["p256dh"], s["auth"], title, body,
                          icon or DEFAULT_ICON, url)
            except Exception:
                continue
    except Exception:
        return


def subscribe(uid, endpoint, p256dh, auth):
    db.execute("INSERT OR REPLACE INTO push_subs (user_id, endpoint, p256dh, auth, created_at) "
               "VALUES (?,?,?,?,?)", (uid, endpoint, p256dh, auth, db.now()))