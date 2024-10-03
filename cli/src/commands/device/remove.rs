// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use libparsec::AvailableDevice;
use libparsec_client::remove_device;

use crate::utils::*;

crate::clap_parser_with_shared_opts_builder!(
    #[with = config_dir, device]
    pub struct Args {}
);

pub async fn main(args: Args) -> anyhow::Result<()> {
    let Args { device, config_dir } = args;
    log::trace!(
        "Removing device {} (confdir={})",
        device.as_deref().unwrap_or("N/A"),
        config_dir.display(),
    );

    // FIXME: https://github.com/Scille/parsec-cloud/issues/8604
    // The client config should be loaded from a config file
    let config = libparsec_client::ClientConfig::from(libparsec::ClientConfig {
        config_dir,
        ..Default::default()
    });

    let device = load_device_file(&config.config_dir, device).await?;

    let short_id = &device.device_id.hex()[..3];
    let AvailableDevice {
        organization_id,
        human_handle,
        device_label,
        ..
    } = &device;

    println!("You are about to remove the following device:");
    println!("{YELLOW}{short_id}{RESET} - {organization_id}: {human_handle} @ {device_label}");
    println!("Are you sure? (y/n)");

    let mut input = String::new();
    std::io::stdin().read_line(&mut input)?;

    match input.trim() {
        "y" => {
            remove_device(&config, &device).await?;
            println!("The device has been removed");
        }
        _ => eprintln!("Operation cancelled"),
    }

    Ok(())
}
