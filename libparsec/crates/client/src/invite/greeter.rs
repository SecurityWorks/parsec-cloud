// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

use std::sync::Arc;

use libparsec_client_connection::{
    protocol::authenticated_cmds, AuthenticatedCmds, ConnectionError,
};
use libparsec_types::prelude::*;

use crate::{EventBus, EventTooMuchDriftWithServerClock};

#[derive(Debug, thiserror::Error)]
pub enum GreetInProgressError {
    #[error("Cannot reach the server")]
    Offline,
    #[error("Invitation not found")]
    NotFound,
    #[error("Invitation already used")]
    AlreadyUsed,
    #[error("Greet operation reset by peer")]
    PeerReset,
    #[error("Active users limit reached")]
    ActiveUsersLimitReached,
    #[error("Claimer's nonce and hashed nonce don't match")]
    NonceMismatch,
    #[error("User already exists")]
    UserAlreadyExists,
    #[error("Device already exists")]
    DeviceAlreadyExists,
    #[error("Not allowed to create a user")]
    UserCreateNotAllowed,
    #[error(transparent)]
    CorruptedInviteUserData(DataError),
    #[error("Our clock ({client_timestamp}) and the server's one ({server_timestamp}) are too far apart")]
    BadTimestamp {
        server_timestamp: DateTime,
        client_timestamp: DateTime,
        ballpark_client_early_offset: f64,
        ballpark_client_late_offset: f64,
    },
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

impl From<ConnectionError> for GreetInProgressError {
    fn from(value: ConnectionError) -> Self {
        match value {
            ConnectionError::NoResponse(_) => Self::Offline,
            err => Self::Internal(err.into()),
        }
    }
}

// GreetInitialCtx

#[derive(Debug)]
struct BaseGreetInitialCtx {
    token: InvitationToken,
    cmds: Arc<AuthenticatedCmds>,
    event_bus: EventBus,
}

impl BaseGreetInitialCtx {
    async fn do_wait_peer(self) -> Result<BaseGreetInProgress1Ctx, GreetInProgressError> {
        let greeter_private_key = PrivateKey::generate();

        let claimer_public_key = {
            use authenticated_cmds::latest::invite_1_greeter_wait_peer::{Rep, Req};

            let rep = self
                .cmds
                .send(Req {
                    greeter_public_key: greeter_private_key.public_key(),
                    token: self.token,
                })
                .await?;

            match rep {
                Rep::Ok { claimer_public_key } => Ok(claimer_public_key),
                Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
                Rep::InvalidState => Err(GreetInProgressError::PeerReset),
                Rep::NotFound => Err(GreetInProgressError::NotFound),
                bad_rep @ Rep::UnknownStatus { .. } => {
                    Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
                }
            }?
        };

        let shared_secret_key = greeter_private_key.generate_shared_secret_key(&claimer_public_key);
        let greeter_nonce: Bytes = generate_nonce().into();

        let claimer_hashed_nonce = {
            use authenticated_cmds::latest::invite_2a_greeter_get_hashed_nonce::{Rep, Req};

            let rep = self.cmds.send(Req { token: self.token }).await?;

            match rep {
                Rep::Ok {
                    claimer_hashed_nonce,
                } => Ok(claimer_hashed_nonce),
                Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
                Rep::InvalidState => Err(GreetInProgressError::PeerReset),
                Rep::NotFound => Err(GreetInProgressError::NotFound),
                bad_rep @ Rep::UnknownStatus { .. } => {
                    Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
                }
            }?
        };

        let claimer_nonce = {
            use authenticated_cmds::latest::invite_2b_greeter_send_nonce::{Rep, Req};

            let rep = self
                .cmds
                .send(Req {
                    greeter_nonce: greeter_nonce.clone(),
                    token: self.token,
                })
                .await?;

            match rep {
                Rep::Ok { claimer_nonce } => Ok(claimer_nonce),
                Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
                Rep::InvalidState => Err(GreetInProgressError::PeerReset),
                Rep::NotFound => Err(GreetInProgressError::NotFound),
                bad_rep @ Rep::UnknownStatus { .. } => {
                    Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
                }
            }?
        };

        if HashDigest::from_data(&claimer_nonce) != claimer_hashed_nonce {
            return Err(GreetInProgressError::NonceMismatch);
        }

        let (claimer_sas, greeter_sas) =
            SASCode::generate_sas_codes(&claimer_nonce, greeter_nonce.as_ref(), &shared_secret_key);

        Ok(BaseGreetInProgress1Ctx {
            token: self.token,
            greeter_sas,
            claimer_sas,
            shared_secret_key,
            cmds: self.cmds,
            event_bus: self.event_bus,
        })
    }
}

#[derive(Debug)]
pub struct UserGreetInitialCtx(BaseGreetInitialCtx);

impl UserGreetInitialCtx {
    pub fn new(cmds: Arc<AuthenticatedCmds>, event_bus: EventBus, token: InvitationToken) -> Self {
        Self(BaseGreetInitialCtx {
            cmds,
            token,
            event_bus,
        })
    }

    pub async fn do_wait_peer(self) -> Result<UserGreetInProgress1Ctx, GreetInProgressError> {
        self.0.do_wait_peer().await.map(UserGreetInProgress1Ctx)
    }
}

#[derive(Debug)]
pub struct DeviceGreetInitialCtx(BaseGreetInitialCtx);

impl DeviceGreetInitialCtx {
    pub fn new(cmds: Arc<AuthenticatedCmds>, event_bus: EventBus, token: InvitationToken) -> Self {
        Self(BaseGreetInitialCtx {
            cmds,
            token,
            event_bus,
        })
    }

    pub async fn do_wait_peer(self) -> Result<DeviceGreetInProgress1Ctx, GreetInProgressError> {
        self.0.do_wait_peer().await.map(DeviceGreetInProgress1Ctx)
    }
}

// GreetInProgress1Ctx

#[derive(Debug)]
struct BaseGreetInProgress1Ctx {
    token: InvitationToken,
    greeter_sas: SASCode,
    claimer_sas: SASCode,
    shared_secret_key: SecretKey,
    cmds: Arc<AuthenticatedCmds>,
    event_bus: EventBus,
}

impl BaseGreetInProgress1Ctx {
    async fn do_wait_peer_trust(self) -> Result<BaseGreetInProgress2Ctx, GreetInProgressError> {
        use authenticated_cmds::latest::invite_3a_greeter_wait_peer_trust::{Rep, Req};

        let rep = self.cmds.send(Req { token: self.token }).await?;

        match rep {
            Rep::Ok => Ok(BaseGreetInProgress2Ctx {
                token: self.token,
                claimer_sas: self.claimer_sas,
                shared_secret_key: self.shared_secret_key,
                cmds: self.cmds,
                event_bus: self.event_bus,
            }),
            Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
            Rep::InvalidState => Err(GreetInProgressError::PeerReset),
            Rep::NotFound => Err(GreetInProgressError::NotFound),
            bad_rep @ Rep::UnknownStatus { .. } => {
                Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
            }
        }
    }
}

#[derive(Debug)]
pub struct UserGreetInProgress1Ctx(BaseGreetInProgress1Ctx);

impl UserGreetInProgress1Ctx {
    pub fn greeter_sas(&self) -> &SASCode {
        &self.0.greeter_sas
    }

    pub async fn do_wait_peer_trust(self) -> Result<UserGreetInProgress2Ctx, GreetInProgressError> {
        self.0
            .do_wait_peer_trust()
            .await
            .map(UserGreetInProgress2Ctx)
    }
}

#[derive(Debug)]
pub struct DeviceGreetInProgress1Ctx(BaseGreetInProgress1Ctx);

impl DeviceGreetInProgress1Ctx {
    pub fn greeter_sas(&self) -> &SASCode {
        &self.0.greeter_sas
    }

    pub async fn do_wait_peer_trust(
        self,
    ) -> Result<DeviceGreetInProgress2Ctx, GreetInProgressError> {
        self.0
            .do_wait_peer_trust()
            .await
            .map(DeviceGreetInProgress2Ctx)
    }
}

// GreetInProgress2Ctx

#[derive(Debug)]
struct BaseGreetInProgress2Ctx {
    token: InvitationToken,
    claimer_sas: SASCode,
    shared_secret_key: SecretKey,
    cmds: Arc<AuthenticatedCmds>,
    event_bus: EventBus,
}

impl BaseGreetInProgress2Ctx {
    fn generate_claimer_sas_choices(&self, size: usize) -> Vec<SASCode> {
        SASCode::generate_sas_code_candidates(&self.claimer_sas, size)
    }

    async fn do_signify_trust(self) -> Result<BaseGreetInProgress3Ctx, GreetInProgressError> {
        use authenticated_cmds::latest::invite_3b_greeter_signify_trust::{Rep, Req};

        let rep = self.cmds.send(Req { token: self.token }).await?;

        match rep {
            Rep::Ok => Ok(BaseGreetInProgress3Ctx {
                token: self.token,
                shared_secret_key: self.shared_secret_key,
                cmds: self.cmds,
                event_bus: self.event_bus,
            }),
            Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
            Rep::InvalidState => Err(GreetInProgressError::PeerReset),
            Rep::NotFound => Err(GreetInProgressError::NotFound),
            bad_rep @ Rep::UnknownStatus { .. } => {
                Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
            }
        }
    }
}

#[derive(Debug)]
pub struct UserGreetInProgress2Ctx(BaseGreetInProgress2Ctx);

impl UserGreetInProgress2Ctx {
    pub fn claimer_sas(&self) -> &SASCode {
        &self.0.claimer_sas
    }

    pub fn generate_claimer_sas_choices(&self, size: usize) -> Vec<SASCode> {
        self.0.generate_claimer_sas_choices(size)
    }

    pub async fn do_signify_trust(self) -> Result<UserGreetInProgress3Ctx, GreetInProgressError> {
        self.0.do_signify_trust().await.map(UserGreetInProgress3Ctx)
    }
}

#[derive(Debug)]
pub struct DeviceGreetInProgress2Ctx(BaseGreetInProgress2Ctx);

impl DeviceGreetInProgress2Ctx {
    pub fn claimer_sas(&self) -> &SASCode {
        &self.0.claimer_sas
    }

    pub fn generate_claimer_sas_choices(&self, size: usize) -> Vec<SASCode> {
        self.0.generate_claimer_sas_choices(size)
    }

    pub async fn do_signify_trust(self) -> Result<DeviceGreetInProgress3Ctx, GreetInProgressError> {
        self.0
            .do_signify_trust()
            .await
            .map(DeviceGreetInProgress3Ctx)
    }
}

// GreetInProgress3Ctx

#[derive(Debug)]
struct BaseGreetInProgress3Ctx {
    token: InvitationToken,
    shared_secret_key: SecretKey,
    cmds: Arc<AuthenticatedCmds>,
    event_bus: EventBus,
}

#[derive(Debug)]
struct BaseGreetInProgress3WithPayloadCtx {
    token: InvitationToken,
    shared_secret_key: SecretKey,
    cmds: Arc<AuthenticatedCmds>,
    event_bus: EventBus,
    payload: Bytes,
}

impl BaseGreetInProgress3Ctx {
    async fn do_get_claim_requests(
        self,
    ) -> Result<BaseGreetInProgress3WithPayloadCtx, GreetInProgressError> {
        use authenticated_cmds::latest::invite_4_greeter_communicate::{Rep, Req};

        let rep = self
            .cmds
            .send(Req {
                token: self.token,
                payload: Bytes::new(),
            })
            .await?;

        let payload = match rep {
            Rep::Ok { payload } => Ok(payload),
            Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
            Rep::InvalidState => Err(GreetInProgressError::PeerReset),
            Rep::NotFound => Err(GreetInProgressError::NotFound),
            bad_rep @ Rep::UnknownStatus { .. } => {
                Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
            }
        }?;

        Ok(BaseGreetInProgress3WithPayloadCtx {
            token: self.token,
            shared_secret_key: self.shared_secret_key,
            cmds: self.cmds,
            event_bus: self.event_bus,
            payload,
        })
    }
}

#[derive(Debug)]
pub struct UserGreetInProgress3Ctx(BaseGreetInProgress3Ctx);

impl UserGreetInProgress3Ctx {
    pub async fn do_get_claim_requests(
        self,
    ) -> Result<UserGreetInProgress4Ctx, GreetInProgressError> {
        let ctx = self.0.do_get_claim_requests().await?;

        let data = InviteUserData::decrypt_and_load(&ctx.payload, &ctx.shared_secret_key)
            .map_err(GreetInProgressError::CorruptedInviteUserData)?;

        Ok(UserGreetInProgress4Ctx {
            token: ctx.token,
            requested_device_label: data.requested_device_label,
            requested_human_handle: data.requested_human_handle,
            public_key: data.public_key,
            verify_key: data.verify_key,
            shared_secret_key: ctx.shared_secret_key,
            cmds: ctx.cmds,
            event_bus: ctx.event_bus,
        })
    }
}

#[derive(Debug)]
pub struct DeviceGreetInProgress3Ctx(BaseGreetInProgress3Ctx);

impl DeviceGreetInProgress3Ctx {
    pub async fn do_get_claim_requests(
        self,
    ) -> Result<DeviceGreetInProgress4Ctx, GreetInProgressError> {
        let ctx = self.0.do_get_claim_requests().await?;

        let data = InviteDeviceData::decrypt_and_load(&ctx.payload, &ctx.shared_secret_key)
            .map_err(GreetInProgressError::CorruptedInviteUserData)?;

        Ok(DeviceGreetInProgress4Ctx {
            token: ctx.token,
            requested_device_label: data.requested_device_label,
            verify_key: data.verify_key,
            shared_secret_key: ctx.shared_secret_key,
            cmds: ctx.cmds,
            event_bus: ctx.event_bus,
        })
    }
}

/// Helper to prepare the creation of a new user.
fn create_new_signed_user_certificates(
    author: &LocalDevice,
    device_label: Option<DeviceLabel>,
    human_handle: Option<HumanHandle>,
    profile: UserProfile,
    public_key: PublicKey,
    verify_key: VerifyKey,
    timestamp: DateTime,
) -> (Bytes, Bytes, Bytes, Bytes, InviteUserConfirmation) {
    let device_id = DeviceID::default();

    let user_certificate = UserCertificate {
        author: CertificateSignerOwned::User(author.device_id.clone()),
        timestamp,
        user_id: device_id.user_id().clone(),
        human_handle: human_handle.clone(),
        public_key: public_key.clone(),
        profile,
    };

    let redacted_user_certificate = UserCertificate {
        author: CertificateSignerOwned::User(author.device_id.clone()),
        timestamp,
        user_id: device_id.user_id().clone(),
        human_handle: None,
        public_key,
        profile,
    };

    let device_certificate = DeviceCertificate {
        author: CertificateSignerOwned::User(author.device_id.clone()),
        timestamp,
        device_id: device_id.clone(),
        device_label: device_label.clone(),
        verify_key: verify_key.clone(),
    };

    let redacted_device_certificate = DeviceCertificate {
        author: CertificateSignerOwned::User(author.device_id.clone()),
        timestamp,
        device_id: device_id.clone(),
        device_label: None,
        verify_key,
    };

    let user_certificate_bytes = user_certificate.dump_and_sign(&author.signing_key);
    let redacted_user_certificate_bytes =
        redacted_user_certificate.dump_and_sign(&author.signing_key);
    let device_certificate_bytes = device_certificate.dump_and_sign(&author.signing_key);
    let redacted_device_certificate_bytes =
        redacted_device_certificate.dump_and_sign(&author.signing_key);

    let invite_user_confirmation = InviteUserConfirmation {
        device_id,
        device_label,
        human_handle,
        profile,
        root_verify_key: author.root_verify_key().clone(),
    };

    (
        user_certificate_bytes.into(),
        redacted_user_certificate_bytes.into(),
        device_certificate_bytes.into(),
        redacted_device_certificate_bytes.into(),
        invite_user_confirmation,
    )
}

fn create_new_signed_device_certificates(
    author: &LocalDevice,
    device_label: Option<DeviceLabel>,
    verify_key: VerifyKey,
    timestamp: DateTime,
) -> (Bytes, Bytes, DeviceID) {
    let device_id = author.user_id().to_device_id(DeviceName::default());

    let device_certificate = DeviceCertificate {
        author: CertificateSignerOwned::User(author.device_id.clone()),
        timestamp,
        device_id: device_id.clone(),
        device_label,
        verify_key: verify_key.clone(),
    };

    let redacted_device_certificate = DeviceCertificate {
        author: CertificateSignerOwned::User(author.device_id.clone()),
        timestamp,
        device_id: device_id.clone(),
        device_label: None,
        verify_key,
    };

    let device_certificate_bytes = device_certificate.dump_and_sign(&author.signing_key);
    let redacted_device_certificate_bytes =
        redacted_device_certificate.dump_and_sign(&author.signing_key);

    (
        device_certificate_bytes.into(),
        redacted_device_certificate_bytes.into(),
        device_id,
    )
}

// GreetInProgress4Ctx

#[derive(Debug)]
pub struct UserGreetInProgress4Ctx {
    pub token: InvitationToken,
    pub requested_device_label: Option<DeviceLabel>,
    pub requested_human_handle: Option<HumanHandle>,
    public_key: PublicKey,
    verify_key: VerifyKey,
    shared_secret_key: SecretKey,
    cmds: Arc<AuthenticatedCmds>,
    event_bus: EventBus,
}

impl UserGreetInProgress4Ctx {
    pub async fn do_create_new_user(
        self,
        author: &LocalDevice,
        device_label: Option<DeviceLabel>,
        human_handle: Option<HumanHandle>,
        profile: UserProfile,
    ) -> Result<(), GreetInProgressError> {
        let mut timestamp = author.time_provider.now();
        let invite_user_confirmation = loop {
            let (
                user_certificate,
                redacted_user_certificate,
                device_certificate,
                redacted_device_certificate,
                invite_user_confirmation,
            ) = create_new_signed_user_certificates(
                author,
                device_label.clone(),
                human_handle.clone(),
                profile,
                self.public_key.clone(),
                self.verify_key.clone(),
                timestamp,
            );

            {
                use authenticated_cmds::latest::user_create::{Rep, Req};

                let rep = self
                    .cmds
                    .send(Req {
                        user_certificate,
                        device_certificate,
                        redacted_user_certificate,
                        redacted_device_certificate,
                    })
                    .await?;

                match rep {
                    Rep::Ok => Ok(()),
                    Rep::RequireGreaterTimestamp {
                        strictly_greater_than,
                    } => {
                        timestamp =
                            std::cmp::max(strictly_greater_than, author.time_provider.now());
                        continue;
                    }
                    Rep::ActiveUsersLimitReached { .. } => {
                        Err(GreetInProgressError::ActiveUsersLimitReached)
                    }
                    Rep::AlreadyExists { .. } => Err(GreetInProgressError::UserAlreadyExists),
                    Rep::NotAllowed { .. } => Err(GreetInProgressError::UserCreateNotAllowed),
                    Rep::BadTimestamp {
                        backend_timestamp,
                        client_timestamp,
                        ballpark_client_early_offset,
                        ballpark_client_late_offset,
                    } => {
                        let event = EventTooMuchDriftWithServerClock {
                            backend_timestamp,
                            ballpark_client_early_offset,
                            ballpark_client_late_offset,
                            client_timestamp,
                        };
                        self.event_bus.send(&event);

                        Err(GreetInProgressError::BadTimestamp {
                            server_timestamp: backend_timestamp,
                            client_timestamp,
                            ballpark_client_early_offset,
                            ballpark_client_late_offset,
                        })
                    }
                    bad_rep @ (Rep::UnknownStatus { .. }
                    | Rep::InvalidCertification { .. }
                    | Rep::InvalidData { .. }) => {
                        Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
                    }
                }?;
            }

            break invite_user_confirmation;
        };

        // From now on the user has been created on the server, but greeter
        // is not aware of it yet. If something goes wrong, we can end up with
        // the greeter losing it private keys.
        // This is considered acceptable given 1) the error window is small and
        // 2) if this occurs the inviter can revoke the user and retry the
        // enrollment process to fix this

        let payload = invite_user_confirmation
            .dump_and_encrypt(&self.shared_secret_key)
            .into();

        {
            use authenticated_cmds::latest::invite_4_greeter_communicate::{Rep, Req};

            let rep = self
                .cmds
                .send(Req {
                    token: self.token,
                    payload,
                })
                .await?;

            match rep {
                Rep::Ok { .. } => Ok(()),
                Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
                Rep::InvalidState => Err(GreetInProgressError::PeerReset),
                Rep::NotFound => Err(GreetInProgressError::NotFound),
                bad_rep @ Rep::UnknownStatus { .. } => {
                    Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
                }
            }?;
        }

        // Invitation deletion is not strictly necessary (enrollment has succeeded
        // anyway) so it's no big deal if something goes wrong before it can be
        // done (and it can be manually deleted from invitation list).

        {
            use authenticated_cmds::latest::invite_delete::{InvitationDeletedReason, Req};

            let _ = self
                .cmds
                .send(Req {
                    token: self.token,
                    reason: InvitationDeletedReason::Finished,
                })
                .await;
        }

        Ok(())
    }
}

#[derive(Debug)]
pub struct DeviceGreetInProgress4Ctx {
    pub token: InvitationToken,
    pub requested_device_label: Option<DeviceLabel>,
    verify_key: VerifyKey,
    shared_secret_key: SecretKey,
    cmds: Arc<AuthenticatedCmds>,
    #[allow(dead_code)]
    event_bus: EventBus,
}

impl DeviceGreetInProgress4Ctx {
    pub async fn do_create_new_device(
        self,
        author: &LocalDevice,
        device_label: Option<DeviceLabel>,
    ) -> Result<(), GreetInProgressError> {
        let mut timestamp = author.time_provider.now();
        let device_id = loop {
            let (device_certificate_bytes, redacted_device_certificate_bytes, device_id) =
                create_new_signed_device_certificates(
                    author,
                    device_label.clone(),
                    self.verify_key.clone(),
                    timestamp,
                );

            {
                use authenticated_cmds::latest::device_create::{Rep, Req};

                let rep = self
                    .cmds
                    .send(Req {
                        device_certificate: device_certificate_bytes,
                        redacted_device_certificate: redacted_device_certificate_bytes,
                    })
                    .await?;

                match rep {
                    Rep::Ok => Ok(()),
                    Rep::RequireGreaterTimestamp {
                        strictly_greater_than,
                    } => {
                        timestamp =
                            std::cmp::max(strictly_greater_than, author.time_provider.now());
                        continue;
                    }
                    Rep::AlreadyExists { .. } => Err(GreetInProgressError::DeviceAlreadyExists),
                    Rep::BadTimestamp {
                        backend_timestamp,
                        client_timestamp,
                        ballpark_client_early_offset,
                        ballpark_client_late_offset,
                    } => Err(GreetInProgressError::BadTimestamp {
                        server_timestamp: backend_timestamp,
                        client_timestamp,
                        ballpark_client_early_offset,
                        ballpark_client_late_offset,
                    }),
                    bad_rep @ (Rep::UnknownStatus { .. }
                    | Rep::BadUserId { .. } // Should never happen given we have used our own UserID which is valid !
                    | Rep::InvalidCertification { .. }
                    | Rep::InvalidData { .. }) => {
                        Err(
                            anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into()
                        )
                    }
                }?;

                break device_id;
            }
        };

        // From now on the device has been created on the server, but greeter
        // is not aware of it yet. If something goes wrong, we can end up with
        // the greeter losing it private keys.
        // This is considered acceptable given 1) the error window is small and
        // 2) if this occurs the inviter can revoke the device and retry the
        // enrollment process to fix this

        let payload = InviteDeviceConfirmation {
            device_id,
            device_label,
            human_handle: author.human_handle.clone(),
            profile: author.initial_profile,
            private_key: author.private_key.clone(),
            user_manifest_id: author.user_manifest_id,
            user_manifest_key: author.user_manifest_key.clone(),
            root_verify_key: author.root_verify_key().clone(),
        }
        .dump_and_encrypt(&self.shared_secret_key)
        .into();

        {
            use authenticated_cmds::latest::invite_4_greeter_communicate::{Rep, Req};

            let rep = self
                .cmds
                .send(Req {
                    token: self.token,
                    payload,
                })
                .await?;

            match rep {
                Rep::Ok { .. } => Ok(()),
                Rep::AlreadyDeleted => Err(GreetInProgressError::AlreadyUsed),
                Rep::InvalidState => Err(GreetInProgressError::PeerReset),
                Rep::NotFound => Err(GreetInProgressError::NotFound),
                bad_rep @ Rep::UnknownStatus { .. } => {
                    Err(anyhow::anyhow!("Unexpected server response: {:?}", bad_rep).into())
                }
            }?;
        }

        // Invitation deletion is not strictly necessary (enrollment has succeeded
        // anyway) so it's no big deal if something goes wrong before it can be
        // done (and it can be manually deleted from invitation list).

        {
            use authenticated_cmds::latest::invite_delete::{InvitationDeletedReason, Req};

            let _ = self
                .cmds
                .send(Req {
                    token: self.token,
                    reason: InvitationDeletedReason::Finished,
                })
                .await;
        }

        Ok(())
    }
}
