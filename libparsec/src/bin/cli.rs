// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use clap::{Parser, Subcommand};

use libparsec::cli::{InviteDevice, ListDevices};

/// Parsec cli
#[derive(Parser)]
struct Arg {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Create device invitation
    InviteDevice(InviteDevice),
    /// List all devices
    ListDevices(ListDevices),
}

#[tokio::main]
async fn main() {
    let arg = Arg::parse();

    match arg.command {
        Command::InviteDevice(invite_device) => libparsec::cli::invite_device(invite_device).await,
        Command::ListDevices(list_devices) => libparsec::cli::list_devices(list_devices).await,
    }
}
