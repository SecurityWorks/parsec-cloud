// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::{future::Future, path::PathBuf, sync::Arc};

use libparsec::{
    internal::{Client, EventBus},
    list_available_devices, load_device, AuthenticatedCmds, AvailableDevice, ClientConfig,
    DeviceAccessStrategy, DeviceFileType, DeviceLabel, HumanHandle, LocalDevice, Password,
    ProxyConfig, SASCode, UserProfile,
};
use spinners::{Spinner, Spinners, Stream};

/// Environment variable to set the Parsec config directory
/// Should not be confused with [`libparsec::PARSEC_BASE_CONFIG_DIR`]
pub const PARSEC_CONFIG_DIR: &str = "PARSEC_CONFIG_DIR";

#[derive(clap::Parser)]
pub(crate) struct ConfigSharedOpts {
    /// Parsec config directory
    #[arg(short, long, default_value_os_t = libparsec::get_default_config_dir(), env = PARSEC_CONFIG_DIR)]
    pub(crate) config_dir: PathBuf,
}

#[derive(clap::Parser)]
pub(crate) struct ConfigWithDeviceSharedOpts {
    /// Parsec config directory
    #[arg(short, long, default_value_os_t = libparsec::get_default_config_dir(), env = PARSEC_CONFIG_DIR)]
    pub(crate) config_dir: PathBuf,
    /// Device ID
    #[arg(short, long, env = "PARSEC_DEVICE_ID")]
    pub(crate) device: Option<String>,
}

#[derive(clap::Parser, Clone)]
pub(crate) struct ServerSharedOpts {
    /// Server address (e.g: parsec3://127.0.0.1:6770?no_ssl=true)
    #[arg(short, long, env = "PARSEC_SERVER_ADDR")]
    pub(crate) addr: libparsec::ParsecAddr,
    /// Administration token
    #[arg(short, long, env = "PARSEC_ADMINISTRATION_TOKEN")]
    pub(crate) token: String,
}

pub const GREEN: &str = "\x1B[92m";
pub const RED: &str = "\x1B[91m";
pub const RESET: &str = "\x1B[39m";
pub const YELLOW: &str = "\x1B[33m";

pub fn format_devices(devices: &[AvailableDevice]) {
    let n = devices.len();
    // Try to shorten the device ID to make it easier to work with
    let short_id_len = 2 + (n + 1).ilog2() as usize;

    for device in devices {
        let short_id = &device.device_id.hex()[..short_id_len];
        let organization_id = &device.organization_id;
        let human_handle = &device.human_handle;
        let device_label = &device.device_label;
        println!("{YELLOW}{short_id}{RESET} - {organization_id}: {human_handle} @ {device_label}");
    }
}

pub async fn load_device_file_and_run<F, Fut>(
    config_dir: PathBuf,
    device_short_id: Option<String>,
    function: F,
) -> anyhow::Result<()>
where
    F: FnOnce(AvailableDevice) -> Fut,
    Fut: Future<Output = anyhow::Result<()>>,
{
    let devices = list_available_devices(&config_dir).await;

    if let Some(device_short_id) = device_short_id {
        let mut possible_devices = vec![];

        for device in &devices {
            if device.device_id.hex().starts_with(&device_short_id) {
                possible_devices.push(device);
            }
        }

        match possible_devices.len() {
            0 => {
                println!("Device `{device_short_id}` not found, available devices:");
                format_devices(&devices);
            }
            1 => {
                function(possible_devices[0].clone()).await?;
            }
            _ => {
                println!("Multiple devices found for `{device_short_id}`:");
                format_devices(&devices);
            }
        }
    } else {
        println!("Error: Missing option '--device'\n");
        println!("Available devices:");
        format_devices(&devices);
    }

    Ok(())
}

pub async fn load_device_and_run<F, Fut>(
    config_dir: PathBuf,
    device_short_id: Option<String>,
    function: F,
) -> anyhow::Result<()>
where
    F: FnOnce(Arc<LocalDevice>) -> Fut,
    Fut: Future<Output = anyhow::Result<()>>,
{
    load_device_file_and_run(config_dir.clone(), device_short_id, |device| async move {
        let device = match device.ty {
            DeviceFileType::Keyring => {
                return Err(anyhow::anyhow!(
                    "Unsupported device file authentication `{:?}`",
                    device.ty
                ));
            }
            DeviceFileType::Password => {
                #[cfg(feature = "testenv")]
                let password = "test".to_string().into();
                #[cfg(not(feature = "testenv"))]
                let password = rpassword::prompt_password("password:")?.into();

                let access = DeviceAccessStrategy::Password {
                    key_file: device.key_file_path.clone(),
                    password,
                };

                // This will fail if the password is invalid, but also if the binary is compiled with fast crypto (see  libparsec_crypto)
                load_device(&config_dir, &access).await?
            }
            DeviceFileType::Smartcard => {
                let access = DeviceAccessStrategy::Smartcard {
                    key_file: device.key_file_path.clone(),
                };

                load_device(&config_dir, &access).await?
            }
            DeviceFileType::Recovery => {
                return Err(anyhow::anyhow!(
                    "Unsupported device file authentication `{:?}`",
                    device.ty
                ));
            }
        };

        function(device).await
    })
    .await
}

pub async fn load_cmds_and_run<F, Fut>(
    config_dir: PathBuf,
    device_short_id: Option<String>,
    function: F,
) -> anyhow::Result<()>
where
    F: FnOnce(AuthenticatedCmds, Arc<LocalDevice>) -> Fut,
    Fut: Future<Output = anyhow::Result<()>>,
{
    load_device_and_run(config_dir.clone(), device_short_id, |device| async move {
        let cmds =
            AuthenticatedCmds::new(&config_dir, device.clone(), ProxyConfig::new_from_env()?)?;

        function(cmds, device).await
    })
    .await
}

pub async fn load_client_and_run<F, Fut>(
    config_dir: PathBuf,
    device_short_id: Option<String>,
    function: F,
) -> anyhow::Result<()>
where
    F: FnOnce(Arc<Client>) -> Fut,
    Fut: Future<Output = anyhow::Result<()>>,
{
    load_device_and_run(config_dir, device_short_id, |device| async move {
        let client = Client::start(
            Arc::new(
                ClientConfig {
                    with_monitors: false,
                    ..Default::default()
                }
                .into(),
            ),
            EventBus::default(),
            device,
        )
        .await?;

        function(client).await
    })
    .await
}

pub fn start_spinner(text: String) -> Spinner {
    Spinner::with_stream(Spinners::Dots, text, Stream::Stdout)
}

pub fn choose_password() -> anyhow::Result<Password> {
    #[cfg(feature = "testenv")]
    return Ok("test".to_string().into());
    #[cfg(not(feature = "testenv"))]
    loop {
        let password = rpassword::prompt_password("Enter password for the new device:")?.into();
        let confirm_password = rpassword::prompt_password("Confirm password:")?.into();

        if password == confirm_password {
            return Ok(password);
        } else {
            eprintln!("Password mismatch")
        }
    }
}

pub fn choose_device_label(input: &mut String) -> anyhow::Result<DeviceLabel> {
    loop {
        println!("Enter device label:");
        input.clear();
        std::io::stdin().read_line(input)?;

        match input.trim().parse() {
            Ok(device_label) => return Ok(device_label),
            Err(e) => eprintln!("{e}"),
        }
    }
}

pub fn choose_human_handle(input: &mut String) -> anyhow::Result<HumanHandle> {
    loop {
        println!("Enter email:");
        input.clear();
        std::io::stdin().read_line(input)?;

        let email = input.trim().to_string();

        println!("Enter name:");
        input.clear();
        std::io::stdin().read_line(input)?;

        let name = input.trim();

        match HumanHandle::new(&email, name) {
            Ok(human_handle) => return Ok(human_handle),
            Err(e) => eprintln!("{e}"),
        }
    }
}

pub fn choose_sas_code(
    input: &mut String,
    sas_codes: &[SASCode],
    expected: &SASCode,
) -> anyhow::Result<()> {
    std::io::stdin().read_line(input)?;

    match sas_codes.get(input.trim().parse::<usize>()?) {
        Some(sas_code) if sas_code == expected => Ok(()),
        Some(_) => Err(anyhow::anyhow!("Invalid SAS code")),
        None => Err(anyhow::anyhow!("Invalid input")),
    }
}

pub fn choose_user_profile(input: &mut String) -> anyhow::Result<UserProfile> {
    println!("Which profile? (0, 1, 2)");
    println!(" 0 - {YELLOW}Standard{RESET}");
    println!(" 1 - {YELLOW}Admin{RESET}");
    println!(" 2 - {YELLOW}Outsider{RESET}");
    loop {
        input.clear();
        std::io::stdin().read_line(input)?;

        match input.trim() {
            "0" => return Ok(UserProfile::Standard),
            "1" => return Ok(UserProfile::Admin),
            "2" => return Ok(UserProfile::Outsider),
            _ => eprintln!("Invalid input, choose between 0, 1 or 2"),
        }
    }
}
