"""Verificador local de PIN y TOTP para el companion CloudPress.

Los factores se conservan exclusivamente en el almacén seguro del sistema
operativo proporcionado por ``keyring``. Este módulo es código local confiable:
no debe ejecutarse, importarse ni configurarse desde una solicitud de agente.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import getpass
import hashlib
import hmac
import json
import secrets
import struct
import time

import keyring

from .client import VerifiedConfirmation


SERVICE = "lsfa.cloudpress.companion"
DEFAULT_PROFILE = "default"
PIN_COST = 2**15
PIN_BLOCK_SIZE = 8
PIN_PARALLELISM = 1


def validate_profile(profile: str) -> str:
    if not isinstance(profile, str) or not 1 <= len(profile) <= 64 or not profile.replace("-", "").replace("_", "").isalnum():
        raise ValueError("invalid_profile")
    return profile


def derive_pin(pin: str, salt: bytes) -> bytes:
    if not isinstance(pin, str) or len(pin) < 6 or len(pin) > 256 or not isinstance(salt, bytes) or len(salt) != 32:
        raise ValueError("invalid_pin")
    return hashlib.scrypt(pin.encode("utf-8"), salt=salt, n=PIN_COST,
                          r=PIN_BLOCK_SIZE, p=PIN_PARALLELISM,
                          maxmem=128 * 1024 * 1024, dklen=32)


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_code(secret: str, timestamp: float | None = None) -> str:
    if not isinstance(secret, str) or not secret or not secret.isascii():
        raise ValueError("invalid_totp_secret")
    try:
        key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8), casefold=True)
    except Exception as error:
        raise ValueError("invalid_totp_secret") from error
    counter = int((time.time() if timestamp is None else timestamp) // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def verify_totp(secret: str, code: str, timestamp: float | None = None) -> bool:
    if not isinstance(code, str) or not code.isascii() or len(code) != 6 or not code.isdecimal():
        return False
    current = time.time() if timestamp is None else timestamp
    return any(hmac.compare_digest(totp_code(secret, current + offset * 30), code) for offset in (-1, 0, 1))


def encode_record(pin: str, totp_secret: str) -> str:
    salt = secrets.token_bytes(32)
    record = {
        "version": 1,
        "pin_salt": base64.b64encode(salt).decode("ascii"),
        "pin_hash": base64.b64encode(derive_pin(pin, salt)).decode("ascii"),
        "totp_secret": totp_secret,
    }
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def decode_record(raw: str) -> dict:
    try:
        record = json.loads(raw)
        if not isinstance(record, dict) or record.get("version") != 1:
            raise ValueError
        salt = base64.b64decode(record["pin_salt"], validate=True)
        pin_hash = base64.b64decode(record["pin_hash"], validate=True)
        secret = record["totp_secret"]
        if len(salt) != 32 or len(pin_hash) != 32:
            raise ValueError
        totp_code(secret, 0)
    except Exception as error:
        raise ValueError("invalid_factor_record") from error
    return {"salt": salt, "pin_hash": pin_hash, "totp_secret": secret}


def load_record(profile: str, backend=keyring) -> dict:
    raw = backend.get_password(SERVICE, validate_profile(profile))
    if not isinstance(raw, str):
        raise ValueError("factors_not_enrolled")
    return decode_record(raw)


def verifier_for_profile(profile: str = DEFAULT_PROFILE):
    """Return a broker-compatible verifier bound to one enrolled profile."""
    profile = validate_profile(profile)

    def local_verify(summary, method, binding, expires_at):
        if method not in {"pin", "pin_and_totp"} or not isinstance(binding, str) or not isinstance(expires_at, (int, float)):
            return None
        if time.time() >= expires_at:
            return None
        try:
            record = load_record(profile)
            rendered = json.dumps(summary, ensure_ascii=True, sort_keys=True, indent=2)
            print("\nCloudPress solicita confirmar esta acción:\n" + rendered)
            if input("Escribe APROBAR para continuar: ") != "APROBAR":
                return None
            pin = getpass.getpass("PIN local: ")
            if not hmac.compare_digest(derive_pin(pin, record["salt"]), record["pin_hash"]):
                return None
            if method == "pin_and_totp":
                code = getpass.getpass("Código del autenticador local: ")
                if not verify_totp(record["totp_secret"], code):
                    return None
            return VerifiedConfirmation(binding, method, min(expires_at, time.time() + 60))
        except Exception:
            return None

    return local_verify


def verify(summary, method, binding, expires_at):
    """Callback exported for ``--verifier src.lsfa.cloudpress_verifier:verify``."""
    return verifier_for_profile()(summary, method, binding, expires_at)


def provisioning_uri(secret: str, profile: str) -> str:
    label = f"CloudPress Local Approval:{validate_profile(profile)}"
    from urllib.parse import quote
    return f"otpauth://totp/{quote(label)}?secret={secret}&issuer={quote('CloudPress Local Approval')}&algorithm=SHA1&digits=6&period=30"


def show_qr(secret: str, profile: str) -> None:
    """Muestra el QR en una ventana local, sin escribir la semilla en stdout."""
    try:
        import qrcode
        from PIL import ImageTk
        import tkinter as tk
    except ImportError as error:
        raise RuntimeError("qr_support_unavailable") from error
    root = tk.Tk()
    root.title("Vincular autenticador local de CloudPress")
    image = qrcode.make(provisioning_uri(secret, profile))
    photo = ImageTk.PhotoImage(image)
    tk.Label(root, text="Escanea este código con tu aplicación autenticadora.\nNo lo compartas.").pack(padx=16, pady=(16, 8))
    label = tk.Label(root, image=photo)
    label.image = photo
    label.pack(padx=16, pady=8)
    tk.Button(root, text="Continuar", command=root.destroy).pack(pady=(8, 16))
    root.mainloop()


def enroll(profile: str = DEFAULT_PROFILE, backend=keyring) -> None:
    profile = validate_profile(profile)
    pin = getpass.getpass("Crea un PIN local (mínimo 6 caracteres): ")
    if pin != getpass.getpass("Confirma el PIN local: "):
        raise ValueError("pin_mismatch")
    secret = new_totp_secret()
    show_qr(secret, profile)
    if not verify_totp(secret, getpass.getpass("Código del autenticador local: ")):
        raise ValueError("totp_not_verified")
    backend.set_password(SERVICE, profile, encode_record(pin, secret))


def main() -> None:
    parser = argparse.ArgumentParser(description="Configura el verificador local de CloudPress LSFA")
    parser.add_argument("command", choices=("enroll",))
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    args = parser.parse_args()
    enroll(args.profile)
    print("Factores locales configurados.")


if __name__ == "__main__":
    main()
