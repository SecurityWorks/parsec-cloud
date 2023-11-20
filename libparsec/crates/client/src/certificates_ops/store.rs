// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

//! The store is an intermediary layer between certificate ops and the storage.
//! It goals are twofold:
//! - handle a cache for the most common operations (e.g. retrieving device's verify key)
//!   and keep it consistent with the storage
//! - supervise read/write operations on the certificates
//!
//! Certificates being ordered, they are very dependant of each-other. Hence
//! we must prevent concurrent write operations to ensure inserting multiple
//! certificates is done in a atomic way.
//! On top of that, some read operations (the validation ones) work with the assumption
//! the storage contains all certificates up to a certain index. Here again we
//! need to prevent concurrent write operations (as it may remove certificates)

use std::{
    collections::HashMap,
    path::Path,
    sync::{Arc, Mutex},
};

use libparsec_platform_async::{
    lock::{RwLock, RwLockReadGuard, RwLockWriteGuard, Mutex as AsyncMutex, MutexGuard as AsyncMutexGuard}};
use libparsec_platform_storage::certificates::{CertificatesStorage, PerTopicLastTimestamps, CertificatesStorageUpdater, StorableCertificate};
pub use libparsec_platform_storage::certificates::{GetCertificateError, GetCertificateQuery, UpTo};
use libparsec_types::prelude::*;

#[derive(Debug, Default)]
enum ScalarCache<T> {
    #[default]
    Miss,
    Present(T),
}

impl<T> ScalarCache<T> {
    pub fn set(&mut self, new: T) -> Option<T> {
        match std::mem::replace(self, Self::Present(new)) {
            Self::Present(old) => Some(old),
            Self::Miss => None,
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum CertificateStorageOperationError {
    #[error("Certificate storage is stopped")]
    Stopped,
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

#[derive(Default, Debug)]
struct CurrentViewCache {
    pub per_topic_last_timestamps: ScalarCache<PerTopicLastTimestamps>,
    pub self_profile: ScalarCache<UserProfile>,
    pub per_user_profile: HashMap<UserID, UserProfile>,
    pub per_device_verify_key: HashMap<DeviceID, VerifyKey>,
}

impl CurrentViewCache {
    fn clear(&mut self) {
        *self = CurrentViewCache::default();
    }
}

#[derive(Debug)]
pub(crate) struct CertificatesStore {
    device: Arc<LocalDevice>,
    // Why 3 locks here ?
    // `lock` is the initial lock taken to exclude reads from write operations.
    // Once taken we first look in the `current_view_cache` and only then use `storage`
    // in case of cache miss.
    // Given accessing `storage` requires exclusive access, it's is better to have it
    // under it own lock so that all cache hit operations can occur concurrently.
    // On top of that, the cache must be behind its own lock (and not behind the main
    // read-write lock) so that it can be updated on cache miss even if we are in a
    // read operation.
    lock: RwLock<()>,
    current_view_cache: Mutex<CurrentViewCache>,
    // Set to `None` once stopped
    storage: AsyncMutex<Option<CertificatesStorage>>,
}

impl CertificatesStore {
    pub async fn start(data_base_dir: &Path, device: Arc<LocalDevice>) -> anyhow::Result<Self> {
        let storage = CertificatesStorage::start(data_base_dir, &device).await?;

        Ok(Self {
            device,
            lock: RwLock::default(),
            storage: AsyncMutex::new(Some(storage)),
            current_view_cache: Mutex::default(),
        })
    }

    pub async fn stop(&self) -> anyhow::Result<()> {
        let mut mutex = self.storage.lock().await;
        let maybe_storage = mutex.take();
        // Go idempotent if the storage is already stopped
        if let Some(storage) = maybe_storage {
            // Note the cache is never ahead of storage (i.e. it strictly constains
            // a subset of what's in the DB), hence no flush before stop is needed
            storage.stop().await?
        }
        Ok(())
    }

    pub async fn for_read(&self) -> CertificatesStoreReadGuard {
        let guard = self.lock.read().await;
        CertificatesStoreReadGuard {
            _guard: guard,
            store: self,
        }
    }

    pub async fn for_write<'a: 'b, 'b: 'c, 'c, T, E, Fut>(
        &'a self,
        cb: impl FnOnce(&'static mut CertificatesStoreWriteGuard) -> Fut,
    ) -> Result<Result<T, E>, CertificateStorageOperationError>
    where
        Fut: std::future::Future<Output = Result<T, E>>
    {
        let _guard = self.lock.write().await;

        let mut maybe_storage = self.storage.lock().await;
        let storage = match &mut *maybe_storage {
            None => return Err(CertificateStorageOperationError::Stopped),
            Some(storage) => storage,
        };
        let updater = storage.for_update().await?;

        let mut write_guard = CertificatesStoreWriteGuard{
            store: &self,
            updater,
        };

        unsafe fn pretend_static(src: &mut CertificatesStoreWriteGuard<'_>) -> &'static mut CertificatesStoreWriteGuard<'static> {
            std::mem::transmute(src)
        }
        // SAFETY: It is not currently possible to express the fact the lifetime
        // of a Future returned by a closure depends on the closure parameter if
        // they are references.
        // Here things are even worst because we have references coming from
        // `for_write` body and from `cb` closure (so workarounds as boxed future
        // don't work).
        // However in practice all our references have a lifetime bound to the
        // parent (i.e. `for_write`) or the grand-parent (i.e.
        // `CertificatesOps::add_certificates_batch`) which are going to poll this
        // future directly, so the references' lifetimes *are* long enough.
        // TODO: Remove this once async closure are available
        let static_write_guard_mut_ref = unsafe { pretend_static(&mut write_guard) };

        let fut = cb(static_write_guard_mut_ref);
        let outcome = fut.await;

        // The cache may have been updated during the write operations, and those new cache
        // entries might be for items that have been added by the current write operation.
        // If something goes wrong the database is rolledback, but this cannot be done
        // for the cache, so we simply clear it instead.
        let reset_cache = || {
            self.current_view_cache
                .lock()
                .expect("Mutex is poisoned !")
                .clear();
        };

        if outcome.is_ok() {
            // Commit the operations to database, without this the changes will
            // be rollback on drop.
            match write_guard.updater.commit().await {
                Err(commit_err) => {
                    reset_cache();
                    Err(commit_err.into())
                }
                Ok(_) => {
                    // Ok(Ok(...))
                    Ok(outcome)
                }
            }
        } else {
            reset_cache();
            // Ok(Err(...))
            Ok(outcome)
        }
    }
}

// #[cfg_attr(target_arch = "wasm32", async_trait(?Send))]
// #[cfg_attr(not(target_arch = "wasm32"), async_trait)]
// pub(crate) trait CertificatesStoreReadExt {
//     fn store(&self) -> &CertificatesStore;

//     async fn get_last_last_timestamps(&self) -> Result<PerTopicLastTimestamps, CertificateStorageOperationError> {
//         {
//             let guard = self
//                 .store()
//                 .current_view_cache
//                 .lock()
//                 .expect("Mutex is poisoned !");
//             if let ScalarCache::Present(last_timestamps) = &guard.per_topic_last_timestamps {
//                 return Ok(last_timestamps.to_owned());
//             }
//         }

//         // Cache miss !

//         let maybe_storage = self.store().storage.lock().await;
//         let storage = match &*maybe_storage {
//             None => return Err(CertificateStorageOperationError::Stopped),
//             Some(storage) => storage
//         };
//         let last_timestamps = storage.get_last_timestamps().await?;

//         let mut guard = self
//             .store()
//             .current_view_cache
//             .lock()
//             .expect("Mutex is poisoned !");

//         guard.per_topic_last_timestamps.set(last_timestamps.clone());

//         Ok(last_timestamps)
//     }

//     async fn get_current_self_profile(&self) -> anyhow::Result<UserProfile> {
//         let maybe_update = get_last_user_update_certificate(
//             self.store(),
//             UpTo::Current,
//             self.store().device.user_id().to_owned(),
//         )
//         .await?;
//         let profile = match maybe_update {
//             Some(update) => update.new_profile,
//             None => self.store().device.initial_profile,
//         };
//         Ok(profile)
//     }

//     async fn get_current_user_profile(
//         &self,
//         user_id: UserID,
//     ) -> Result<UserProfile, GetCertificateError> {
//         {
//             let guard = self
//                 .store()
//                 .current_view_cache
//                 .lock()
//                 .expect("Mutex is poisoned !");
//             if let Some(profile) = guard.per_user_profile.get(&user_id) {
//                 return Ok(*profile);
//             }
//         }

//         // Cache miss !

//         let profile = {
//             let maybe_user_update =
//                 get_last_user_update_certificate(self.store(), UpTo::Current, user_id.clone())
//                     .await?;
//             if let Some(user_update) = maybe_user_update {
//                 return Ok(user_update.new_profile);
//             }
//             // The user has never been modified
//             if user_id == *self.store().device.user_id() {
//                 self.store().device.initial_profile
//             } else {
//                 let certif =
//                     get_user_certificate(self.store(), UpTo::Current, user_id.clone()).await?;
//                 certif.profile
//             }
//         };
//         let mut guard = self
//             .store()
//             .current_view_cache
//             .lock()
//             .expect("Mutex is poisoned !");

//         guard.per_user_profile.insert(user_id, profile);

//         Ok(profile)
//     }

//     async fn get_timestamp_bounds(
//         &self,
//         index: IndexInt,
//     ) -> Result<(DateTime, Option<DateTime>), GetTimestampBoundsError> {
//         self.store().storage.get_timestamp_bounds(index).await
//     }

//     async fn get_any_certificate(
//         &self,
//         index: IndexInt,
//     ) -> Result<AnyArcCertificate, GetCertificateError> {
//         let data = self
//             .store()
//             .storage
//             .get_any_certificate_encrypted(index)
//             .await?;

//         let certif = data
//             .decrypt_and_load(&self.store().device.local_symkey)
//             .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

//         Ok(certif)
//     }

//     async fn get_user_certificate(
//         &self,
//         up_to: UpTo,
//         user_id: UserID,
//     ) -> Result<Arc<UserCertificate>, GetCertificateError> {
//         get_user_certificate(self.store(), up_to, user_id).await
//     }

//     async fn get_user_certificates(
//         &self,
//         up_to: UpTo,
//         offset: Option<usize>,
//         limit: Option<usize>,
//     ) -> anyhow::Result<Vec<Arc<UserCertificate>>> {
//         let query = GetCertificateQuery::users_certificates();
//         get_certificates(
//             self.store(),
//             query,
//             up_to,
//             offset,
//             limit,
//             UserCertificate::unsecure_load,
//             UnsecureUserCertificate::skip_validation,
//         )
//         .await
//     }

//     async fn get_last_user_update_certificate(
//         &self,
//         up_to: UpTo,
//         user_id: UserID,
//     ) -> anyhow::Result<Option<Arc<UserUpdateCertificate>>> {
//         get_last_user_update_certificate(self.store(), up_to, user_id).await
//     }

//     async fn get_device_certificate(
//         &self,
//         up_to: UpTo,
//         device_id: DeviceID,
//     ) -> Result<Arc<DeviceCertificate>, GetCertificateError> {
//         let query = GetCertificateQuery::device_certificate(device_id);
//         let (_, encrypted) = self
//             .store()
//             .storage
//             .get_certificate_encrypted(query, up_to)
//             .await?;

//         Ok(get_certificate_from_encrypted(
//             self.store(),
//             &encrypted,
//             DeviceCertificate::unsecure_load,
//             UnsecureDeviceCertificate::skip_validation,
//         )
//         .await?)
//     }

//     async fn get_user_devices_certificates(
//         &self,
//         up_to: UpTo,
//         user_id: UserID,
//     ) -> anyhow::Result<Vec<Arc<DeviceCertificate>>> {
//         let query = GetCertificateQuery::user_device_certificates(user_id);
//         get_certificates(
//             self.store(),
//             query,
//             up_to,
//             None,
//             None,
//             DeviceCertificate::unsecure_load,
//             UnsecureDeviceCertificate::skip_validation,
//         )
//         .await
//     }

//     async fn get_revoked_user_certificate(
//         &self,
//         up_to: UpTo,
//         user_id: UserID,
//     ) -> anyhow::Result<Option<Arc<RevokedUserCertificate>>> {
//         let query = GetCertificateQuery::revoked_user_certificate(user_id);
//         let encrypted = match self
//             .store()
//             .storage
//             .get_certificate_encrypted(query, up_to)
//             .await
//         {
//             Ok((_, encrypted)) => encrypted,
//             Err(
//                 GetCertificateError::NonExisting | GetCertificateError::ExistButTooRecent { .. },
//             ) => return Ok(None),
//             Err(GetCertificateError::Internal(err)) => return Err(err),
//         };

//         get_certificate_from_encrypted(
//             self.store(),
//             &encrypted,
//             RevokedUserCertificate::unsecure_load,
//             UnsecureRevokedUserCertificate::skip_validation,
//         )
//         .await
//         .map(Some)
//     }

//     async fn get_realm_roles(
//         &self,
//         up_to: UpTo,
//         realm_id: VlobID,
//     ) -> anyhow::Result<Vec<Arc<RealmRoleCertificate>>> {
//         let query = GetCertificateQuery::realm_role_certificates(realm_id);
//         get_certificates(
//             self.store(),
//             query,
//             up_to,
//             None,
//             None,
//             RealmRoleCertificate::unsecure_load,
//             UnsecureRealmRoleCertificate::skip_validation,
//         )
//         .await
//     }

//     async fn get_user_realm_role(
//         &self,
//         up_to: UpTo,
//         user_id: UserID,
//         realm_id: VlobID,
//     ) -> anyhow::Result<Option<Arc<RealmRoleCertificate>>> {
//         let query = GetCertificateQuery::realm_role_certificate(realm_id, user_id);
//         let encrypted = match self
//             .store()
//             .storage
//             .get_certificate_encrypted(query, up_to)
//             .await
//         {
//             Ok((_, encrypted)) => encrypted,
//             Err(
//                 GetCertificateError::NonExisting | GetCertificateError::ExistButTooRecent { .. },
//             ) => return Ok(None),
//             Err(GetCertificateError::Internal(err)) => return Err(err),
//         };

//         get_certificate_from_encrypted(
//             self.store(),
//             &encrypted,
//             RealmRoleCertificate::unsecure_load,
//             UnsecureRealmRoleCertificate::skip_validation,
//         )
//         .await
//         .map(Some)
//     }

//     async fn get_user_realms_roles(
//         &self,
//         up_to: UpTo,
//         user_id: UserID,
//     ) -> anyhow::Result<Vec<Arc<RealmRoleCertificate>>> {
//         let query = GetCertificateQuery::user_realm_role_certificates(user_id);
//         get_certificates(
//             self.store(),
//             query,
//             up_to,
//             None,
//             None,
//             RealmRoleCertificate::unsecure_load,
//             UnsecureRealmRoleCertificate::skip_validation,
//         )
//         .await
//     }

//     async fn get_sequester_authority_certificate(
//         &self,
//         up_to: UpTo,
//     ) -> Result<Arc<SequesterAuthorityCertificate>, GetCertificateError> {
//         let query = GetCertificateQuery::sequester_authority_certificate();
//         let (_, encrypted) = self
//             .store()
//             .storage
//             .get_certificate_encrypted(query, up_to)
//             .await?;

//         Ok(get_certificate_from_encrypted(
//             self.store(),
//             &encrypted,
//             SequesterAuthorityCertificate::unsecure_load,
//             UnsecureSequesterAuthorityCertificate::skip_validation,
//         )
//         .await?)
//     }

//     async fn get_sequester_service_certificates(
//         &self,
//         up_to: UpTo,
//     ) -> anyhow::Result<Vec<Arc<SequesterServiceCertificate>>> {
//         let query = GetCertificateQuery::sequester_service_certificates();
//         get_certificates(
//             self.store(),
//             query,
//             up_to,
//             None,
//             None,
//             SequesterServiceCertificate::unsecure_load,
//             UnsecureSequesterServiceCertificate::skip_validation,
//         )
//         .await
//     }
// }

pub(crate) struct CertificatesStoreReadGuard<'a> {
    _guard: RwLockReadGuard<'a, ()>,
    store: &'a CertificatesStore,
}

impl<'a> CertificatesStoreReadGuard<'a> {
    pub async fn get_last_timestamps(&self) -> Result<PerTopicLastTimestamps, CertificateStorageOperationError> {
        {
            let guard = self
                .store.current_view_cache
                .lock()
                .expect("Mutex is poisoned !");
            if let ScalarCache::Present(last_timestamps) = &guard.per_topic_last_timestamps {
                return Ok(last_timestamps.to_owned());
            }
        }

        // Cache miss !

        let mut maybe_storage = self.store.storage.lock().await;
        let storage = match &mut *maybe_storage {
            None => return Err(CertificateStorageOperationError::Stopped),
            Some(storage) => storage,
        };
        let last_timestamps = storage.get_last_timestamps().await?;

        let mut guard = self
            .store.current_view_cache
            .lock()
            .expect("Mutex is poisoned !");

        guard.per_topic_last_timestamps.set(last_timestamps.clone());

        Ok(last_timestamps)
    }
}


#[clippy::has_significant_drop]
pub(crate) struct CertificatesStoreWriteGuard<'a> {
    store: &'a CertificatesStore,
    updater: CertificatesStorageUpdater<'a>,
}

pub(crate) struct CertificatesStoreWriteGuard2<'a: 'b, 'b: 'c, 'c> {
    _guard: RwLockWriteGuard<'a, ()>,
    store: &'a CertificatesStore,
    maybe_storage_guard: Box<AsyncMutexGuard<'b, Option<CertificatesStorage>>>,
    storage_updater: CertificatesStorageUpdater<'c>,
}

impl<'a> CertificatesStoreWriteGuard<'a> {
    pub async fn forget_all_certificates(&mut self) -> anyhow::Result<()> {
        self.updater.forget_all_certificates().await?;
        self.store.current_view_cache
            .lock()
            .expect("Mutex is poisoned !")
            .clear();
        Ok(())
    }

    pub async fn add_next_common_certificate(
        &mut self,
        certif: CommonTopicArcCertificate,
        signed: &[u8]
    ) -> anyhow::Result<()> {
        let encrypted = self.store.device.local_symkey.encrypt(signed);

        let update_timestamp_cache = |cache: &mut CurrentViewCache, timestamp| {
            match &mut cache.per_topic_last_timestamps {
                ScalarCache::Present(last_timestamps) => last_timestamps.common = Some(timestamp),
                cache @ ScalarCache::Miss => {
                    cache.set(PerTopicLastTimestamps { common: Some(timestamp), sequester: None, realm: HashMap::default(), shamir: None });
                },
            }
        };

        match certif {
            CommonTopicArcCertificate::User(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;

                // Update cache

                let mut cache = self.store.current_view_cache.lock().expect("Mutex is poisoned");
                update_timestamp_cache(&mut *cache, certif.timestamp);
                cache.per_user_profile.insert(certif.user_id.clone(), certif.profile);
                if &certif.user_id == self.store.device.user_id() {
                    cache.self_profile.set(certif.profile);
                }
            },
            CommonTopicArcCertificate::Device(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;

                // Update cache

                let mut cache = self.store.current_view_cache.lock().expect("Mutex is poisoned");
                update_timestamp_cache(&mut *cache, certif.timestamp);
                cache.per_device_verify_key.insert(certif.device_id.clone(), certif.verify_key.clone());
            },
            CommonTopicArcCertificate::UserUpdate(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;

                // Update cache

                let mut cache = self.store.current_view_cache.lock().expect("Mutex is poisoned");
                update_timestamp_cache(&mut *cache, certif.timestamp);
                cache.per_user_profile.insert(certif.user_id.clone(), certif.new_profile);
                if &certif.user_id == self.store.device.user_id() {
                    cache.self_profile.set(certif.new_profile);
                }
            },
            CommonTopicArcCertificate::RevokedUser(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;

                // Update cache

                let mut cache = self.store.current_view_cache.lock().expect("Mutex is poisoned");
                update_timestamp_cache(&mut *cache, certif.timestamp);
            },
        }

        Ok(())
    }

    pub async fn add_next_realm_x_certificate(
        &mut self,
        certif: RealmTopicArcCertificate,
        signed: &[u8]
    ) -> anyhow::Result<()> {
        let encrypted = self.store.device.local_symkey.encrypt(signed);
        let (realm_id, timestamp) = match certif {
            RealmTopicArcCertificate::RealmRole(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;
                (certif.realm_id, certif.timestamp)
            },
        };

        let mut guard = self.store.current_view_cache.lock().expect("Mutex is poisoned");
        match &mut guard.per_topic_last_timestamps {
            ScalarCache::Present(last_timestamps) => {
                last_timestamps.realm.insert(realm_id, timestamp);
            },
            cache @ ScalarCache::Miss => {
                cache.set(PerTopicLastTimestamps {
                    common: None,
                    sequester: None,
                    realm: HashMap::from([(realm_id, timestamp)]),
                    shamir: None
                });
            },
        }

        Ok(())
    }

    pub async fn add_next_sequester_certificate(
        &mut self,
        certif: SequesterTopicArcCertificate,
        signed: &[u8]
    ) -> anyhow::Result<()> {
        let encrypted = self.store.device.local_symkey.encrypt(signed);
        let timestamp = match certif {
            SequesterTopicArcCertificate::SequesterAuthority(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;
                certif.timestamp
            },
            SequesterTopicArcCertificate::SequesterService(certif) => {
                self.updater.add_certificate(&*certif, encrypted).await?;
                certif.timestamp
            }
        };

        let mut guard = self.store.current_view_cache.lock().expect("Mutex is poisoned");
        match &mut guard.per_topic_last_timestamps {
            ScalarCache::Present(last_timestamps) => last_timestamps.sequester = Some(timestamp),
            cache @ ScalarCache::Miss => {
                cache.set(PerTopicLastTimestamps { common: None, sequester: Some(timestamp), realm: HashMap::default(), shamir: None });
            },
        }

        Ok(())
    }

    // pub async fn add_next_certificate<C: StorableCertificate>(
    //     &mut self,
    //     certif: &C,
    //     signed: &[u8],
    // ) -> anyhow::Result<()> {
    //     let encrypted = self.store.device.local_symkey.encrypt(signed);
    //     self.updater.add_certificate(certif, encrypted).await

    //     // let data = AddCertificateData::from_certif(certif, encrypted);
    //     // self.store.storage.add_next_certificate(index, data).await?;

    //     // // Update cache

    //     // let mut guard = self
    //     //     .store
    //     //     .current_view_cache
    //     //     .lock()
    //     //     .expect("Mutex is poisoned !");
    //     // guard.last_timestamp = ScalarCache::Miss;
    //     // match certif {
    //     //     AnyArcCertificate::User(certif) => {
    //     //         guard
    //     //             .per_user_profile
    //     //             .insert(certif.user_id.clone(), certif.profile);
    //     //     }
    //     //     AnyArcCertificate::UserUpdate(certif) => {
    //     //         guard
    //     //             .per_user_profile
    //     //             .insert(certif.user_id.clone(), certif.new_profile);
    //     //     }
    //     //     _ => (),
    //     // }

    //     Ok(())
    // }


    pub async fn get_current_self_profile(&mut self) -> anyhow::Result<UserProfile> {
        {
            let guard = self
                .store.current_view_cache
                .lock()
                .expect("Mutex is poisoned !");
            if let ScalarCache::Present(self_profile) = guard.self_profile {
                return Ok(self_profile);
            }
        }

        // Cache miss !

        let maybe_update = self.get_last_user_update_certificate(
            UpTo::Current,
            self.store.device.user_id().to_owned(),
        )
        .await?;
        let self_profile = match maybe_update {
            Some(update) => update.new_profile,
            None => self.store.device.initial_profile,
        };

        self
            .store.current_view_cache
            .lock()
            .expect("Mutex is poisoned !")
            .self_profile.set(self_profile);

        Ok(self_profile)
    }

    pub async fn get_last_timestamps(&mut self) -> anyhow::Result<PerTopicLastTimestamps> {
        {
            let guard = self
                .store.current_view_cache
                .lock()
                .expect("Mutex is poisoned !");
            if let ScalarCache::Present(last_timestamps) = &guard.per_topic_last_timestamps {
                return Ok(last_timestamps.to_owned());
            }
        }

        // Cache miss !

        let last_timestamps = self.updater.get_last_timestamps().await?;

        let mut guard = self
            .store.current_view_cache
            .lock()
            .expect("Mutex is poisoned !");

        guard.per_topic_last_timestamps.set(last_timestamps.clone());

        Ok(last_timestamps)
    }

    pub async fn get_device_verify_key(&mut self, up_to: UpTo, device_id: DeviceID) -> Result<VerifyKey, GetCertificateError> {
        let query = GetCertificateQuery::device_certificate(device_id);
        let (_, encrypted) = self
            .updater
            .get_certificate_encrypted(query, up_to)
            .await?;

        let certif = get_certificate_from_encrypted(
            self.store,
            &encrypted,
            DeviceCertificate::unsecure_load,
            UnsecureDeviceCertificate::skip_validation,
        )
        .await?;

        Ok(certif.verify_key.to_owned())
    }

    pub async fn get_user_certificate(&mut self, up_to: UpTo, user_id: UserID) -> Result<Arc<UserCertificate>, GetCertificateError> {
        let query = GetCertificateQuery::user_certificate(user_id);
        let (_, encrypted) = self
            .updater
            .get_certificate_encrypted(query, up_to)
            .await?;

        let certif = get_certificate_from_encrypted(
            self.store,
            &encrypted,
            UserCertificate::unsecure_load,
            UnsecureUserCertificate::skip_validation,
        )
        .await?;

        Ok(certif)
    }

    pub async fn get_device_certificate(
        &mut self,
        up_to: UpTo,
        device_id: DeviceID,
    ) -> Result<Arc<DeviceCertificate>, GetCertificateError> {
        let query = GetCertificateQuery::device_certificate(device_id);
        let (_, encrypted) = self
            .updater
            .get_certificate_encrypted(query, up_to)
            .await?;

        let certif = get_certificate_from_encrypted(
            self.store,
            &encrypted,
            DeviceCertificate::unsecure_load,
            UnsecureDeviceCertificate::skip_validation,
        )
        .await?;

        Ok(certif)
    }

    pub async fn get_revoked_user_certificate(&mut self, up_to: UpTo, user_id: UserID) -> anyhow::Result<Option<Arc<RevokedUserCertificate>>> {
        let query = GetCertificateQuery::user_certificate(user_id);
        let outcome = self
            .updater
            .get_certificate_encrypted(query, up_to)
            .await;

        let encrypted = match outcome {
            Ok((_, encrypted)) => encrypted,
            Err(GetCertificateError::NonExisting | GetCertificateError::ExistButTooRecent { .. }) => return Ok(None),
            Err(GetCertificateError::Internal(err)) => return Err(err),
        };

        get_certificate_from_encrypted(
            self.store,
            &encrypted,
            RevokedUserCertificate::unsecure_load,
            UnsecureRevokedUserCertificate::skip_validation,
        )
        .await
        .map(Some)
    }

    pub async fn get_last_user_update_certificate(
        &mut self,
        up_to: UpTo,
        user_id: UserID,
    ) -> anyhow::Result<Option<Arc<UserUpdateCertificate>>> {
        let query = GetCertificateQuery::user_update_certificates(user_id);
        // `get_certificate_encrypted` return the last certificate if multiple are available
        let outcome = self.updater.get_certificate_encrypted(query, up_to).await;
        let encrypted = match outcome {
            Ok((_, encrypted)) => encrypted,
            Err(GetCertificateError::NonExisting | GetCertificateError::ExistButTooRecent { .. }) => {
                return Ok(None)
            }
            Err(GetCertificateError::Internal(err)) => return Err(err),
        };

        let signed = self.store
            .device
            .local_symkey
            .decrypt(&encrypted)
            .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

        let unsecure = UserUpdateCertificate::unsecure_load(signed.into())
            .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

        let certif = unsecure.skip_validation(UnsecureSkipValidationReason::DataFromLocalStorage);

        Ok(Some(Arc::new(certif)))
    }


    pub async fn get_user_realms_roles(
        &mut self,
        up_to: UpTo,
        user_id: UserID,
    ) -> anyhow::Result<Vec<Arc<RealmRoleCertificate>>> {
        let query = GetCertificateQuery::user_realm_role_certificates(user_id);
        get_multiple_certificates(
            &self.store,
            &mut self.updater,
            query,
            up_to,
            None,
            None,
            RealmRoleCertificate::unsecure_load,
            UnsecureRealmRoleCertificate::skip_validation,
        ).await
    }

    pub async fn get_realm_roles(
        &mut self,
        up_to: UpTo,
        realm_id: VlobID,
    ) -> anyhow::Result<Vec<Arc<RealmRoleCertificate>>> {
        let query = GetCertificateQuery::realm_role_certificates(realm_id);
        get_multiple_certificates(
            &self.store,
            &mut self.updater,
            query,
            up_to,
            None,
            None,
            RealmRoleCertificate::unsecure_load,
            UnsecureRealmRoleCertificate::skip_validation,
        ).await
    }

    pub async fn get_sequester_authority_certificate(
        &mut self,
    ) -> anyhow::Result<Option<Arc<SequesterAuthorityCertificate>>> {
        let query = GetCertificateQuery::sequester_authority_certificate();
        let outcome = self
            .updater
            .get_certificate_encrypted(query, UpTo::Current)
            .await;
        let encrypted= match outcome {
            Ok((_, encrypted)) => encrypted,
            Err(GetCertificateError::NonExisting) => return Ok(None),
            Err(GetCertificateError::Internal(err)) => return Err(err),
            // Cannot get this error with `UpTo::Current`
            Err(GetCertificateError::ExistButTooRecent { .. }) => unreachable!(),
        };

        let certif = get_certificate_from_encrypted(
            self.store,
            &encrypted,
            SequesterAuthorityCertificate::unsecure_load,
            UnsecureSequesterAuthorityCertificate::skip_validation,
        )
        .await?;

        Ok(Some(certif))
    }

    pub async fn get_sequester_service_certificates(
        &mut self,
        up_to: UpTo,
    ) -> anyhow::Result<Vec<Arc<SequesterServiceCertificate>>> {
        let query = GetCertificateQuery::sequester_service_certificates();
        get_multiple_certificates(
            &self.store,
            &mut self.updater,
            query,
            up_to,
            None,
            None,
            SequesterServiceCertificate::unsecure_load,
            UnsecureSequesterServiceCertificate::skip_validation,
        )
        .await
    }
}

// pub struct CertificateStoreReadOperations<'a> {
//     store: &'a CertificatesStore,
// }

// impl<'a> CertificateStoreReadOperations<'a> {
//     pub async fn get_last_timestamps(&self) -> Result<PerTopicLastTimestamps, CertificateStorageOperationError> {
//         {
//             let guard = self
//                 .store
//                 .current_view_cache
//                 .lock()
//                 .expect("Mutex is poisoned !");
//             if let ScalarCache::Present(last_timestamps) = &guard.per_topic_last_timestamps {
//                 return Ok(last_timestamps.to_owned());
//             }
//         }

//         // Cache miss !

//         let mut maybe_storage = self.store.storage.lock().await;
//         let storage = match &mut *maybe_storage {
//             None => return Err(CertificateStorageOperationError::Stopped),
//             Some(storage) => storage
//         };
//         let last_timestamps = storage.get_last_timestamps().await?;

//         let mut guard = self
//             .store
//             .current_view_cache
//             .lock()
//             .expect("Mutex is poisoned !");

//         guard.per_topic_last_timestamps.set(last_timestamps.clone());

//         Ok(last_timestamps)
//     }
// }

// async fn get_user_certificate(
//     store: &CertificatesStore,
//     up_to: UpTo,
//     user_id: UserID,
// ) -> Result<Arc<UserCertificate>, GetCertificateError> {
//     let query = GetCertificateQuery::user_certificate(user_id);
//     let (_, encrypted) = store
//         .storage
//         .get_certificate_encrypted(query, up_to)
//         .await?;

//     let signed = store
//         .device
//         .local_symkey
//         .decrypt(&encrypted)
//         .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

//     let unsecure = UserCertificate::unsecure_load(signed.into())
//         .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

//     let certif = unsecure.skip_validation(UnsecureSkipValidationReason::DataFromLocalStorage);

//     Ok(Arc::new(certif))
// }

// async fn get_last_user_update_certificate(
//     store: &CertificatesStore,
//     up_to: UpTo,
//     user_id: UserID,
// ) -> anyhow::Result<Option<Arc<UserUpdateCertificate>>> {
//     let query = GetCertificateQuery::user_update_certificates(user_id);
//     // `get_certificate_encrypted` return the last certificate if multiple are available
//     let outcome = store.storage.get_certificate_encrypted(query, up_to).await;
//     let encrypted = match outcome {
//         Ok((_, encrypted)) => encrypted,
//         Err(GetCertificateError::NonExisting | GetCertificateError::ExistButTooRecent { .. }) => {
//             return Ok(None)
//         }
//         Err(GetCertificateError::Internal(err)) => return Err(err),
//     };

//     let signed = store
//         .device
//         .local_symkey
//         .decrypt(&encrypted)
//         .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

//     let unsecure = UserUpdateCertificate::unsecure_load(signed.into())
//         .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

//     let certif = unsecure.skip_validation(UnsecureSkipValidationReason::DataFromLocalStorage);

//     Ok(Some(Arc::new(certif)))
// }

async fn get_multiple_certificates<T, U>(
    store: &CertificatesStore,
    updater: &mut CertificatesStorageUpdater<'_>,
    query: GetCertificateQuery,
    up_to: UpTo,
    offset: Option<u32>,
    limit: Option<u32>,
    unsecure_load: fn(Bytes) -> DataResult<U>,
    skip_validation: fn(U, UnsecureSkipValidationReason) -> T,
) -> anyhow::Result<Vec<Arc<T>>> {
    let items = updater.get_multiple_certificates_encrypted(query, up_to, offset, limit).await?;

    let mut certifs = Vec::with_capacity(items.len());
    for (_, encrypted) in items {
        let certif =
            get_certificate_from_encrypted(store, &encrypted, unsecure_load, skip_validation)
                .await?;
        certifs.push(certif);
    }

    Ok(certifs)
}

async fn get_certificate_from_encrypted<T, U>(
    store: &CertificatesStore,
    encrypted: &[u8],
    unsecure_load: fn(Bytes) -> DataResult<U>,
    skip_validation: fn(U, UnsecureSkipValidationReason) -> T,
) -> anyhow::Result<Arc<T>> {
    let signed = store
        .device
        .local_symkey
        .decrypt(encrypted)
        .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

    let unsecure = unsecure_load(signed.into())
        .map_err(|e| anyhow::anyhow!("Local database contains invalid data: {}", e))?;

    let certif = skip_validation(unsecure, UnsecureSkipValidationReason::DataFromLocalStorage);

    Ok(Arc::new(certif))
}
