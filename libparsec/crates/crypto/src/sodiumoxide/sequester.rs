// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use zeroize::Zeroizing;

use openssl::hash::MessageDigest;
use openssl::pkey::{PKey, Private, Public};
use openssl::rsa::{Padding, Rsa};
use openssl::sign::{Signer, Verifier};

use serde::{Deserialize, Serialize};
use serde_bytes::Bytes;

use crate::{
    deserialize_with_armor, serialize_with_armor, CryptoError, CryptoResult, SecretKey,
    SequesterKeySize,
};

/*
 * PrivateKey
 */

#[derive(Clone)]
pub struct SequesterPrivateKeyDer(PKey<Private>);

crate::impl_key_debug!(SequesterPrivateKeyDer);

impl PartialEq for SequesterPrivateKeyDer {
    fn eq(&self, other: &Self) -> bool {
        let privkey = self
            .0
            .rsa()
            .expect("Should have been initialized with a RSA key");
        let other_privkey = other
            .0
            .rsa()
            .expect("Should have been initialized with a RSA key");
        privkey.n() == other_privkey.n()
            && privkey.e() == other_privkey.e()
            && privkey.d() == other_privkey.d()
            && privkey.p() == other_privkey.p()
            && privkey.q() == other_privkey.q()
            && privkey.dmp1() == other_privkey.dmp1()
            && privkey.dmq1() == other_privkey.dmq1()
            && privkey.iqmp() == other_privkey.iqmp()
    }
}

impl Eq for SequesterPrivateKeyDer {}

impl TryFrom<&[u8]> for SequesterPrivateKeyDer {
    type Error = CryptoError;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        PKey::private_key_from_der(bytes)
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))?
            .rsa()
            .and_then(PKey::from_rsa)
            .map(Self)
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))
    }
}

impl SequesterPrivateKeyDer {
    const ALGORITHM: &'static str = "RSAES-OAEP-SHA256-XSALSA20-POLY1305";

    pub fn generate_pair(size_in_bits: SequesterKeySize) -> (Self, SequesterPublicKeyDer) {
        let priv_key = Rsa::generate(size_in_bits as u32).expect("Cannot generate the RSA key");
        let pub_key = Rsa::from_public_components(
            priv_key.n().to_owned().expect("Unreachable"),
            priv_key.e().to_owned().expect("Unreachable"),
        )
        .and_then(PKey::from_rsa)
        .expect("Unreachable");
        let priv_key = PKey::from_rsa(priv_key).expect("Unreachable");

        (Self(priv_key), SequesterPublicKeyDer(pub_key))
    }

    pub fn size_in_bytes(&self) -> usize {
        self.0.size() as usize
    }

    pub fn dump(&self) -> Zeroizing<Vec<u8>> {
        Zeroizing::new(self.0.private_key_to_der().expect("Unreachable"))
    }

    pub fn dump_pem(&self) -> Zeroizing<String> {
        let pkey_pem = self.0.private_key_to_pem_pkcs8().expect("Unreachable");

        Zeroizing::new(String::from_utf8(pkey_pem).expect("Unreachable"))
    }

    pub fn load_pem(s: &str) -> CryptoResult<Self> {
        PKey::private_key_from_pem(s.as_bytes())
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))?
            .rsa()
            .and_then(PKey::from_rsa)
            .map(Self)
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))
    }

    pub fn decrypt(&self, data: &[u8]) -> CryptoResult<Vec<u8>> {
        let (cipherkey, ciphertext) =
            deserialize_with_armor(data, self.size_in_bytes(), Self::ALGORITHM)?;

        let mut decrypted_key_der = vec![0; cipherkey.len()];
        let mut decrypter =
            openssl::encrypt::Decrypter::new(&self.0).expect("Cannot create decrypter");
        decrypter
            .set_rsa_padding(Padding::PKCS1_OAEP)
            .expect("Cannot set RSA padding to OAEP");
        decrypter
            .set_rsa_oaep_md(openssl::hash::MessageDigest::sha256())
            .expect("Cannot set RSA OAEP MD to SHA256");

        let decrypted_key_bytecount = decrypter
            .decrypt(cipherkey, &mut decrypted_key_der)
            .map_err(|_| CryptoError::Decryption)?;

        let clearkey = SecretKey::try_from(&decrypted_key_der[..decrypted_key_bytecount])?;

        clearkey.decrypt(ciphertext)
    }
}

/*
 * PublicKey
 */

#[derive(Clone, Deserialize)]
#[serde(try_from = "&Bytes")]
pub struct SequesterPublicKeyDer(PKey<Public>);

crate::impl_key_debug!(SequesterPublicKeyDer);

impl PartialEq for SequesterPublicKeyDer {
    fn eq(&self, other: &Self) -> bool {
        // This is the only way I could find to compare two public keys.
        // There is also public_eq, but it is defined on the PKey type, and to get
        // a PKey<Public> from a Rsa<Public> we have to give up ownership, which
        // we can't do because we take a reference to both the keys we want to compare.
        // We could also clone the keys, but that would mean having an allocation in the
        // comparison method.
        let pubkey = self
            .0
            .rsa()
            .expect("Should have been initialized with a RSA key");
        let other_pubkey = other
            .0
            .rsa()
            .expect("Should have been initialized with a RSA key");
        pubkey.n() == other_pubkey.n() && pubkey.e() == other_pubkey.e()
    }
}

impl Eq for SequesterPublicKeyDer {}

impl TryFrom<&[u8]> for SequesterPublicKeyDer {
    type Error = CryptoError;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        Rsa::public_key_from_der(bytes)
            .and_then(PKey::from_rsa)
            .map(Self)
            .map_err(|err| CryptoError::SequesterPublicKeyDer(err.to_string()))
    }
}

impl TryFrom<&Bytes> for SequesterPublicKeyDer {
    type Error = CryptoError;

    fn try_from(data: &Bytes) -> Result<Self, Self::Error> {
        Self::try_from(data.as_ref())
    }
}

impl Serialize for SequesterPublicKeyDer {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_bytes(&self.dump())
    }
}

impl SequesterPublicKeyDer {
    const ALGORITHM: &'static str = "RSAES-OAEP-SHA256-XSALSA20-POLY1305";

    pub fn size_in_bytes(&self) -> usize {
        self.0.size() as usize
    }

    pub fn dump(&self) -> Vec<u8> {
        self.0.public_key_to_der().expect("Unreachable")
    }

    pub fn dump_pem(&self) -> String {
        let pkey_pem = self.0.public_key_to_pem().expect("Unreachable");

        String::from_utf8(pkey_pem).expect("Unreachable")
    }

    pub fn load_pem(s: &str) -> CryptoResult<Self> {
        Rsa::public_key_from_pem(s.as_bytes())
            .and_then(PKey::from_rsa)
            .map(Self)
            .map_err(|err| CryptoError::SequesterPublicKeyDer(err.to_string()))
    }

    // Encryption format:
    //   <algorithm name>:<encrypted secret key with RSA key><encrypted data with secret key>
    pub fn encrypt(&self, data: &[u8]) -> Vec<u8> {
        let secret_key = SecretKey::generate();

        let mut encrypted_secret_key = vec![0; self.0.size() as usize];

        let mut encrypter =
            openssl::encrypt::Encrypter::new(&self.0).expect("Cannot create encrypter");
        encrypter
            .set_rsa_padding(Padding::PKCS1_OAEP)
            .expect("Cannot set RSA padding to OAEP");
        encrypter
            .set_rsa_oaep_md(openssl::hash::MessageDigest::sha256())
            .expect("Cannot set RSA OAEP MD to SHA256");

        let encrypted_key_bytes = encrypter
            .encrypt(secret_key.as_ref(), &mut encrypted_secret_key)
            .expect("Unable to encrypt a secret key");

        // RSAES-OAEP uses 42 bytes for padding, hence even with an insecure
        // 1024 bits RSA key there is still 86 bytes available for payload
        // which is plenty to store the 32 bytes XSalsa20 key
        serialize_with_armor(
            &encrypted_secret_key[0..encrypted_key_bytes],
            &secret_key.encrypt(data),
            self.size_in_bytes(),
            Self::ALGORITHM,
        )
    }
}

/*
 * SigningKey
 */

#[derive(Clone)]
pub struct SequesterSigningKeyDer(PKey<Private>);

crate::impl_key_debug!(SequesterSigningKeyDer);

impl PartialEq for SequesterSigningKeyDer {
    fn eq(&self, other: &Self) -> bool {
        self.0.public_eq(other.0.as_ref())
    }
}

impl Eq for SequesterSigningKeyDer {}

impl TryFrom<&[u8]> for SequesterSigningKeyDer {
    type Error = CryptoError;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        let key = PKey::private_key_from_der(bytes)
            .map(Self)
            .map_err(|err| CryptoError::SequesterPublicKeyDer(err.to_string()))?;

        // Verify it's RSA key
        key.0
            .rsa()
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))?;

        Ok(key)
    }
}

impl SequesterSigningKeyDer {
    const ALGORITHM: &'static str = "RSASSA-PSS-SHA256";

    pub fn generate_pair(size_in_bits: SequesterKeySize) -> (Self, SequesterVerifyKeyDer) {
        let (priv_key, pub_key) = SequesterPrivateKeyDer::generate_pair(size_in_bits);
        let signing_key = priv_key.0;
        let verify_key = pub_key.0;

        (Self(signing_key), SequesterVerifyKeyDer(verify_key))
    }

    pub fn size_in_bytes(&self) -> usize {
        self.0.bits() as usize / 8
    }

    pub fn dump(&self) -> Zeroizing<Vec<u8>> {
        Zeroizing::new(self.0.private_key_to_der().expect("Unreachable"))
    }

    pub fn dump_pem(&self) -> Zeroizing<String> {
        let pkey_pem = self.0.private_key_to_pem_pkcs8().expect("Unreachable");

        Zeroizing::new(String::from_utf8(pkey_pem).expect("Unreachable"))
    }

    pub fn load_pem(s: &str) -> CryptoResult<Self> {
        let key = PKey::private_key_from_pem(s.as_bytes())
            .map(Self)
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))?;

        // Verify it's RSA key
        key.0
            .rsa()
            .map_err(|err| CryptoError::SequesterPrivateKeyDer(err.to_string()))?;

        Ok(key)
    }

    // Signature format:
    //   <algorithm name>:<signature><data>
    pub fn sign(&self, data: &[u8]) -> Vec<u8> {
        // https://www.openssl.org/docs/man3.0/man3/EVP_PKEY_CTX_set_rsa_pss_saltlen.html
        // EVP_PKEY_CTX_set_rsa_pss_saltlen() sets the RSA PSS salt length to saltlen.
        // As its name implies it is only supported for PSS padding. If this function
        // is not called then the maximum salt length is used when signing and auto
        // detection when verifying.
        // Rustcrypto uses maximum salt length, so we do the same, to not call `set_rsa_pss_saltlen()`.
        let mut signer =
            Signer::new(MessageDigest::sha256(), &self.0).expect("Unable to build a Signer");

        signer
            .set_rsa_padding(Padding::PKCS1_PSS)
            .expect("OpenSSL error");

        signer.update(data).expect("Unreachable");
        let signed_data = signer.sign_to_vec().expect("Unable to sign a message");

        serialize_with_armor(&signed_data, data, self.size_in_bytes(), Self::ALGORITHM)
    }
}

/*
 * VerifyKey
 */

#[derive(Clone, Deserialize)]
#[serde(try_from = "&Bytes")]
pub struct SequesterVerifyKeyDer(PKey<Public>);

crate::impl_key_debug!(SequesterVerifyKeyDer);

impl PartialEq for SequesterVerifyKeyDer {
    fn eq(&self, other: &Self) -> bool {
        self.0.public_eq(other.0.as_ref())
    }
}

impl Eq for SequesterVerifyKeyDer {}

impl TryFrom<&[u8]> for SequesterVerifyKeyDer {
    type Error = CryptoError;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        // Verify it's RSA key
        Rsa::public_key_from_der(bytes)
            .map(|x| PKey::from_rsa(x).expect("Unreachable"))
            .map(Self)
            .map_err(|err| CryptoError::SequesterPublicKeyDer(err.to_string()))
    }
}

impl TryFrom<&Bytes> for SequesterVerifyKeyDer {
    type Error = CryptoError;

    fn try_from(data: &Bytes) -> Result<Self, Self::Error> {
        Self::try_from(data.as_ref())
    }
}

impl Serialize for SequesterVerifyKeyDer {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_bytes(&self.dump())
    }
}

impl SequesterVerifyKeyDer {
    const ALGORITHM: &'static str = "RSASSA-PSS-SHA256";

    pub fn size_in_bytes(&self) -> usize {
        self.0.bits() as usize / 8
    }

    pub fn dump(&self) -> Vec<u8> {
        self.0.public_key_to_der().expect("Unreachable")
    }

    pub fn dump_pem(&self) -> String {
        let pkey_pem = self.0.public_key_to_pem().expect("Unreachable");

        String::from_utf8(pkey_pem).expect("Unable to get UTF-8 String from public key PEM")
    }

    pub fn load_pem(s: &str) -> CryptoResult<Self> {
        // Verify it's RSA key
        Rsa::public_key_from_pem(s.as_bytes())
            .map(|x| PKey::from_rsa(x).expect("Unreachable"))
            .map(Self)
            .map_err(|err| CryptoError::SequesterPublicKeyDer(err.to_string()))
    }

    pub fn verify(&self, data: &[u8]) -> CryptoResult<Vec<u8>> {
        let (signature, contents) =
            deserialize_with_armor(data, self.size_in_bytes(), Self::ALGORITHM)?;

        // https://www.openssl.org/docs/man3.0/man3/EVP_PKEY_CTX_set_rsa_pss_saltlen.html
        // EVP_PKEY_CTX_set_rsa_pss_saltlen() sets the RSA PSS salt length to saltlen.
        // As its name implies it is only supported for PSS padding. If this function
        // is not called then the maximum salt length is used when signing and auto
        // detection when verifying.
        // So we don't need to call `set_rsa_pss_saltlen()`.
        let mut verifier = Verifier::new(MessageDigest::sha256(), &self.0)
            .map_err(|_| CryptoError::SignatureVerification)?;

        verifier
            .set_rsa_padding(Padding::PKCS1_PSS)
            .expect("OpenSSL error");

        verifier
            .update(contents)
            .map_err(|_| CryptoError::SignatureVerification)?;

        match verifier.verify(signature) {
            Ok(true) => Ok(contents.to_vec()),
            Ok(false) | Err(_) => Err(CryptoError::SignatureVerification),
        }
    }
}
