use std::sync::Arc;

use libparsec::{tmp_path, HumanHandle, RealmRole, TmpPath};

use super::bootstrap_cli_test;
use crate::utils::load_client;

#[rstest::rstest]
#[tokio::test]
// This test seems to fail because alice's device ID is no longer stable (it used
// to be a string, now it's a UUID regenerated at each run), hence the test process
// and the cli invocation process have different values for `alice.device_id.hex()` !
#[ignore = "TODO: fix this test !"]
async fn share_workspace(tmp_path: TmpPath) {
    let (_, [alice, bob, ..], _) = bootstrap_cli_test(&tmp_path).await.unwrap();

    // FIXME: The test should not rely on the load_client_and_run since it use the stdin to read the password to unlock the device.
    let client = load_client(
        &libparsec::get_default_config_dir(),
        Some(alice.device_id.to_string()),
        false,
    )
    .await
    .unwrap();
    let wid = client
        .create_workspace("new-workspace".parse().unwrap())
        .await
        .unwrap();
    client.ensure_workspaces_bootstrapped().await.unwrap();

    client.poll_server_for_new_certificates().await.unwrap();
    let users = client.list_users(false, None, None).await.unwrap();
    let bob_id = &users
        .iter()
        .find(|x| x.human_handle == HumanHandle::new("bob@example.com", "Bob").unwrap())
        .unwrap()
        .id;

    crate::assert_cmd_success!(
        "share-workspace",
        "--device",
        &alice.device_id.hex(),
        "--workspace-id",
        &wid.hex(),
        "--user-id",
        &bob_id.hex(),
        "--role",
        "contributor"
    )
    .stdout(predicates::str::contains("Workspace has been shared"));

    let client = libparsec::internal::Client::start(
        Arc::new(
            libparsec::ClientConfig {
                with_monitors: false,
                ..Default::default()
            }
            .into(),
        ),
        libparsec::internal::EventBus::default(),
        bob.clone(),
    )
    .await
    .unwrap();

    let workspaces = client.list_workspaces().await;

    let workspace_name = "new-workspace".parse().unwrap();
    assert!(
        workspaces
            .iter()
            .any(|w| w.current_name == workspace_name
                && w.current_self_role == RealmRole::Contributor)
    );
}
