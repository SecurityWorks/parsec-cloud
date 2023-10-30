// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use libparsec_constant::*;

fn raw_expected_platform() -> &'static str {
    #[cfg(not(target_arch = "wasm32"))]
    return std::env::consts::OS;
    #[cfg(target_arch = "wasm32")]
    return "web";
}

#[test]
fn current_platform() {
    assert_eq!(get_platform().to_string(), raw_expected_platform())
}

#[test]
fn user_agent() {
    assert_eq!(
        get_client_user_agent(),
        format!(
            "Parsec-Client/{}; {}",
            CLIENT_VERSION,
            raw_expected_platform()
        )
    )
}
