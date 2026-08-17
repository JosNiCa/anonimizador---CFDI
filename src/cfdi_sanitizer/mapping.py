from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path

class DatasetContext:
    """Mapping HMAC determinista; los valores reales jamás se registran ni exportan."""

    def __init__(self, seed: str | bytes | None = None) -> None:
        raw = seed.encode() if isinstance(seed, str) else seed
        self._seed = raw or os.urandom(32)
        self._mapping: dict[str, dict[str, str]] = {}
        self.originals: set[str] = set()

    def digest(self, category: str, value: str) -> bytes:
        return hmac.new(self._seed, f"{category}\0{value}".encode(), hashlib.sha256).digest()

    def map(self, category: str, value: str, factory) -> str:
        self.originals.add(value)
        bucket = self._mapping.setdefault(category, {})
        if value not in bucket:
            bucket[value] = factory(self.digest(category, value))
        return bucket[value]

    def save_encrypted(self, path: Path, password: str) -> None:
        from cryptography.fernet import Fernet

        salt = os.urandom(16)
        key = _key(password, salt)
        payload = json.dumps({"seed": base64.b64encode(self._seed).decode(), "map": self._mapping}).encode()
        path.write_bytes(b"CFDI1" + salt + Fernet(key).encrypt(payload))

    @classmethod
    def load_encrypted(cls, path: Path, password: str) -> "DatasetContext":
        from cryptography.fernet import Fernet

        data = path.read_bytes()
        if not data.startswith(b"CFDI1"):
            raise ValueError("Formato de proyecto no reconocido")
        payload = json.loads(Fernet(_key(password, data[5:21])).decrypt(data[21:]))
        context = cls(base64.b64decode(payload["seed"]))
        context._mapping = payload["map"]
        context.originals = {value for values in context._mapping.values() for value in values}
        return context


def _key(password: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))
