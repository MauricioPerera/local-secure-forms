"""Verificador local de PIN y TOTP para el companion CloudPress.

Los factores se conservan exclusivamente en el almacén seguro del sistema
operativo proporcionado por ``keyring``. Este módulo es código local confiable:
no debe ejecutarse, importarse ni configurarse desde una solicitud de agente.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
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
MIN_LOCAL_PASSPHRASE_LENGTH = 12


def validate_profile(profile: str) -> str:
    if not isinstance(profile, str) or not 1 <= len(profile) <= 64 or not profile.replace("-", "").replace("_", "").isalnum():
        raise ValueError("invalid_profile")
    return profile


def derive_pin(pin: str, salt: bytes) -> bytes:
    if not isinstance(pin, str) or len(pin) < MIN_LOCAL_PASSPHRASE_LENGTH or len(pin) > 256 or not isinstance(salt, bytes) or len(salt) != 32:
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


def ensure_secure_keyring(backend=keyring) -> None:
    """Reject known plaintext, null and unavailable credential backends."""
    active = backend.get_keyring() if hasattr(backend, "get_keyring") else backend
    identity = f"{type(active).__module__}.{type(active).__name__}".lower()
    allowed = ("keyring.backends.windows.", "keyring.backends.macos.",
               "keyring.backends.secretservice.", "keyring.backends.kwallet.")
    if not identity.startswith(allowed):
        raise RuntimeError("secure_keyring_required")


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
            if not local_approval_dialog(summary, method, record):
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


def local_secret_dialog(title: str, prompt: str, *, secret: bool = True) -> str | None:
    """Collect one local factor in a modal GUI instead of an invisible shell."""
    try:
        import tkinter as tk
        from tkinter import simpledialog
    except ImportError as error:
        raise RuntimeError("gui_support_unavailable") from error
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return simpledialog.askstring(title, prompt, parent=root, show="•" if secret else "")
    finally:
        root.destroy()


def approval_summary(summary: object) -> str:
    """Render the server-attested target as a concise human review, never raw JSON."""
    if not isinstance(summary, dict):
        return "CloudPress no proporcionó un resumen verificable de la acción."
    operations = {
        "purge_content": "Eliminar permanentemente contenido de la Papelera",
        "delete_user": "Eliminar permanentemente una cuenta de usuario",
        "delete_media": "Eliminar permanentemente un archivo multimedia",
        "uninstall_plugin": "Desinstalar un plugin",
        "delete_metadata": "Eliminar un valor de metadatos",
        "delete_core_term": "Eliminar un término de taxonomía",
        "delete_plugin_term": "Eliminar un término de plugin",
    }
    labels = {
        "id": "ID", "title": "Título", "username": "Usuario", "role": "Rol",
        "key": "Archivo", "size": "Tamaño", "scope": "Ámbito", "entityId": "Entidad",
        "pluginId": "Plugin", "taxonomyId": "Taxonomía", "name": "Nombre", "slug": "Slug",
        "contentReferences": "Contenido vinculado", "policy": "Política",
    }
    operation = summary.get("operation")
    target = summary.get("target")
    lines = [f"Acción: {operations.get(operation, 'Acción irreversible de CloudPress')}", "", "Destino confirmado por CloudPress:"]
    if isinstance(target, dict) and target:
        for key, value in target.items():
            if value is not None:
                lines.append(f"• {labels.get(key, key)}: {value}")
    else:
        lines.append("• No hay detalles de destino disponibles.")
    lines.extend(("", "Esta acción no se puede deshacer."))
    return "\n".join(lines)


def local_approval_dialog(summary: object, method: str, record: dict) -> bool:
    """Show one roomy local approval form; factors never leave this process."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as error:
        raise RuntimeError("gui_support_unavailable") from error
    root = tk.Tk()
    root.title("CloudPress — Confirmación local requerida")
    root.minsize(720, 520)
    root.geometry("780x600")
    root.attributes("-topmost", True)
    root.configure(bg="#f4f7fb")
    approved = False
    try:
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Confirmar acción irreversible", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Revisa el destino. CloudPress no ejecutará esta acción sin tus factores locales.", wraplength=700).pack(anchor="w", pady=(6, 16))
        details = tk.Text(frame, height=12, wrap="word", font=("Segoe UI", 11), padx=12, pady=12, relief="solid", borderwidth=1)
        details.insert("1.0", approval_summary(summary))
        details.configure(state="disabled", background="#ffffff", foreground="#172033")
        details.pack(fill="both", expand=True)
        understood = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Entiendo que esta acción no se puede deshacer.", variable=understood).pack(anchor="w", pady=(16, 8))
        fields = ttk.Frame(frame)
        fields.pack(fill="x")
        ttk.Label(fields, text="Contraseña local:").grid(row=0, column=0, sticky="w", pady=5)
        pin = ttk.Entry(fields, show="•", width=42)
        pin.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=5)
        code = None
        if method == "pin_and_totp":
            ttk.Label(fields, text="Código del autenticador:").grid(row=1, column=0, sticky="w", pady=5)
            code = ttk.Entry(fields, width=18)
            code.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=5)
        fields.columnconfigure(1, weight=1)
        feedback = ttk.Label(frame, foreground="#b42318")
        feedback.pack(anchor="w", pady=(8, 0))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(16, 0))

        def cancel() -> None:
            root.destroy()

        def submit() -> None:
            nonlocal approved
            if not understood.get():
                feedback.configure(text="Confirma que entiendes que la acción es irreversible.")
                return
            try:
                pin_ok = hmac.compare_digest(derive_pin(pin.get(), record["salt"]), record["pin_hash"])
            except Exception:
                pin_ok = False
            if not pin_ok:
                pin.delete(0, "end")
                feedback.configure(text="La contraseña local no coincide.")
                pin.focus_set()
                return
            if method == "pin_and_totp" and (code is None or not verify_totp(record["totp_secret"], code.get())):
                if code is not None:
                    code.delete(0, "end")
                    code.focus_set()
                feedback.configure(text="El código del autenticador no es válido.")
                return
            approved = True
            root.destroy()

        ttk.Button(buttons, text="Cancelar", command=cancel).pack(side="right")
        ttk.Button(buttons, text="Aprobar acción", command=submit).pack(side="right", padx=(0, 10))
        root.protocol("WM_DELETE_WINDOW", cancel)
        pin.focus_set()
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
    return approved


def enroll(profile: str = DEFAULT_PROFILE, backend=keyring) -> None:
    profile = validate_profile(profile)
    if backend is keyring:
        ensure_secure_keyring()
    pin = local_secret_dialog("CloudPress LSFA", f"Crea una contraseña local (mínimo {MIN_LOCAL_PASSPHRASE_LENGTH} caracteres):")
    if pin is None:
        raise ValueError("enrollment_cancelled")
    confirmation = local_secret_dialog("CloudPress LSFA", "Confirma la contraseña local:")
    if confirmation is None:
        raise ValueError("enrollment_cancelled")
    if not hmac.compare_digest(pin, confirmation):
        raise ValueError("pin_mismatch")
    # Validate before generating or displaying a QR. A failed enrolment must
    # never leave the user with an unpersisted authenticator seed.
    if len(pin) < MIN_LOCAL_PASSPHRASE_LENGTH:
        raise ValueError("local_password_too_short")
    secret = new_totp_secret()
    show_qr(secret, profile)
    code = local_secret_dialog("CloudPress LSFA", "Introduce el código de seis dígitos de tu autenticador:", secret=False)
    if code is None:
        raise ValueError("enrollment_cancelled")
    if not verify_totp(secret, code):
        raise ValueError("totp_not_verified")
    backend.set_password(SERVICE, profile, encode_record(pin, secret))


def main() -> None:
    parser = argparse.ArgumentParser(description="Configura el verificador local de CloudPress LSFA")
    parser.add_argument("command", choices=("enroll",))
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    args = parser.parse_args()
    ensure_secure_keyring()
    try:
        enroll(args.profile)
    except ValueError as error:
        if str(error) == "pin_mismatch":
            raise SystemExit("Las contraseñas locales no coinciden. No se modificó el enrolamiento; vuelve a intentarlo.") from None
        if str(error) == "local_password_too_short":
            raise SystemExit(f"La contraseña local debe tener al menos {MIN_LOCAL_PASSPHRASE_LENGTH} caracteres. No se modificó el enrolamiento.") from None
        if str(error) == "enrollment_cancelled":
            raise SystemExit("El enrolamiento se canceló. No se modificó ningún factor.") from None
        raise
    print("Factores locales configurados.")


if __name__ == "__main__":
    main()
