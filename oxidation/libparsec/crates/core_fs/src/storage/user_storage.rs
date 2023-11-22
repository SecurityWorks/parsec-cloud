// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

use std::{
    path::Path,
    sync::{Arc, Mutex},
};

use libparsec_platform_async::Mutex as AsyncMutex;
use libparsec_platform_storage::{Closable, ManifestStorage, NeedSyncEntries};
use libparsec_types::prelude::*;

use super::version::get_user_data_storage_db_relative_path;
use crate::{error::FSResult, FSError};

pub struct UserStorage<Data>
where
    Data: ManifestStorage + Send + Sync + Closable,
{
    pub device: Arc<LocalDevice>,
    pub user_manifest_id: EntryID,
    data_storage: Data,
    /// A lock that will be used to prevent concurrent update in [UserStorage::set_user_manifest].
    /// When updating the user manifest.
    lock_update_manifest: AsyncMutex<()>,
    /// Keep a copy of the user manifest to have it available at all time.
    /// (We don't rely on [ManifestStorage]'s cache since it can be cleared).
    user_manifest_copy: Mutex<LocalUserManifest>,
}

#[cfg(not(target_arch = "wasm32"))]
pub type UserStorageSpecialized =
    UserStorage<libparsec_platform_storage::sqlite::SqliteDataStorage>;

#[cfg(not(target_arch = "wasm32"))]
impl UserStorage<libparsec_platform_storage::sqlite::SqliteDataStorage> {
    pub async fn new(
        data_base_dir: &Path,
        device: Arc<LocalDevice>,
        user_manifest_id: EntryID,
    ) -> FSResult<Self> {
        let data_relative_path = get_user_data_storage_db_relative_path(&device);
        let data_storage = libparsec_platform_storage::sqlite::SqliteDataStorage::from_path(
            data_base_dir,
            &data_relative_path,
            libparsec_platform_storage::sqlite::VacuumMode::default(),
            device.clone(),
        )
        .await
        .map_err(libparsec_platform_storage::StorageError::from)?;
        let user_manifest =
            UserStorage::load_user_manifest(&data_storage, user_manifest_id, &device).await?;
        let user_storage = Self {
            device,
            user_manifest_id,
            data_storage,
            lock_update_manifest: AsyncMutex::new(()),
            user_manifest_copy: Mutex::new(user_manifest),
        };
        Ok(user_storage)
    }
}

impl<Data> UserStorage<Data>
where
    Data: ManifestStorage + Closable + Send + Sync,
{
    /// Close the connections to the databases.
    /// Provide a way to manually close those connections.
    /// In theory this is not needed given we always ask the manifest storage
    /// to flush manifests on disk (i.e. we never rely on cache-ahead-of-db feature).
    /// So it should be a noop compared to database close without cache flush that
    /// is done when [UserStorage] is dropped.
    pub async fn close_connections(&self) {
        self.data_storage.close().await
    }

    // Checkpoint Interface

    pub async fn get_realm_checkpoint(&self) -> i64 {
        self.data_storage.get_realm_checkpoint().await
    }

    pub async fn update_realm_checkpoint(
        &self,
        new_checkpoint: i64,
        changed_vlobs: Vec<(EntryID, i64)>,
    ) -> FSResult<()> {
        self.data_storage
            .update_realm_checkpoint(new_checkpoint, changed_vlobs)
            .await
            .map_err(FSError::from)
    }

    pub async fn get_need_sync_entries(&self) -> FSResult<NeedSyncEntries> {
        self.data_storage
            .get_need_sync_entries()
            .await
            .map_err(FSError::from)
    }

    // User manifest

    pub fn get_user_manifest(&self) -> LocalUserManifest {
        self.user_manifest_copy
            .lock()
            .expect("Mutex is poisoned")
            .clone()
    }

    async fn load_user_manifest(
        manifest_storage: &Data,
        user_manifest_id: EntryID,
        device: &LocalDevice,
    ) -> FSResult<LocalUserManifest> {
        match manifest_storage.get_manifest(user_manifest_id).await {
            Ok(LocalManifest::User(manifest)) => Ok(manifest),
            Ok(_) => panic!("User manifest id is used for something other than a user manifest"),
            // It is possible to lack the user manifest in local if our
            // device hasn't tried to access it yet (and we are not the
            // initial device of our user, in which case the user local db is
            // initialized with a non-speculative local manifest placeholder).
            // In such case it is easy to fall back on an empty manifest
            // which is a good enough approximation of the very first version
            // of the manifest (field `created` is invalid, but it will be
            // correction by the merge during sync).
            Err(_) => {
                let timestamp = device.now();
                let manifest = LocalUserManifest::new(
                    device.device_id.clone(),
                    timestamp,
                    Some(device.user_manifest_id),
                    true,
                );
                manifest_storage
                    .set_manifest(
                        user_manifest_id,
                        LocalManifest::User(manifest.clone()),
                        None,
                    )
                    .await?;
                Ok(manifest)
            }
        }
    }

    pub async fn set_user_manifest(&self, user_manifest: LocalUserManifest) -> FSResult<()> {
        assert_eq!(
            self.user_manifest_id, user_manifest.base.id,
            "UserManifest should have the same EntryID as registered in UserStorage"
        );

        // We must make sure `manifest_storage` and `user_manifest_copy` are modified
        // atomically (given the copy is a basically a convenient shortcut on `manifest_storage`).
        let update_guard = self.lock_update_manifest.lock().await;

        self.data_storage
            .set_manifest(
                self.user_manifest_id,
                LocalManifest::User(user_manifest.clone()),
                None,
            )
            .await?;
        *self.user_manifest_copy.lock().expect("Mutex is poisoned") = user_manifest;

        drop(update_guard);
        Ok(())
    }
}

pub async fn user_storage_non_speculative_init(
    data_base_dir: &Path,
    device: Arc<LocalDevice>,
) -> FSResult<()> {
    let data_relative_path = get_user_data_storage_db_relative_path(&device);
    let manifest_storage = libparsec_platform_storage::sqlite::SqliteDataStorage::from_path(
        data_base_dir,
        &data_relative_path,
        libparsec_platform_storage::sqlite::VacuumMode::default(),
        device.clone(),
    )
    .await
    .map_err(libparsec_platform_storage::StorageError::from)?;

    let timestamp = device.now();
    let manifest = LocalUserManifest::new(
        device.device_id.clone(),
        timestamp,
        Some(device.user_manifest_id),
        false,
    );

    manifest_storage
        .set_manifest(device.user_manifest_id, LocalManifest::User(manifest), None)
        .await?;
    manifest_storage.commit_deferred_manifest().await?;
    manifest_storage.close().await;

    Ok(())
}

#[cfg(test)]
mod tests {
    use libparsec_testbed::TestbedEnv;
    use libparsec_tests_fixtures::{parsec_test, timestamp};

    use super::*;

    // TODO: add tests for `user_storage_non_speculative_init`

    #[parsec_test(testbed = "minimal")]
    async fn user_storage(timestamp: DateTime, env: &TestbedEnv) {
        let alice = env.local_device("alice@dev1".parse().unwrap());
        let user_manifest_id = alice.user_manifest_id;

        let user_storage = UserStorage::new(&env.discriminant_dir, alice.clone(), user_manifest_id)
            .await
            .unwrap();

        user_storage.get_realm_checkpoint().await;
        user_storage
            .update_realm_checkpoint(64, vec![])
            .await
            .unwrap();
        user_storage.get_need_sync_entries().await.unwrap();

        let user_manifest = LocalUserManifest {
            base: UserManifest {
                author: alice.device_id.clone(),
                timestamp,
                id: user_manifest_id,
                version: 0,
                created: timestamp,
                updated: timestamp,
                last_processed_message: 0,
                workspaces: vec![],
            },
            need_sync: false,
            updated: timestamp,
            last_processed_message: 0,
            workspaces: vec![],
            speculative: false,
        };

        user_storage
            .set_user_manifest(user_manifest.clone())
            .await
            .unwrap();

        assert_eq!(user_storage.get_user_manifest(), user_manifest);
    }
}