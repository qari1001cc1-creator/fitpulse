# -*- coding: utf-8 -*-
"""Minimal Web Push (RFC 8291) + VAPID client built on `cryptography`.

Sends push notifications to browser subscriptions (FCM/Mozilla push services)
without external dependencies. Everything is best effort - callers must
catch exceptions.
"""
import base64
import json
import os
import time
import requests

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _hkdf(ikm, salt, info, length):
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(ikm)


def _load_or_create_vapid():
    import config
    keyfile = os.path.join(config.DATA_DIR, "vapid_private.pem")
    if os.path.exists(keyfile):
        with open(keyfile, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
    else:
        priv = ec.generate_private_key(ec.SECP256R1())
        with open(keyfile, "wb") as f:
            f.write(priv.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()))
    return priv


def vapid_public_b64url():
    priv = _load_or_create_vapid()
    pub = priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return _b64e(pub)


def _vapid_aud(endpoint):
    from urllib.parse import urlsplit
    p = urlsplit(endpoint)
    return p.scheme + "://" + (p.netloc.split("@")[-1])


def _make_jwt(endpoint, priv):
    header = {"typ": "JWT", "alg": "ES256"}
    claims = {"aud": _vapid_aud(endpoint), "exp": int(time.time()) + 12 * 3600,
              "sub": "mailto:fitpulse@localhost"}
    seg = _b64e(json.dumps(header).encode()) + "." + _b64e(json.dumps(claims).encode())
    der = priv.sign(seg.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der)
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return seg + "." + _b64e(sig)


def send_push(endpoint, p256dh, auth, title, body, icon, url=None, timeout=10):
    """Send a push notification to one subscription. Raises on failure."""
    client_pub = _b64d(p256dh)
    auth_secret = _b64d(auth)
    priv = _load_or_create_vapid()
    vapid_pub = priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)

    eph = ec.generate_private_key(ec.SECP256R1())
    eph_pub = eph.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    peer = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), client_pub)
    shared = eph.exchange(ec.ECDH(), peer)

    prk = _hkdf(shared, auth_secret, b"WebPush: info\x00" + client_pub + eph_pub, 32)
    salt = os.urandom(16)
    ikm = _hkdf(prk, salt, b"WebPush: ikm", 32)
    key = _hkdf(ikm, b"Content-Encoding: aes128gcm\x00", b"", 16)
    nonce = _hkdf(ikm, b"Content-Encoding: nonce\x00", b"", 12)

    payload = json.dumps({"title": title, "body": body, "icon": icon,
                          "url": url or "/"}).encode("utf-8")
    ct = AESGCM(key).encrypt(nonce, payload, None)

    msg = salt + len(ct).to_bytes(4, "big") + eph_pub + ct
    jwt = _make_jwt(endpoint, priv)
    headers = {
        "Authorization": "vapid t=%s, k=%s" % (jwt, _b64e(vapid_pub)),
        "Content-Encoding": "aes128gcm",
        "TTL": "3600",
        "Content-Type": "application/octet-stream",
        "Urgency": "normal",
    }
    requests.post(endpoint, data=msg, headers=headers, timeout=timeout)