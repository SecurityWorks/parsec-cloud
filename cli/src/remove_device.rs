// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use crate::utils::*;

#[derive(clap::Parser)]
pub struct RemoveDevice {
    #[clap(flatten)]
    config: ConfigWithDeviceSharedOpts,
}

pub async fn remove_device(remove_device: RemoveDevice) -> anyhow::Result<()> {
    let RemoveDevice {
        config: ConfigWithDeviceSharedOpts { config_dir, device },
    } = remove_device;
    log::trace!(
        "Removing device {device} (confdir={})",
        config_dir.display(),
        device = device.as_deref().unwrap_or("N/A")
    );

    load_device_file_and_run(config_dir, device, |device| async move {
        let short_id = &device.device_id.hex()[..3];
        let organization_id = &device.organization_id;
        let human_handle = &device.human_handle;
        let device_label = &device.device_label;

        println!("You are about to remove the following device:");
        println!("{YELLOW}{short_id}{RESET} - {organization_id}: {human_handle} @ {device_label}");
        println!("Are you sure? (y/n)");

        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;

        match input.trim() {
            "y" => {
                std::fs::remove_file(&device.key_file_path)?;
                println!("The device has been removed");
            }
            _ => eprintln!("Operation cancelled"),
        }

        Ok(())
    })
    .await
}
