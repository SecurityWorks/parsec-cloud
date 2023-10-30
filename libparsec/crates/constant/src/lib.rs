// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::{fmt::Display, sync::OnceLock};

pub enum Platform {
    Windows,
    Linux,
    MacOS,
    Android,
    Web,
}

/// Return the current platform the code is executed on.
pub const fn get_platform() -> Platform {
    match std::env::consts::OS.as_bytes() {
        b"linux" => Platform::Linux,
        b"macos" => Platform::MacOS,
        b"windows" => Platform::Windows,
        b"android" => Platform::Android,
        _ => {
            #[cfg(target_arch = "wasm32")]
            return Platform::Web;
            #[cfg(not(target_arch = "wasm32"))]
            panic!("Unknown platform");
        }
    }
}

impl Display for Platform {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Platform::Windows => "windows",
            Platform::Linux => "linux",
            Platform::MacOS => "macos",
            Platform::Android => "android",
            Platform::Web => "web",
        };

        f.write_str(s)
    }
}

pub const CLIENT_VERSION: &str = "2.16.0-a.0+dev";

static CLIENT_USER_AGENT: OnceLock<String> = OnceLock::new();

/// Return the user-agent that should be used when doing HTTP request.
pub fn get_client_user_agent() -> &'static str {
    CLIENT_USER_AGENT
        .get_or_init(|| {
            let platform = get_platform();
            format!("Parsec-Client/{CLIENT_VERSION}; {platform}")
        })
        .as_str()
}
