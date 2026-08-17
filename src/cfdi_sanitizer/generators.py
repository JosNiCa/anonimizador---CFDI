from __future__ import annotations

import uuid


WORDS = ("HORIZONTE", "VECTOR", "CENTRO", "PRISMA", "NEXO", "VALLE", "AURORA", "SENDERO")


def rfc(d: bytes) -> str:
    # Prefijo reservado como ficción y fecha imposible de confundir deliberadamente con validación SAT.
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "FIC000000" + "".join(chars[b % len(chars)] for b in d[:3])


def name(d: bytes) -> str:
    return f"ENTIDAD SINTETICA {WORDS[d[0] % len(WORDS)]} {d[1]:03d} SA DE CV"


def email(d: bytes) -> str:
    return f"entidad-{d[:6].hex()}@example.invalid"


def phone(d: bytes) -> str:
    return "000" + "".join(str(x % 10) for x in d[:7])


def account(d: bytes, length: int = 18) -> str:
    return "0" + "".join(str(x % 10) for x in d[: length - 1])


def clabe(d: bytes) -> str:
    digits = [d[index % len(d)] % 10 for index in range(17)]
    weights = (3, 7, 1)
    check = (10 - sum((digit * weights[index % 3]) % 10 for index, digit in enumerate(digits)) % 10) % 10
    return "".join(map(str, digits + [check]))


def synthetic_uuid(d: bytes) -> str:
    raw = bytearray(d[:16]); raw[6] = (raw[6] & 15) | 64; raw[8] = (raw[8] & 63) | 128
    return str(uuid.UUID(bytes=bytes(raw))).upper()


def identifier(d: bytes) -> str:
    return "SYN-" + d[:8].hex().upper()
