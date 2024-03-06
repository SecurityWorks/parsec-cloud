// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::{path::PathBuf, sync::Arc};

use libparsec_client::{workspace::WorkspaceOps, Client};
use libparsec_tests_fixtures::prelude::*;
use libparsec_types::prelude::*;

use super::utils::mount_and_test;
use crate::Mountpoint;

#[parsec_test(testbed = "minimal_client_ready")]
async fn ok(tmp_path: TmpPath, env: &TestbedEnv) {
    mount_and_test!(
        env,
        &tmp_path,
        |_client: Arc<Client>, _wksp1_ops: Arc<WorkspaceOps>, mountpoint_path: PathBuf| async move {
            let mut children = vec![];
            let mut readdir = tokio::fs::read_dir(mountpoint_path).await.unwrap();
            while let Some(child) = readdir.next_entry().await.unwrap() {
                children.push(child.file_name());
            }

            p_assert_eq!(
                children,
                [std::ffi::OsStr::new("bar.txt"), std::ffi::OsStr::new("foo")]
            );
        }
    );
}

// FUSE typically uses readdir to read a block of 128 entries at a time.
#[parsec_test(testbed = "minimal_client_ready")]
async fn ok_lot_of_entries(tmp_path: TmpPath, env: &TestbedEnv) {
    mount_and_test!(
        env,
        &tmp_path,
        |_client: Arc<Client>, wksp1_ops: Arc<WorkspaceOps>, mountpoint_path: PathBuf| async move {
            for i in 0..1000 {
                let path = format!("/foo/spam/{}", i).parse().unwrap();
                wksp1_ops.create_file(path).await.unwrap();
            }

            let mut readdir = tokio::fs::read_dir(mountpoint_path.join("foo/spam"))
                .await
                .unwrap();
            let mut children = Vec::with_capacity(1000);
            while let Some(child) = readdir.next_entry().await.unwrap() {
                let file_index = child.file_name().to_str().unwrap().parse::<u64>().unwrap();
                children.push(file_index);
            }
            p_assert_eq!(
                children.len(),
                1000,
                "Expected 1000 entries, got {}",
                children.len()
            );
            children.sort();
            p_assert_eq!(children, (0..1000).collect::<Vec<_>>());
        }
    );
}

#[parsec_test(testbed = "minimal_client_ready")]
async fn not_found(tmp_path: TmpPath, env: &TestbedEnv) {
    mount_and_test!(
        env,
        &tmp_path,
        |_client: Arc<Client>, _wksp1_ops: Arc<WorkspaceOps>, mountpoint_path: PathBuf| async move {
            let err = tokio::fs::read_dir(mountpoint_path.join("dummy"))
                .await
                .unwrap_err();
            p_assert_matches!(err.kind(), std::io::ErrorKind::NotFound);
        }
    );
}

#[parsec_test(testbed = "minimal_client_ready")]
async fn is_file(tmp_path: TmpPath, env: &TestbedEnv) {
    mount_and_test!(
        env,
        &tmp_path,
        |_client: Arc<Client>, _wksp1_ops: Arc<WorkspaceOps>, mountpoint_path: PathBuf| async move {
            let err = tokio::fs::read_dir(mountpoint_path.join("bar.txt"))
                .await
                .unwrap_err();
            p_assert_eq!(err.raw_os_error(), Some(libc::ENOTDIR), "{}", err);
        }
    );
}

#[parsec_test(testbed = "minimal_client_ready")]
async fn stopped(tmp_path: TmpPath, env: &TestbedEnv) {
    mount_and_test!(
        env,
        &tmp_path,
        |client: Arc<Client>, wksp1_ops: Arc<WorkspaceOps>, mountpoint_path: PathBuf| async move {
            client.stop_workspace(wksp1_ops.realm_id()).await;

            let err = tokio::fs::read_dir(mountpoint_path.join("foo"))
                .await
                .unwrap_err();
            p_assert_eq!(err.raw_os_error(), Some(libc::EIO), "{}", err);
        }
    );
}

#[parsec_test(testbed = "minimal_client_ready")]
async fn offline(tmp_path: TmpPath, env: &TestbedEnv) {
    let env = env.customize(|builder| {
        // Ignore all events related to workspace local storage except for the
        // workspace manifest. This way we have a root containing entries, but
        // accessing them require to fetch data from the server.
        builder.filter_client_storage_events(|e| {
            !matches!(
                e,
                TestbedEvent::WorkspaceDataStorageFetchFileVlob(_)
                    | TestbedEvent::WorkspaceDataStorageFetchFolderVlob(_)
                    | TestbedEvent::WorkspaceCacheStorageFetchBlock(_)
                    | TestbedEvent::WorkspaceDataStorageLocalWorkspaceManifestUpdate(_)
                    | TestbedEvent::WorkspaceDataStorageLocalFolderManifestCreateOrUpdate(_)
                    | TestbedEvent::WorkspaceDataStorageLocalFileManifestCreateOrUpdate(_)
                    | TestbedEvent::WorkspaceDataStorageFetchRealmCheckpoint(_)
                    | TestbedEvent::WorkspaceDataStorageChunkCreate(_)
            )
        });
    });
    mount_and_test!(
        &env,
        &tmp_path,
        |_client: Arc<Client>, _wksp1_ops: Arc<WorkspaceOps>, mountpoint_path: PathBuf| async move {
            let err = tokio::fs::read_dir(mountpoint_path.join("foo"))
                .await
                .unwrap_err();
            // Cannot use `std::io::ErrorKind::HostUnreachable` as it is unstable
            p_assert_eq!(err.raw_os_error(), Some(libc::EHOSTUNREACH), "{}", err);
        }
    );
}
