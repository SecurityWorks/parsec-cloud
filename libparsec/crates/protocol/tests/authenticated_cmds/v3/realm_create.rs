// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

// `allow-unwrap-in-test` don't behave as expected, see:
// https://github.com/rust-lang/rust-clippy/issues/11119
#![allow(clippy::unwrap_used)]

use libparsec_tests_lite::prelude::*;

use super::authenticated_cmds;

// Request

pub fn req() {
    // Generated from Python implementation (Parsec v2.6.0+dev)
    // Content:
    //   cmd: "realm_create"
    //   role_certificate: hex!("666f6f626172")
    let raw = hex!(
        "82a3636d64ac7265616c6d5f637265617465b0726f6c655f6365727469666963617465c406"
        "666f6f626172"
    );

    let req = authenticated_cmds::realm_create::Req {
        role_certificate: b"foobar".as_ref().into(),
    };

    let expected = authenticated_cmds::AnyCmdReq::RealmCreate(req);

    let data = authenticated_cmds::AnyCmdReq::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let authenticated_cmds::AnyCmdReq::RealmCreate(req2) = data else {
        unreachable!()
    };

    let raw2 = req2.dump().unwrap();

    let data2 = authenticated_cmds::AnyCmdReq::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

// Responses

pub fn rep_ok() {
    // Generated from Python implementation (Parsec v2.6.0+dev)
    // Content:
    //   status: "ok"
    let raw = hex!("81a6737461747573a26f6b");
    let expected = authenticated_cmds::realm_create::Rep::Ok;

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

pub fn rep_invalid_certification() {
    // Generated from Python implementation (Parsec v2.6.0+dev)
    // Content:
    //   reason: "foobar"
    //   status: "invalid_certification"
    let raw = hex!(
        "82a6726561736f6ea6666f6f626172a6737461747573b5696e76616c69645f636572746966"
        "69636174696f6e"
    );
    let expected = authenticated_cmds::realm_create::Rep::InvalidCertification {
        reason: Some("foobar".to_owned()),
    };

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

pub fn rep_invalid_data() {
    // Generated from Python implementation (Parsec v2.6.0+dev)
    // Content:
    //   reason: "foobar"
    //   status: "invalid_data"
    let raw = hex!("82a6726561736f6ea6666f6f626172a6737461747573ac696e76616c69645f64617461");

    let expected = authenticated_cmds::realm_create::Rep::InvalidData {
        reason: Some("foobar".to_owned()),
    };

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

pub fn rep_not_found() {
    // Generated from Python implementation (Parsec v2.6.0+dev)
    // Content:
    //   reason: "foobar"
    //   status: "not_found"
    let raw = hex!("82a6726561736f6ea6666f6f626172a6737461747573a96e6f745f666f756e64");

    let expected = authenticated_cmds::realm_create::Rep::NotFound {
        reason: Some("foobar".to_owned()),
    };

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

pub fn rep_already_exists() {
    // Generated from Python implementation (Parsec v2.6.0+dev)
    // Content:
    //   status: "already_exists"
    let raw = hex!("81a6737461747573ae616c72656164795f657869737473");

    let expected = authenticated_cmds::realm_create::Rep::AlreadyExists;

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

pub fn rep_bad_timestamp() {
    // Generated from Python implementation (Parsec v2.11.1+dev)
    // Content:
    //   status: "bad_timestamp"
    //
    // Note that raw data does not contain:
    //  - ballpark_client_early_offset
    //  - ballpark_client_late_offset
    //  - backend_timestamp
    //  - client_timestamp
    // This was valid behavior in api v2 but is no longer valid from v3 onwards.
    // The corresponding expected values used here are therefore not important
    // since loading raw data should fail.
    //
    let raw = hex!("81a6737461747573ad6261645f74696d657374616d70");

    let err = authenticated_cmds::realm_create::Rep::load(&raw).unwrap_err();
    let expected_err = rmp_serde::decode::Error::Syntax("missing field `backend_timestamp`".into());

    assert!(matches!(err, expected_err));

    // Generated from Python implementation (Parsec v2.11.1+dev)
    // Content:
    //   backend_timestamp: ext(1, 946774800.0)
    //   ballpark_client_early_offset: 50.0
    //   ballpark_client_late_offset: 70.0
    //   client_timestamp: ext(1, 946774800.0)
    //   status: "bad_timestamp"
    //
    let raw = hex!(
        "85b16261636b656e645f74696d657374616d70d70141cc375188000000bc62616c6c706172"
        "6b5f636c69656e745f6561726c795f6f6666736574cb4049000000000000bb62616c6c7061"
        "726b5f636c69656e745f6c6174655f6f6666736574cb4051800000000000b0636c69656e74"
        "5f74696d657374616d70d70141cc375188000000a6737461747573ad6261645f74696d6573"
        "74616d70"
    );

    let expected = authenticated_cmds::realm_create::Rep::BadTimestamp {
        reason: None,
        ballpark_client_early_offset: 50.,
        ballpark_client_late_offset: 70.,
        backend_timestamp: "2000-1-2T01:00:00Z".parse().unwrap(),
        client_timestamp: "2000-1-2T01:00:00Z".parse().unwrap(),
    };

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}

pub fn rep_require_greater_timestamp() {
    // Generated from Python implementation (Parsec v2.11.1+dev)
    // Content:
    //   status: "require_greater_timestamp"
    //   strictly_greater_than: ext(1, 946774800.0)
    //
    let raw = hex!(
        "82a6737461747573b9726571756972655f677265617465725f74696d657374616d70b57374"
        "726963746c795f677265617465725f7468616ed70141cc375188000000"
    );

    let expected = authenticated_cmds::realm_create::Rep::RequireGreaterTimestamp {
        strictly_greater_than: "2000-1-2T01:00:00Z".parse().unwrap(),
    };

    let data = authenticated_cmds::realm_create::Rep::load(&raw).unwrap();

    p_assert_eq!(data, expected);

    // Also test serialization round trip
    let raw2 = data.dump().unwrap();

    let data2 = authenticated_cmds::realm_create::Rep::load(&raw2).unwrap();

    p_assert_eq!(data2, expected);
}