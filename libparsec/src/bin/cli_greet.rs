// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

#![allow(clippy::unwrap_used)]

use clap::Parser;
use hex_literal::hex;
use std::{path::Path, sync::Arc};

use libparsec_client::{new_user_invitation, EventBus, UserGreetInitialCtx};
use libparsec_client_connection::{AuthenticatedCmds, ProxyConfig};
use libparsec_crypto::{PrivateKey, SecretKey, SigningKey};
use libparsec_types::{BackendOrganizationAddr, EntryID, LocalDevice, TimeProvider, UserProfile};

/// Simple cli to greet a device
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Url (e.g.: parsec://127.0.0.1:41905)
    #[arg(short, long)]
    url: String,
}

#[tokio::main]
async fn main() {
    let mut input = String::new();
    let args = Args::parse();

    let local_device = Arc::new(LocalDevice {
        organization_addr: BackendOrganizationAddr::from_any(&format!(
            "{}/Org1?no_ssl=true&rvk=NTZTUXJDBIXUPQI5SYSVLI3L2Q5GW3U2O7WCHIK5TXMONULHFCOAssss",
            args.url
        ))
        .unwrap(),
        device_id: "alice@dev1".parse().unwrap(),
        device_label: Some("My dev1 machine".parse().unwrap()),
        human_handle: Some("Alicey McAliceFace <alice@example.com>".parse().unwrap()),
        signing_key: SigningKey::from(hex!(
            "aa00000000000000000000000000000000000000000000000000000000000000"
        )),
        private_key: PrivateKey::from(hex!(
            "aa00000000000000000000000000000000000000000000000000000000000000"
        )),
        initial_profile: UserProfile::Admin,
        user_manifest_id: EntryID::from(0xf0000000000000000000000000000001u128.to_le_bytes()),
        user_manifest_key: SecretKey::from(hex!(
            "aa00000000000000000000000000000000000000000000000000000000000000"
        )),
        local_symkey: SecretKey::from(hex!(
            "aa00000000000000000000000000000000000000000000000000000000000000"
        )),
        time_provider: TimeProvider::default(),
    });

    let cmds = Arc::new(
        AuthenticatedCmds::new(
            Path::new("/parsec/testbed/0/Org1"),
            local_device.clone(),
            ProxyConfig::default(),
        )
        .unwrap(),
    );

    let (token, _status) = new_user_invitation(&cmds, "john@example.com".into(), false)
        .await
        .unwrap();

    println!("{token:?}");

    let ctx = UserGreetInitialCtx::new(local_device, cmds, EventBus::default(), token);

    // Step 1: wait peer
    let ctx = ctx.do_wait_peer().await.unwrap();

    // Step 2: wait peer trust
    println!("Communicate your SAS code: {}", ctx.greeter_sas());

    let ctx = ctx.do_wait_peer_trust().await.unwrap();

    // Step 3: signify trust
    println!("SAS codes:");
    for sas_code in ctx.generate_claimer_sas_choices(4) {
        println!("{sas_code}")
    }

    println!("Enter claimer SAS code:");
    input.clear();
    std::io::stdin().read_line(&mut input).unwrap();

    if input.trim() != ctx.claimer_sas().as_ref() {
        println!("Invalid SAS code");
        return;
    }

    let ctx = ctx.do_signify_trust().await.unwrap();

    // Step 4: get claim requests
    let ctx = ctx.do_get_claim_requests().await.unwrap();

    // Step 5: create new user
    let device_label = ctx.requested_device_label.clone();
    let human_handle = ctx.requested_human_handle.clone();
    println!(
        "Requested device label: {:?}",
        device_label
            .as_ref()
            .map(|x| x.to_string())
            .unwrap_or_default()
    );
    println!(
        "Requested human handle: {:?}",
        human_handle
            .as_ref()
            .map(|x| x.to_string())
            .unwrap_or_default()
    );

    println!("Accept ? (y/n)");
    loop {
        input.clear();
        std::io::stdin().read_line(&mut input).unwrap();

        match input.trim() {
            "y" => {
                break;
            }
            "n" => {
                println!("Invitation aborted");
                return;
            }
            _ => (),
        }
    }

    let profile;
    println!("Which profile ? (standard/outsider/admin)");
    loop {
        input.clear();
        std::io::stdin().read_line(&mut input).unwrap();

        match input.trim() {
            "standard" => {
                profile = UserProfile::Standard;
                break;
            }
            "outsider" => {
                profile = UserProfile::Outsider;
                break;
            }
            "admin" => {
                profile = UserProfile::Admin;
                break;
            }
            _ => (),
        }
    }

    ctx.do_create_new_user(device_label, human_handle, profile)
        .await
        .unwrap();
}
