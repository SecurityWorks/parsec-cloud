// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use libparsec_client_connection::{
    test_register_sequence_of_send_hooks, test_send_hook_vlob_read_batch,
};
use libparsec_tests_fixtures::prelude::*;
use libparsec_types::prelude::*;

use super::utils::{DataAccessStrategy, StartWorkspaceHistoryOpsError};
use crate::workspace_history::{WorkspaceHistoryFdStatError, WorkspaceHistoryFileStat};

#[parsec_test(testbed = "workspace_history")]
async fn ok(
    #[values(DataAccessStrategy::Server, DataAccessStrategy::RealmExport)]
    strategy: DataAccessStrategy,
    env: &TestbedEnv,
) {
    let wksp1_id: VlobID = *env.template.get_stuff("wksp1_id");
    let wksp1_bar_txt_id: VlobID = *env.template.get_stuff("wksp1_bar_txt_id");
    let wksp1_bar_txt_v1_timestamp: DateTime =
        *env.template.get_stuff("wksp1_bar_txt_v1_timestamp");
    let wksp1_bar_txt_v2_timestamp: DateTime =
        *env.template.get_stuff("wksp1_bar_txt_v2_timestamp");
    let ops = match strategy.start_workspace_history_ops(env).await {
        Ok(ops) => ops,
        Err(StartWorkspaceHistoryOpsError::RealmExportNotSupportedOnWeb) => return,
    };

    // 0) Open `bar.txt` v1 and v2

    if matches!(strategy, DataAccessStrategy::Server) {
        test_register_sequence_of_send_hooks!(
            &env.discriminant_dir,
            // Get back `/` manifest
            test_send_hook_vlob_read_batch!(env, at: wksp1_bar_txt_v1_timestamp, wksp1_id, wksp1_id),
            // Note workspace key bundle has already been loaded at workspace history ops startup
        );
    }
    ops.set_timestamp_of_interest(wksp1_bar_txt_v1_timestamp)
        .await
        .unwrap();

    if matches!(strategy, DataAccessStrategy::Server) {
        test_register_sequence_of_send_hooks!(
            &env.discriminant_dir,
            // Get back the `bar.txt` manifest @ wksp1_bar_txt_v1_timestamp
            test_send_hook_vlob_read_batch!(env, at: wksp1_bar_txt_v1_timestamp, wksp1_id, wksp1_bar_txt_id),
            // Note workspace key bundle has already been loaded at workspace history ops startup
        );
    }
    let fd_v1 = ops.open_file_by_id(wksp1_bar_txt_id).await.unwrap();

    if matches!(strategy, DataAccessStrategy::Server) {
        test_register_sequence_of_send_hooks!(
            &env.discriminant_dir,
            // Get back `/` manifest
            test_send_hook_vlob_read_batch!(env, at: wksp1_bar_txt_v2_timestamp, wksp1_id, wksp1_id),
            // Note workspace key bundle has already been loaded at workspace history ops startup
        );
    }
    ops.set_timestamp_of_interest(wksp1_bar_txt_v2_timestamp)
        .await
        .unwrap();

    if matches!(strategy, DataAccessStrategy::Server) {
        test_register_sequence_of_send_hooks!(
            &env.discriminant_dir,
            // 1) Get back the `bar.txt` manifest
            test_send_hook_vlob_read_batch!(env, at: wksp1_bar_txt_v2_timestamp, wksp1_id, wksp1_bar_txt_id),
            // (workspace keys bundle already fetched)
        );
    }
    let fd_v2 = ops.open_file_by_id(wksp1_bar_txt_id).await.unwrap();

    // 1) Access bar.txt's v1

    p_assert_matches!(
        ops.fd_stat(fd_v1).await.unwrap(),
        WorkspaceHistoryFileStat {
            id,
            created,
            updated,
            version,
            size,
        } if {
            p_assert_eq!(id, wksp1_bar_txt_id);
            p_assert_eq!(created, "2000-01-10T00:00:00Z".parse().unwrap());
            p_assert_eq!(updated, "2000-01-10T00:00:00Z".parse().unwrap());
            p_assert_eq!(version, 1);
            p_assert_eq!(size, 8);
            true
        }
    );

    // 2) Access bar.txt's v2

    p_assert_matches!(
        ops.fd_stat(fd_v2).await.unwrap(),
        WorkspaceHistoryFileStat {
            id,
            created,
            updated,
            version,
            size,
        } if {
            p_assert_eq!(id, wksp1_bar_txt_id);
            p_assert_eq!(created, "2000-01-18T00:00:00Z".parse().unwrap());
            p_assert_eq!(updated, "2000-01-18T00:00:00Z".parse().unwrap());
            p_assert_eq!(version, 2);
            p_assert_eq!(size, 14);
            true
        }
    );

    ops.fd_close(fd_v1).unwrap();
    ops.fd_close(fd_v2).unwrap();
}

#[parsec_test(testbed = "workspace_history")]
async fn bad_file_descriptor(
    #[values(DataAccessStrategy::Server, DataAccessStrategy::RealmExport)]
    strategy: DataAccessStrategy,
    env: &TestbedEnv,
) {
    let ops = match strategy.start_workspace_history_ops(env).await {
        Ok(ops) => ops,
        Err(StartWorkspaceHistoryOpsError::RealmExportNotSupportedOnWeb) => return,
    };

    p_assert_matches!(
        ops.fd_stat(FileDescriptor(42)).await.unwrap_err(),
        WorkspaceHistoryFdStatError::BadFileDescriptor
    );
}

#[parsec_test(testbed = "workspace_history")]
async fn reuse_after_close(
    #[values(DataAccessStrategy::Server, DataAccessStrategy::RealmExport)]
    strategy: DataAccessStrategy,
    env: &TestbedEnv,
) {
    let wksp1_id: VlobID = *env.template.get_stuff("wksp1_id");
    let wksp1_bar_txt_id: VlobID = *env.template.get_stuff("wksp1_bar_txt_id");
    let wksp1_v2_timestamp: DateTime = *env.template.get_stuff("wksp1_v2_timestamp");
    let ops = match strategy
        .start_workspace_history_ops_at(env, wksp1_v2_timestamp)
        .await
    {
        Ok(ops) => ops,
        Err(StartWorkspaceHistoryOpsError::RealmExportNotSupportedOnWeb) => return,
    };

    if matches!(strategy, DataAccessStrategy::Server) {
        test_register_sequence_of_send_hooks!(
            &env.discriminant_dir,
            // Get back the `bar.txt` manifest
            test_send_hook_vlob_read_batch!(env, at: ops.timestamp_of_interest(), wksp1_id, wksp1_bar_txt_id),
            // Note workspace key bundle has already been loaded at workspace history ops startup
        );
    }

    let fd = ops.open_file_by_id(wksp1_bar_txt_id).await.unwrap();
    ops.fd_close(fd).unwrap();

    p_assert_matches!(
        ops.fd_stat(fd).await.unwrap_err(),
        WorkspaceHistoryFdStatError::BadFileDescriptor
    );
}
