// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use libparsec_client_connection::ConnectionError;
use libparsec_platform_storage::certificates::PerTopicLastTimestamps;
use libparsec_protocol::authenticated_cmds;
use libparsec_types::prelude::*;

use super::{
    store::{CertificatesStoreReadGuard, CertificateStorageOperationError}, AddCertificateError, CertificatesOps,
    InvalidCertificateError, MaybeRedactedSwitch,
};

#[derive(Debug, thiserror::Error)]
pub enum PollServerError {
    #[error("Cannot reach the server")]
    Offline,
    #[error("A certificate provided by the server is invalid: {0}")]
    InvalidCertificate(#[from] InvalidCertificateError),
    #[error("Certificate storage is stopped")]
    StorageStopped,
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

impl From<ConnectionError> for PollServerError {
    fn from(value: ConnectionError) -> Self {
        match value {
            ConnectionError::NoResponse(_) => Self::Offline,
            err => Self::Internal(err.into()),
        }
    }
}

impl From<AddCertificateError> for PollServerError {
    fn from(value: AddCertificateError) -> Self {
        match value {
            AddCertificateError::InvalidCertificate(err) => err.into(),
            AddCertificateError::StorageStopped => PollServerError::StorageStopped,
            AddCertificateError::Internal(err) => err.into(),
        }
    }
}

// pub(super) async fn ensure_certificates_available_and_read_lock(
//     ops: &CertificatesOps,
//     certificate_index: IndexInt,
// ) -> Result<CertificatesStoreReadGuard, PollServerError> {
//     loop {
//         poll_server_for_new_certificates(ops, Some(certificate_index)).await?;
//         let store = ops.store.for_read().await;
//         let last_index = store.get_last_certificate_timestamp().await?;
//         if last_index >= certificate_index {
//             return Ok(store);
//         }
//     }
// }

pub(super) async fn poll_server_for_new_certificates(
    ops: &CertificatesOps,
    latest_known_timestamps: Option<PerTopicLastTimestamps>,
) -> Result<(), PollServerError> {
    loop {
        // 1) Retrieve the last certificates timestamps when are currently aware of

        let last_stored_timestamps = ops
            .store
            .for_read()
            .await
            .get_last_timestamps()
            .await
            .map_err(|err| match err {
                CertificateStorageOperationError::Stopped => PollServerError::StorageStopped,
                CertificateStorageOperationError::Internal(e) => e.into(),
            })?;

        // `latest_known_timestamps` is useful to detect outdated `CertificatesUpdated`
        // events given the server has already been polled in the meantime.
        if let Some(latest_known_timestamps) = &latest_known_timestamps {
            if latest_known_timestamps.is_up_to_date(&last_stored_timestamps) {
                return Ok(())
            }
        }

        // 2) We are missing some certificates, time to ask the server about them...
        //
        // But first we must take the write lock so that certificate fetch from server
        // and add to storage are atomic. This is important to to avoid concurrency
        // access changing certificates and breaking the deterministic order certificates
        // must be added on.

        let outcome = ops.store.for_write(
            move |store| {
            async move {
                // 3) Fetch certificates

                // Last stored timestamp may have changed while we were waiting for the lock.
                let last_stored_timestamps = store.get_last_timestamps().await?;
                let request = authenticated_cmds::latest::certificate_get::Req {
                    common_after: last_stored_timestamps.common,
                    sequester_after: last_stored_timestamps.sequester,
                    shamir_after: last_stored_timestamps.shamir,
                    realm_after: last_stored_timestamps.realm,
                };
                let rep = ops.cmds.send(request).await?;
                let (common_certificates, realm_certificates, sequester_certificates, shamir_certificates) = match rep {
                    authenticated_cmds::latest::certificate_get::Rep::Ok { common_certificates, realm_certificates, sequester_certificates, shamir_certificates } => {
                        (common_certificates, realm_certificates, sequester_certificates, shamir_certificates)
                    },
                    authenticated_cmds::latest::certificate_get::Rep::UnknownStatus {
                        unknown_status,
                        ..
                    } => {
                        return Err(PollServerError::Internal(anyhow::anyhow!(
                            "Unknown error status `{}` from server",
                            unknown_status
                        )));
                    }
                };

                // 4) Integrate the new certificates.

                super::add::add_certificates_batch(
                    ops,
                    store,
                    &common_certificates,
                    &sequester_certificates,
                    &shamir_certificates,
                    &realm_certificates
                ).await.map_err(
                    |err| match err {
                        AddCertificateError::InvalidCertificate(err) => {
                            PollServerError::InvalidCertificate(err)
                        },
                        AddCertificateError::StorageStopped => PollServerError::StorageStopped,
                        AddCertificateError::Internal(err) => PollServerError::Internal(err),
                    }
                )
            }
        }).await.map_err(|err| match err {
            CertificateStorageOperationError::Stopped => AddCertificateError::StorageStopped,
            CertificateStorageOperationError::Internal(err) => err.into(),
        })??;

        match outcome {
            MaybeRedactedSwitch::NoSwitch => (),
            // Unlike other profiles, Outsider is required to use the redacted
            // certificates, hence our local certificate has been flushed and we
            // must go back to the server to get the all certificates from scratch.
            MaybeRedactedSwitch::Switched => continue,
        }

        return Ok(());
    }
}
