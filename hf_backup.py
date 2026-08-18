# -*- coding: utf-8 -*-
"""Hugging Face Spaces free persistence.

Free CPU Spaces have ephemeral disk, so SQLite + VAPID keys are backed up to a
private HF dataset repo (free tier includes 100GB private storage, no card).
On startup the latest backup is restored; a background thread re-uploads every
minute when files change.
"""
import os
import threading
import time

import config

BACKUP_FILES = ["fitpulse.db", "vapid_private.pem"]
POLL_SECONDS = 60


def _api():
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        return None
    try:
        from huggingface_hub import HfApi
        return HfApi(token=token)
    except Exception:
        return None


def repo_id():
    return os.environ.get("HF_DATA_REPO", "").strip()


def _file_state():
    state = {}
    for name in BACKUP_FILES:
        p = os.path.join(config.DATA_DIR, name)
        if os.path.exists(p):
            state[name] = (os.path.getmtime(p), os.path.getsize(p))
    return state


def restore():
    api, rid = _api(), repo_id()
    if not api or not rid:
        return False
    for name in BACKUP_FILES:
        try:
            api.hf_hub_download(repo_id=rid, repo_type="dataset", filename=name,
                                local_dir=config.DATA_DIR)
        except Exception:
            pass
    return True


def _upload(files, api, rid):
    for name in files:
        p = os.path.join(config.DATA_DIR, name)
        if not os.path.exists(p):
            continue
        try:
            api.upload_file(path_or_fileobj=p, path_in_repo=name,
                            repo_id=rid, repo_type="dataset")
        except Exception:
            pass


def _run_loop(api, rid):
    last = {}
    while True:
        try:
            cur = _file_state()
            for name, st in cur.items():
                if last.get(name) != st:
                    _upload([name], api, rid)
                    last[name] = st
        except Exception:
            pass
        time.sleep(POLL_SECONDS)


def start():
    api, rid = _api(), repo_id()
    if not api or not rid:
        return
    restore()
    t = threading.Thread(target=_run_loop, args=(api, rid), daemon=True)
    t.start()