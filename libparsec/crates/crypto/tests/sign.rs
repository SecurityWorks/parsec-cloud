// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

use std::convert::TryFrom;

use hex_literal::hex;
use pretty_assertions::assert_eq;
use serde_test::{assert_tokens, Token};

use libparsec_crypto::{CryptoError, SigningKey, VerifyKey};

#[macro_use]
mod common;

#[test]
fn consts() {
    assert_eq!(SigningKey::ALGORITHM, "ed25519");
    assert_eq!(VerifyKey::ALGORITHM, "ed25519");

    assert_eq!(SigningKey::SIZE, 32);
    assert_eq!(VerifyKey::SIZE, 32);
}

test_serde!(signing_serde, SigningKey);
test_serde!(verify_serde, VerifyKey);

#[test]
fn round_trip() {
    let sk = SigningKey::generate();

    let data = b"Hello, world !";
    let signed = sk.sign(data);

    let vk = sk.verify_key();
    let verified_data = vk.verify(&signed).unwrap();
    assert_eq!(verified_data, data);

    let expected_signature = &signed[..SigningKey::SIGNATURE_SIZE];
    let expected_message = &signed[SigningKey::SIGNATURE_SIZE..];

    let (signature, message) = VerifyKey::unsecure_unwrap(&signed).unwrap();
    assert_eq!(signature, expected_signature);
    assert_eq!(message, expected_message);
}

#[test]
fn signature_verification_spec() {
    let vk = VerifyKey::from(hex!(
        "78958e49abad190be2d51bab73af07f87682cfcd65cceedd27e4b2a94bfd8537"
    ));
    // Signed text generated with base python implementation
    let signed_text = hex!("32d26711dc973e8df13bbafddc23fc26efe4aca1b86a4e0e7dad7c03df7ffc25d24b865478d164f8868ad0e087587e2c45e45d5598c7929b4605699bbab4b109616c6c20796f75722062617365206172652062656c6f6e6720746f207573");

    let text = vk.verify(&signed_text).unwrap();
    assert_eq!(text, b"all your base are belong to us");

    let (signature, message) = VerifyKey::unsecure_unwrap(&signed_text).unwrap();
    assert_eq!(message, b"all your base are belong to us");
    assert_eq!(signature, &signed_text[..64]);
}

#[test]
fn signature_only() {
    let sk = SigningKey::generate();

    let data = b"Hello world, I would like to sign this message!";
    let signed = sk.sign_only_signature(data);
    let expected_signed_message = sk.sign(data);
    let expected_signature = &expected_signed_message[..SigningKey::SIGNATURE_SIZE];

    assert_eq!(signed, expected_signature);

    let vk = sk.verify_key();
    let signed_message = Vec::from_iter(signed.iter().chain(data).copied());
    let res = vk.verify(&signed_message).unwrap();

    assert_eq!(res, data);

    // Also test verify_with_signature

    vk.verify_with_signature(signed.as_ref().try_into().unwrap(), data)
        .unwrap();
}

test_msgpack_serialization!(
    signingkey_serialization_spec,
    SigningKey,
    hex!("bae756e3815f05b1a5877c7d625d51af5805ef217142781948e62215bdf0f21b"),
    hex!("c420bae756e3815f05b1a5877c7d625d51af5805ef217142781948e62215bdf0f21b")
);

test_msgpack_serialization!(
    verifykey_serialization_spec,
    VerifyKey,
    hex!("78958e49abad190be2d51bab73af07f87682cfcd65cceedd27e4b2a94bfd8537"),
    hex!("c42078958e49abad190be2d51bab73af07f87682cfcd65cceedd27e4b2a94bfd8537")
);

#[test]
fn signing_key_should_verify_length_when_deserialize() {
    let data = hex!("c40564756d6d79");
    assert_eq!(
        rmp_serde::from_slice::<SigningKey>(&data)
            .unwrap_err()
            .to_string(),
        "Invalid data size"
    );
}

#[test]
fn verify_key_should_verify_length_when_deserialize() {
    let data = hex!("c40564756d6d79");
    assert_eq!(
        rmp_serde::from_slice::<VerifyKey>(&data)
            .unwrap_err()
            .to_string(),
        "Invalid data size"
    );
}

#[test]
fn signkey_from_too_small_data() {
    assert!(matches!(
        SigningKey::try_from(b"dummy".as_ref()),
        Err(CryptoError::DataSize)
    ))
}

#[test]
fn verifykey_from_too_small_data() {
    assert!(matches!(
        VerifyKey::try_from(b"dummy".as_ref()),
        Err(CryptoError::DataSize)
    ))
}

#[test]
fn signed_too_small() {
    let too_small = b"dummy";

    assert!(matches!(
        VerifyKey::unsecure_unwrap(too_small),
        Err(CryptoError::Signature)
    ));

    let vk = VerifyKey::from(hex!(
        "78958e49abad190be2d51bab73af07f87682cfcd65cceedd27e4b2a94bfd8537"
    ));
    assert!(matches!(vk.verify(too_small), Err(CryptoError::Signature)));
}
