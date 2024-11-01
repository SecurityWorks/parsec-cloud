// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use libparsec_client_connection::ConnectionError;
use libparsec_platform_storage::certificates::{GetCertificateError, UpTo};
use libparsec_protocol::authenticated_cmds::{
    latest::shamir_recovery_setup::{Rep, Req},
    v4::{
        device_create::{self},
        shamir_recovery_setup::ShamirRecoverySetup,
    },
};
use libparsec_types::{
    anyhow, shamir_make_shares, thiserror, Bytes, CertificateSignerOwned, DateTime,
    DeviceCertificate, DeviceLabel, InvitationToken, LocalDevice, MaybeRedacted, SecretKey,
    ShamirRecoveryBriefCertificate, ShamirRecoverySecret, ShamirRecoveryShareCertificate,
    ShamirRecoveryShareData, SigningKeyAlgorithm, UserID,
};
use std::{
    collections::{HashMap, HashSet},
    num::NonZeroU64,
    sync::Arc,
};

use crate::{
    CertificateBasedActionOutcome, CertificateOps, EventTooMuchDriftWithServerClock,
    InvalidCertificateError,
};

use super::{
    encrypt::CertifEncryptForUserError, greater_timestamp, CertifStoreError, GreaterTimestampOffset,
};

#[derive(Debug, thiserror::Error)]
pub enum CertifShamirSetupError {
    #[error("Component has stopped")]
    Stopped,
    #[error("Cannot reach the server")]
    Offline,
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

impl From<ConnectionError> for CertifShamirSetupError {
    fn from(value: ConnectionError) -> Self {
        match value {
            ConnectionError::NoResponse(_) => Self::Offline,
            // TODO: handle organization expired and user revoked here ?
            err => Self::Internal(err.into()),
        }
    }
}

impl From<CertifStoreError> for CertifShamirSetupError {
    fn from(value: CertifStoreError) -> Self {
        match value {
            CertifStoreError::Stopped => Self::Stopped,
            CertifStoreError::Internal(err) => err.into(),
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum CertifShamirError {
    #[error("Invalid threshold: it must be less that total share count")]
    InvalidThreshold,
    #[error("Author included as recipient")]
    AuthorIncludedAsRecipient,
    #[error("Shamir setup already exists: {0}")]
    ShamirSetupAlreadyExist(DateTime),
    #[error("Component has stopped")]
    Stopped,
    #[error("Cannot reach the server")]
    Offline,
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
    #[error("User {0} is revoked")]
    UserRevoked(UserID),
    #[error("Threshold is 0")]
    ThresholdIsZero,
    #[error("Share recipient declared in brief has no share certificate")]
    ShareRecipientHasZeroShares,
    #[error("User {0} not found.")]
    MissingUser(UserID),
    #[error("Our clock ({client_timestamp}) and the server's one ({server_timestamp}) are too far apart")]
    TimestampOutOfBallpark {
        server_timestamp: DateTime,
        client_timestamp: DateTime,
        ballpark_client_early_offset: f64,
        ballpark_client_late_offset: f64,
    },
    #[error(transparent)]
    InvalidCertificate(#[from] Box<InvalidCertificateError>),
    #[error(transparent)]
    DataError(#[from] libparsec_types::DataError),
    #[error(transparent)]
    EncryptionError(#[from] CertifEncryptForUserError),
    #[error(transparent)]
    GetCertificateError(#[from] GetCertificateError),
}

impl From<CertifStoreError> for CertifShamirError {
    fn from(value: CertifStoreError) -> Self {
        match value {
            CertifStoreError::Stopped => Self::Stopped,
            CertifStoreError::Internal(err) => err.into(),
        }
    }
}

impl From<ConnectionError> for CertifShamirError {
    fn from(value: ConnectionError) -> Self {
        match value {
            ConnectionError::NoResponse(_) => Self::Offline,
            // TODO: handle organization expired and user revoked here ?
            err => Self::Internal(err.into()),
        }
    }
}
pub(super) async fn shamir_setup_create(
    certificate_ops: &CertificateOps,
    share_recipients: HashMap<UserID, u8>,
    threshold: u8,
) -> Result<CertificateBasedActionOutcome, CertifShamirError> {
    // Keep looping while a RequireGreaterTimestamp is returned
    let mut recovery_device_timestamp = certificate_ops.device.now();
    let recovery_device = loop {
        let outcome =
            create_shamir_recovery_device(certificate_ops, recovery_device_timestamp).await?;

        match outcome {
            CreateShamirRecoveryDeviceOutcome::Done(recovery_device) => break recovery_device,
            CreateShamirRecoveryDeviceOutcome::RequireGreaterTimestamp(strictly_greater_than) => {
                recovery_device_timestamp = greater_timestamp(
                    &certificate_ops.device.time_provider,
                    GreaterTimestampOffset::User,
                    strictly_greater_than,
                );
            }
        }
    };

    // Keep looping while a RequireGreaterTimestamp is returned
    let mut recovery_setup_timestamp = certificate_ops.device.now();
    loop {
        let outcome = do_shamir_recovery_setup(
            certificate_ops,
            &recovery_device,
            &share_recipients,
            threshold,
            recovery_setup_timestamp,
        )
        .await?;

        match outcome {
            DoShamirRecoverySetupOutcome::Done(outcome) => return Ok(outcome),
            DoShamirRecoverySetupOutcome::RequireGreaterTimestamp(strictly_greater_than) => {
                recovery_setup_timestamp = greater_timestamp(
                    &certificate_ops.device.time_provider,
                    GreaterTimestampOffset::User,
                    strictly_greater_than,
                );
            }
        }
    }
}

#[derive(Debug)]
enum CreateShamirRecoveryDeviceOutcome {
    Done(LocalDevice),
    RequireGreaterTimestamp(DateTime),
}

async fn create_shamir_recovery_device(
    certificate_ops: &CertificateOps,
    timestamp: DateTime,
) -> Result<CreateShamirRecoveryDeviceOutcome, CertifShamirError> {
    let author = &certificate_ops.device;

    let recovery_device = LocalDevice::from_existing_device_for_user(
        &author.clone(),
        DeviceLabel::try_from(format!("shamir-recovery-{timestamp}").as_str())
            .expect("Invalid device label"),
    );

    let device_cert = DeviceCertificate {
        author: CertificateSignerOwned::User(author.device_id),
        timestamp,
        user_id: recovery_device.user_id,
        device_id: recovery_device.device_id,
        device_label: MaybeRedacted::Real(recovery_device.device_label.clone()),
        verify_key: recovery_device.verify_key(),
        algorithm: SigningKeyAlgorithm::Ed25519,
    };

    let device_certificate = device_cert.dump_and_sign(&author.signing_key).into();

    let redacted_device_cert = device_cert.into_redacted();

    let redacted_device_certificate = redacted_device_cert
        .dump_and_sign(&author.signing_key)
        .into();

    match certificate_ops
        .cmds
        .send(device_create::Req {
            device_certificate,
            redacted_device_certificate,
        })
        .await?
    {
        device_create::Rep::Ok => Ok(CreateShamirRecoveryDeviceOutcome::Done(recovery_device)),
        device_create::Rep::RequireGreaterTimestamp {
            strictly_greater_than,
        } =>
        // The retry is handled by the caller
        {
            Ok(CreateShamirRecoveryDeviceOutcome::RequireGreaterTimestamp(
                strictly_greater_than,
            ))
        }
        device_create::Rep::TimestampOutOfBallpark {
            server_timestamp,
            client_timestamp,
            ballpark_client_early_offset,
            ballpark_client_late_offset,
            ..
        } => {
            let event = EventTooMuchDriftWithServerClock {
                server_timestamp,
                ballpark_client_early_offset,
                ballpark_client_late_offset,
                client_timestamp,
            };
            certificate_ops.event_bus.send(&event);

            Err(CertifShamirError::TimestampOutOfBallpark {
                server_timestamp,
                client_timestamp,
                ballpark_client_early_offset,
                ballpark_client_late_offset,
            })
        }
        bad_rep @ (device_create::Rep::UnknownStatus { .. }
        | device_create::Rep::InvalidCertificate
        | device_create::Rep::DeviceAlreadyExists) => {
            Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
        }
    }
}

#[derive(Debug)]
enum DoShamirRecoverySetupOutcome {
    Done(CertificateBasedActionOutcome),
    RequireGreaterTimestamp(DateTime),
}

async fn do_shamir_recovery_setup(
    certificate_ops: &CertificateOps,
    recovery_device: &LocalDevice,
    share_recipients: &HashMap<UserID, u8>,
    threshold: u8,
    timestamp: DateTime,
) -> Result<DoShamirRecoverySetupOutcome, CertifShamirError> {
    let author_device_id = certificate_ops.device.device_id;
    let author_user_id = certificate_ops.device.user_id;

    // 1. Check if share_recipients and threshold are internally coherent
    let total_share_count: u8 = share_recipients.values().sum();
    if total_share_count < threshold {
        return Err(CertifShamirError::InvalidThreshold);
    }

    if share_recipients
        .keys()
        .any(|&recipient| recipient == author_user_id)
    {
        return Err(CertifShamirError::AuthorIncludedAsRecipient);
    }

    if threshold == 0 {
        return Err(CertifShamirError::ThresholdIsZero);
    }

    if share_recipients.values().any(|&v| v == 0) {
        return Err(CertifShamirError::ShareRecipientHasZeroShares);
    }

    // 2. Check for previous setup
    // TODO add option to force shamir creation
    if let Some(setup) =
        get_latest_shamir_setup_for_author(certificate_ops, &author_user_id, &timestamp).await?
    {
        return Err(CertifShamirError::ShamirSetupAlreadyExist(setup.timestamp));
    }

    // 3. Check recipients status

    let mut participants_id: HashSet<_> = share_recipients.keys().collect();
    participants_id.insert(&author_user_id);
    // TODO implement a get_users method instead of list_user (let the DB do its job)
    let participants = certificate_ops.list_users(true, None, None).await?;
    let participants = participants
        .iter()
        .filter(|info| participants_id.contains(&info.id));

    // no participant is missing
    for &&id in &participants_id {
        if !participants.clone().any(|info| info.id == id) {
            return Err(CertifShamirError::MissingUser(id));
        }
    }

    // no participant is revoked
    for info in participants {
        if info.revoked_on.is_some() {
            return Err(CertifShamirError::UserRevoked(info.id));
        }
    }

    // 4. Generate certificates

    let brief: Bytes = ShamirRecoveryBriefCertificate {
        author: author_device_id,
        timestamp,
        user_id: author_user_id,
        threshold: NonZeroU64::new(threshold.into()).expect("shamir threshold is zero"), // checked during the first step
        per_recipient_shares: share_recipients
            .iter()
            .map(|(&k, &v)| (k, NonZeroU64::new(v.into()).expect("Share count is zero")))
            .collect(),
    }
    .dump_and_sign(&certificate_ops.device.signing_key)
    .into();

    let data_key = SecretKey::generate();
    let reveal_token = InvitationToken::default();

    let ciphered_data = data_key.encrypt(&recovery_device.dump()).into();

    let shark_shares = shamir_make_shares(
        threshold,
        &ShamirRecoverySecret {
            data_key,
            reveal_token,
        }
        .dump()?,
        total_share_count.into(),
    );
    let mut idx = 0_usize;
    let mut shares = Vec::new();
    for (&share_recipient_id, &share_count) in share_recipients {
        let pub_key = &certificate_ops
            .store
            .for_read(|store| store.get_user_certificate(UpTo::Current, share_recipient_id))
            .await??
            .public_key;
        let ciphered_share = ShamirRecoveryShareData {
            weighted_share: shark_shares[idx..idx + share_count as usize].to_vec(),
        }
        .dump_and_encrypt_for(pub_key);

        idx += share_count as usize;
        let share = ShamirRecoveryShareCertificate {
            author: author_device_id,
            timestamp,
            user_id: author_user_id,
            recipient: share_recipient_id,
            ciphered_share,
        }
        .dump_and_sign(&certificate_ops.device.signing_key)
        .into();
        shares.push(share);
    }
    // 5. Send certificates

    let req = Req {
        setup: Some(ShamirRecoverySetup {
            brief,
            ciphered_data,
            reveal_token,
            shares,
        }),
    };
    let rep = certificate_ops.cmds.send(req).await?;

    match rep {
        Rep::Ok => Ok(DoShamirRecoverySetupOutcome::Done(
            CertificateBasedActionOutcome::Uploaded {
                certificate_timestamp: timestamp,
            },
        )),

        Rep::RequireGreaterTimestamp {
            strictly_greater_than,
        } => {
            // The retry is handled by the caller
            Ok(DoShamirRecoverySetupOutcome::RequireGreaterTimestamp(
                strictly_greater_than,
            ))
        }
        Rep::TimestampOutOfBallpark {
            server_timestamp,
            client_timestamp,
            ballpark_client_early_offset,
            ballpark_client_late_offset,
            ..
        } => {
            let event = EventTooMuchDriftWithServerClock {
                server_timestamp,
                ballpark_client_early_offset,
                ballpark_client_late_offset,
                client_timestamp,
            };
            certificate_ops.event_bus.send(&event);

            Err(CertifShamirError::TimestampOutOfBallpark {
                server_timestamp,
                client_timestamp,
                ballpark_client_early_offset,
                ballpark_client_late_offset,
            })
        }
        Rep::InvalidRecipient { user_id } => Err(CertifShamirError::MissingUser(user_id)),
        Rep::ShamirSetupAlreadyExists {
            last_shamir_certificate_timestamp,
        } => Err(CertifShamirError::ShamirSetupAlreadyExist(
            last_shamir_certificate_timestamp,
        )),
        bad_rep @ (Rep::BriefInvalidData { .. }
        | Rep::ShareInvalidData { .. }
        | Rep::UnknownStatus { .. }
        | Rep::DuplicateShareForRecipient
        | Rep::MissingShareForRecipient
        | Rep::ShareInconsistentTimestamp
        | Rep::ShareRecipientNotInBrief
        | Rep::AuthorIncludedAsRecipient) => {
            //
            Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
        }
    }
}

/// Takes a for_read lock
async fn get_latest_shamir_setup_for_author(
    certificate_ops: &CertificateOps,
    author_id: &UserID,
    timestamp: &DateTime,
) -> Result<Option<Arc<ShamirRecoveryBriefCertificate>>, CertifShamirError> {
    Ok(certificate_ops
        .store
        .for_read(|store| {
            store.get_last_shamir_recovery_brief_certificate_for_author(
                author_id,
                UpTo::Timestamp(*timestamp),
            )
        })
        .await??)
}
