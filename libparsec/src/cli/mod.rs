// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

mod list_devices;

use libparsec_types::AvailableDevice;

pub use list_devices::{list_devices, ListDevices};

const GREEN: &str = "\x1B[92m";
const RESET: &str = "\x1B[39m";
const YELLOW: &str = "\x1B[33m";

pub fn format_devices(devices: &[AvailableDevice]) {
    let n = devices.len();
    // Try to shorten the slughash to make it easier to work with
    let slug_len = 2 + (n + 1).ilog2() as usize;

    for device in devices {
        let slug = &device.slughash()[..slug_len];
        let organization_id = &device.organization_id;
        let human_handle = &device.human_handle;
        let device_label = &device.device_label;
        println!("{YELLOW}{slug}{RESET} - {organization_id}: {human_handle} @ {device_label}");
    }
}
