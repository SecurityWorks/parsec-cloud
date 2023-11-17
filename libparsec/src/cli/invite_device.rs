// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use clap::Args;
use std::path::PathBuf;
use terminal_spinners::{SpinnerBuilder, DOTS};

use libparsec_client_connection::{AuthenticatedCmds, ProxyConfig};
use libparsec_platform_device_loader::load_device;
use libparsec_protocol::authenticated_cmds::latest::invite_new::{
    self, InviteNewRep, UserOrDevice,
};
use libparsec_types::{BackendInvitationAddr, DeviceAccessStrategy, InvitationType};

use crate::{cli::*, get_default_config_dir, list_available_devices};

#[derive(Args)]
pub struct InviteDevice {
    /// Parsec config directory
    #[arg(short, long)]
    config_dir: Option<PathBuf>,
    /// Device slughash
    #[arg(short, long)]
    device: Option<String>,
}

pub async fn invite_device(invite_device: InviteDevice) {
    let config_dir = invite_device.config_dir.unwrap_or(get_default_config_dir());
    let devices = list_available_devices(&config_dir).await;

    if let Some(device_slughash) = invite_device.device {
        let mut possible_devices = vec![];

        for device in &devices {
            if device.slughash().starts_with(&device_slughash) {
                possible_devices.push(device);
            }
        }

        match possible_devices.len() {
            0 => {
                println!("Device `{device_slughash}` not found, available devices:");
                format_devices(&devices);
            }
            2 => {
                println!("Multiple devices found for `{device_slughash}`:");
                format_devices(&devices);
            }
            _ => {
                let device = &possible_devices[0];

                let device = match device.ty {
                    libparsec_types::DeviceFileType::Password => {
                        let password = rpassword::prompt_password("password:")
                            .expect("Cannot prompt password")
                            .into();
                        let access = DeviceAccessStrategy::Password {
                            key_file: device.key_file_path.clone(),
                            password,
                        };

                        match load_device(&config_dir, &access).await {
                            Ok(device) => device,
                            Err(_) => {
                                // The password is invalid or the binary is compiled with fast crypto
                                println!("Invalid password");
                                return;
                            }
                        }
                    }
                    libparsec_types::DeviceFileType::Smartcard => {
                        let access = DeviceAccessStrategy::Smartcard {
                            key_file: device.key_file_path.clone(),
                        };

                        match load_device(&config_dir, &access).await {
                            Ok(device) => device,
                            Err(_) => {
                                println!("Invalid smartcard");
                                return;
                            }
                        }
                    }
                    libparsec_types::DeviceFileType::Recovery => {
                        println!("Unsupported device file authentication `{:?}`", device.ty);
                        return;
                    }
                };

                let cmds = AuthenticatedCmds::new(
                    &config_dir,
                    device.clone(),
                    ProxyConfig::new_from_env().expect("Invalid proxy env"),
                )
                .expect("Cannot create client");

                let handle = SpinnerBuilder::new()
                    .spinner(&DOTS)
                    .text("Creating device invitation")
                    .start();

                let rep = cmds
                    .send(invite_new::Req(UserOrDevice::Device { send_email: false }))
                    .await
                    .expect("Wrong protocol between client & server");

                let url = match rep {
                    InviteNewRep::Ok { token, .. } => BackendInvitationAddr::new(
                        device.organization_addr.clone(),
                        device.organization_id().clone(),
                        InvitationType::Device,
                        token,
                    )
                    .to_url(),
                    rep => {
                        println!("Backend refused to create device invitation: {rep:?}");
                        return;
                    }
                };

                handle.done();

                println!("url: {YELLOW}{url}{RESET}");
            }
        }
    } else {
        println!("Error: Missing option '--device'\n");
        println!("Available devices are:");
        format_devices(&devices);
    }
}
