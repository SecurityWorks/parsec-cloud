// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

#![allow(clippy::unwrap_used)]

use clap::Parser;
use std::{path::PathBuf, sync::Arc};

use libparsec_client::{claimer_retrieve_info, ClientConfig};
use libparsec_client_connection::ProxyConfig;
use libparsec_types::{BackendInvitationAddr, HumanHandle};

/// Simple cli to greet a device
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Url (e.g.: parsec://127.0.0.1:41905)
    #[arg(short, long)]
    url: String,

    /// Invitation token (e.g.: 4e45cc21e7604af196173ff6c9184a1f)
    #[arg(short, long)]
    token: String,
}

#[tokio::main]
async fn main() {
    let mut input = String::new();
    let args = Args::parse();

    let path = PathBuf::from("/parsec/testbed/0/Org1");

    let addr = BackendInvitationAddr::from_any(&format!(
        "{}/Org1?no_ssl=true&action=claim_user&token={}",
        args.url, args.token
    ))
    .unwrap();

    let config = Arc::new(ClientConfig {
        config_dir: path.clone(),
        data_base_dir: path.clone(),
        mountpoint_base_dir: path,
        workspace_storage_cache_size: libparsec_client::WorkspaceStorageCacheSize::Default,
        proxy: ProxyConfig::default(),
    });

    // Step 0: retrieve info
    let ctx = claimer_retrieve_info(config, addr).await.unwrap();

    let ctx = match ctx {
        libparsec_client::UserOrDeviceClaimInitialCtx::User(ctx) => ctx,
        libparsec_client::UserOrDeviceClaimInitialCtx::Device(_) => unreachable!(),
    };

    // Step 1: wait peer
    let ctx = ctx.do_wait_peer().await.unwrap();

    // Step 2: signify trust
    println!("SAS codes:");
    for sas_code in ctx.generate_greeter_sas_choices(4) {
        println!("{sas_code}");
    }

    println!("Enter greeter SAS code:");
    input.clear();
    std::io::stdin().read_line(&mut input).unwrap();

    if input.trim() != ctx.greeter_sas().as_ref() {
        return;
    }

    let ctx = ctx.do_signify_trust().await.unwrap();

    // Step 3: wait peer trust
    println!("Communicate your SAS code: {}", ctx.claimer_sas());

    let ctx = ctx.do_wait_peer_trust().await.unwrap();

    println!("Enter device label:");
    input.clear();
    std::io::stdin().read_line(&mut input).unwrap();

    let device_label = match input.trim().parse() {
        Ok(data) => Some(data),
        Err(_) => None,
    };

    println!("Enter email:");
    input.clear();
    std::io::stdin().read_line(&mut input).unwrap();

    let email = input.trim().to_string();

    println!("Enter name:");
    input.clear();
    std::io::stdin().read_line(&mut input).unwrap();

    let name = input.trim();

    let human_handle = HumanHandle::new(&email, name).ok();

    // Step 4: claim user
    let ctx = ctx.do_claim_user(device_label, human_handle).await.unwrap();

    let key_file = ctx.get_default_key_file();
    println!("Key file generated at: {key_file:?}");
}
