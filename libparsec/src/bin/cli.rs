// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use clap::{Parser, Subcommand};

use libparsec::cli::ListDevices;

/// Parsec cli
#[derive(Parser)]
struct Arg {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// List all devices
    ListDevices(ListDevices),
}

#[tokio::main]
async fn main() {
    let arg = Arg::parse();

    match arg.command {
        Command::ListDevices(list_devices) => libparsec::cli::list_devices(list_devices).await,
    }
}
