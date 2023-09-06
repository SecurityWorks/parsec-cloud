# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

class SecretKey:
    def __init__(self, data: bytes) -> None: ...
    @property
    def secret(self) -> bytes: ...
    @classmethod
    def generate(cls) -> SecretKey: ...
    def encrypt(self, data: bytes) -> bytes: ...
    def decrypt(self, ciphered: bytes) -> bytes: ...
    def hmac(self, data: bytes, digest_size: int) -> bytes: ...
    @classmethod
    def generate_recovery_passphrase(cls) -> tuple[str, SecretKey]: ...
    @classmethod
    def from_recovery_passphrase(cls, passphrase: str) -> SecretKey: ...
    @classmethod
    def generate_salt(cls) -> bytes: ...
    @classmethod
    def from_password(cls, password: str, salt: bytes) -> SecretKey: ...

class HashDigest:
    def __init__(self, hash: bytes) -> None: ...
    @property
    def digest(self) -> bytes: ...
    @staticmethod
    def from_data(data: bytes) -> HashDigest: ...
    def hexdigest(self) -> str: ...

class SigningKey:
    def __init__(self, data: bytes) -> None: ...
    @property
    def verify_key(self) -> VerifyKey: ...
    @classmethod
    def generate(cls) -> SigningKey: ...
    def sign(self, data: bytes) -> bytes: ...
    def sign_only_signature(self, data: bytes) -> bytes: ...
    def encode(self) -> bytes: ...

class VerifyKey:
    def __init__(self, data: bytes) -> None: ...
    def __bytes__(self) -> bytes: ...
    def verify(self, signed: bytes) -> bytes: ...
    def verify_with_signature(self, signature: bytes, message: bytes) -> None: ...
    @classmethod
    def unsecure_unwrap(cls, signed: bytes) -> bytes: ...
    def encode(self) -> bytes: ...

class PrivateKey:
    def __init__(self, data: bytes) -> None: ...
    @property
    def public_key(self) -> PublicKey: ...
    @classmethod
    def generate(cls) -> PrivateKey: ...
    def decrypt_from_self(self, ciphered: bytes) -> bytes: ...
    def encode(self) -> bytes: ...
    def generate_shared_secret_key(self, peer_public_key: PublicKey) -> SecretKey: ...

class PublicKey:
    def __init__(self, data: bytes) -> None: ...
    def encrypt_for_self(self, data: bytes) -> bytes: ...
    def encode(self) -> bytes: ...

class SequesterPrivateKeyDer:
    def __init__(self, data: bytes) -> None: ...
    @classmethod
    def generate_pair(
        cls, size_in_bits: int
    ) -> tuple[SequesterPrivateKeyDer, SequesterPublicKeyDer]: ...
    def dump(self) -> bytes: ...
    def dump_pem(self) -> str: ...
    @classmethod
    def load_pem(cls, s: str) -> SequesterPrivateKeyDer: ...
    def decrypt(self, data: bytes) -> bytes: ...

class SequesterPublicKeyDer:
    def __init__(self, data: bytes) -> None: ...
    def dump(self) -> bytes: ...
    def dump_pem(self) -> str: ...
    @classmethod
    def load_pem(cls, s: str) -> SequesterPublicKeyDer: ...
    def encrypt(self, data: bytes) -> bytes: ...

class SequesterSigningKeyDer:
    @classmethod
    def generate_pair(
        cls, size_in_bits: int
    ) -> tuple[SequesterSigningKeyDer, SequesterVerifyKeyDer]: ...
    def dump(self) -> bytes: ...
    def dump_pem(self) -> str: ...
    @classmethod
    def load_pem(cls, s: str) -> SequesterSigningKeyDer: ...
    def sign(self, data: bytes) -> bytes: ...

class SequesterVerifyKeyDer:
    def __init__(self, data: bytes) -> None: ...
    def dump(self) -> bytes: ...
    def dump_pem(self) -> str: ...
    @classmethod
    def load_pem(cls, s: str) -> SequesterVerifyKeyDer: ...
    def verify(self, data: bytes) -> bytes: ...

def generate_nonce() -> bytes: ...

class CryptoError(Exception): ...