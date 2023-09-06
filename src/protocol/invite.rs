// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

use pyo3::{
    exceptions::{PyAttributeError, PyNotImplementedError, PyValueError},
    prelude::*,
    types::{PyBytes, PyTuple, PyType},
};
use std::num::NonZeroU64;

use libparsec::{
    protocol::{
        authenticated_cmds::v2::{
            invite_1_greeter_wait_peer, invite_2a_greeter_get_hashed_nonce,
            invite_2b_greeter_send_nonce, invite_3a_greeter_wait_peer_trust,
            invite_3b_greeter_signify_trust, invite_4_greeter_communicate, invite_delete,
            invite_list, invite_new,
        },
        invited_cmds::v2::{
            invite_1_claimer_wait_peer, invite_2a_claimer_send_hashed_nonce,
            invite_2b_claimer_send_nonce, invite_3a_claimer_signify_trust,
            invite_3b_claimer_wait_peer_trust, invite_4_claimer_communicate, invite_info,
        },
    },
    types::{Maybe, ProtocolRequest},
};

use crate::{
    api_crypto::{HashDigest, PublicKey},
    binding_utils::BytesWrapper,
    enumerate::{
        InvitationDeletedReason, InvitationEmailSentStatus, InvitationStatus, InvitationType,
    },
    ids::{HumanHandle, InvitationToken, UserID},
    protocol::{
        error::{ProtocolError, ProtocolErrorFields, ProtocolResult},
        gen_rep,
    },
    time::DateTime,
};

#[pyclass]
#[derive(Clone)]
pub(crate) struct InviteListItem(pub invite_list::InviteListItem);

crate::binding_utils::gen_proto!(InviteListItem, __repr__);
crate::binding_utils::gen_proto!(InviteListItem, __copy__);
crate::binding_utils::gen_proto!(InviteListItem, __deepcopy__);
crate::binding_utils::gen_proto!(InviteListItem, __richcmp__, eq);

#[pymethods]
impl InviteListItem {
    #[classmethod]
    #[pyo3(name = "User")]
    fn user(
        _cls: &PyType,
        token: InvitationToken,
        created_on: DateTime,
        claimer_email: String,
        status: InvitationStatus,
    ) -> PyResult<Self> {
        let token = token.0;
        let created_on = created_on.0;
        Ok(Self(invite_list::InviteListItem::User {
            token,
            created_on,
            claimer_email,
            status: status.0,
        }))
    }

    #[classmethod]
    #[pyo3(name = "Device")]
    fn device(
        _cls: &PyType,
        token: InvitationToken,
        created_on: DateTime,
        status: InvitationStatus,
    ) -> PyResult<Self> {
        let token = token.0;
        let created_on = created_on.0;
        Ok(Self(invite_list::InviteListItem::Device {
            token,
            created_on,
            status: status.0,
        }))
    }

    #[classmethod]
    #[pyo3(name = "ShamirRecovery")]
    fn shamir_recovery(
        _cls: &PyType,
        token: InvitationToken,
        created_on: DateTime,
        claimer_user_id: UserID,
        status: InvitationStatus,
    ) -> PyResult<Self> {
        let token = token.0;
        let created_on = created_on.0;
        Ok(Self(invite_list::InviteListItem::ShamirRecovery {
            token,
            created_on,
            claimer_user_id: claimer_user_id.0,
            status: status.0,
        }))
    }

    #[getter]
    #[pyo3(name = "r#type")]
    fn r#type(&self) -> PyResult<InvitationType> {
        Ok(InvitationType(match self.0 {
            invite_list::InviteListItem::User { .. } => libparsec::types::InvitationType::User,
            invite_list::InviteListItem::Device { .. } => libparsec::types::InvitationType::Device,
            invite_list::InviteListItem::ShamirRecovery { .. } => {
                libparsec::types::InvitationType::ShamirRecovery
            }
        }))
    }

    #[getter]
    fn token(&self) -> PyResult<InvitationToken> {
        Ok(InvitationToken(match self.0 {
            invite_list::InviteListItem::User { token, .. } => token,
            invite_list::InviteListItem::Device { token, .. } => token,
            invite_list::InviteListItem::ShamirRecovery { token, .. } => token,
        }))
    }

    #[getter]
    fn created_on(&self) -> PyResult<DateTime> {
        Ok(DateTime(match self.0 {
            invite_list::InviteListItem::User { created_on, .. } => created_on,
            invite_list::InviteListItem::Device { created_on, .. } => created_on,
            invite_list::InviteListItem::ShamirRecovery { created_on, .. } => created_on,
        }))
    }

    #[getter]
    fn claimer_email(&self) -> PyResult<&str> {
        match &self.0 {
            invite_list::InviteListItem::User { claimer_email, .. } => Ok(claimer_email),
            _ => Err(PyAttributeError::new_err("claimer_email")),
        }
    }

    #[getter]
    fn claimer_user_id(&self) -> PyResult<UserID> {
        match &self.0 {
            invite_list::InviteListItem::ShamirRecovery {
                claimer_user_id, ..
            } => Ok(UserID(claimer_user_id.clone())),
            _ => Err(PyAttributeError::new_err("claimer_user_id")),
        }
    }

    #[getter]
    fn status(&self) -> PyResult<InvitationStatus> {
        Ok(InvitationStatus(match &self.0 {
            invite_list::InviteListItem::User { status, .. } => status.clone(),
            invite_list::InviteListItem::Device { status, .. } => status.clone(),
            invite_list::InviteListItem::ShamirRecovery { status, .. } => status.clone(),
        }))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct InviteNewReq(pub invite_new::Req);

crate::binding_utils::gen_proto!(InviteNewReq, __repr__);
crate::binding_utils::gen_proto!(InviteNewReq, __copy__);
crate::binding_utils::gen_proto!(InviteNewReq, __deepcopy__);
crate::binding_utils::gen_proto!(InviteNewReq, __richcmp__, eq);

#[pymethods]
impl InviteNewReq {
    #[new]
    #[args(claimer_email = "None", claimer_user_id = "None")]
    fn new(
        r#type: InvitationType,
        send_email: bool,
        claimer_email: Option<String>,
        claimer_user_id: Option<UserID>,
    ) -> PyResult<Self> {
        Ok(InviteNewReq(match r#type.0 {
            libparsec::types::InvitationType::Device => {
                invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::Device { send_email })
            }
            libparsec::types::InvitationType::User => {
                invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::User {
                    claimer_email: claimer_email
                        .ok_or(PyAttributeError::new_err("Missing claimer_email argument"))?,
                    send_email,
                })
            }
            libparsec::types::InvitationType::ShamirRecovery => {
                invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                    claimer_user_id: claimer_user_id.map(|x| x.0).ok_or(
                        PyAttributeError::new_err("Missing claimer_user_id argument"),
                    )?,
                    send_email,
                })
            }
        }))
    }

    #[classmethod]
    #[pyo3(name = "User")]
    fn user(_cls: &PyType, claimer_email: String, send_email: bool) -> Self {
        Self(invite_new::Req(
            invite_new::UserOrDeviceOrShamirRecovery::User {
                claimer_email,
                send_email,
            },
        ))
    }

    #[classmethod]
    #[pyo3(name = "Device")]
    fn device(_cls: &PyType, send_email: bool) -> Self {
        Self(invite_new::Req(
            invite_new::UserOrDeviceOrShamirRecovery::Device { send_email },
        ))
    }

    #[classmethod]
    #[pyo3(name = "ShamirRecovery")]
    fn shamir_recovery(_cls: &PyType, send_email: bool, claimer_user_id: UserID) -> Self {
        let claimer_user_id = claimer_user_id.0;
        Self(invite_new::Req(
            invite_new::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                send_email,
                claimer_user_id,
            },
        ))
    }

    #[getter]
    #[pyo3(name = "r#type")]
    fn invitation_type(&self) -> PyResult<InvitationType> {
        Ok(InvitationType(match self.0 {
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::Device { .. }) => {
                libparsec::types::InvitationType::Device
            }
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::User { .. }) => {
                libparsec::types::InvitationType::User
            }
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                ..
            }) => libparsec::types::InvitationType::ShamirRecovery,
        }))
    }

    #[getter]
    fn claimer_email(&self) -> PyResult<&str> {
        match &self.0 {
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::User {
                claimer_email,
                ..
            }) => Ok(claimer_email),
            _ => Err(PyAttributeError::new_err("No claimer_email attribute")),
        }
    }

    #[getter]
    fn send_email(&self) -> bool {
        match self.0 {
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::User {
                send_email, ..
            }) => send_email,
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::Device { send_email }) => {
                send_email
            }
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                send_email,
                ..
            }) => send_email,
        }
    }

    #[getter]
    fn claimer_user_id(&self) -> PyResult<UserID> {
        match &self.0 {
            invite_new::Req(invite_new::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                claimer_user_id,
                ..
            }) => Ok(UserID(claimer_user_id.clone())),
            _ => Err(PyAttributeError::new_err("No claimer_user_id attribute")),
        }
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }
}

gen_rep!(
    invite_new,
    InviteNewRep,
    { .. },
    [NotAllowed],
    [AlreadyMember],
    [NotAvailable],
    [ShamirRecoveryNotSetup],
);

#[pyclass(extends=InviteNewRep)]
pub(crate) struct InviteNewRepOk;

#[pymethods]
impl InviteNewRepOk {
    #[new]
    pub fn new(
        token: InvitationToken,
        email_sent: InvitationEmailSentStatus,
    ) -> PyResult<(Self, InviteNewRep)> {
        let token = token.0;
        Ok((
            Self,
            InviteNewRep(invite_new::Rep::Ok {
                token,
                email_sent: libparsec::types::Maybe::Present(email_sent.0),
            }),
        ))
    }

    #[getter]
    fn token(_self: PyRef<'_, Self>) -> PyResult<InvitationToken> {
        match &_self.as_ref().0 {
            invite_new::Rep::Ok { token, .. } => Ok(InvitationToken(*token)),
            _ => Err(PyAttributeError::new_err("No attribute token")),
        }
    }

    #[getter]
    fn email_sent(_self: PyRef<'_, Self>) -> PyResult<InvitationEmailSentStatus> {
        match &_self.as_ref().0 {
            invite_new::Rep::Ok { email_sent, .. } => match email_sent {
                libparsec::types::Maybe::Present(p) => Ok(InvitationEmailSentStatus(p.clone())),
                libparsec::types::Maybe::Absent => Err(PyAttributeError::new_err("")),
            },
            _ => Err(PyAttributeError::new_err("")),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct InviteDeleteReq(pub invite_delete::Req);

crate::binding_utils::gen_proto!(InviteDeleteReq, __repr__);
crate::binding_utils::gen_proto!(InviteDeleteReq, __copy__);
crate::binding_utils::gen_proto!(InviteDeleteReq, __deepcopy__);
crate::binding_utils::gen_proto!(InviteDeleteReq, __richcmp__, eq);

#[pymethods]
impl InviteDeleteReq {
    #[new]
    fn new(token: InvitationToken, reason: InvitationDeletedReason) -> PyResult<Self> {
        let token = token.0;
        Ok(Self(invite_delete::Req {
            token,
            reason: reason.0,
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(&self) -> PyResult<InvitationToken> {
        Ok(InvitationToken(self.0.token))
    }

    #[getter]
    fn reason(&self) -> PyResult<InvitationDeletedReason> {
        Ok(InvitationDeletedReason(self.0.reason.clone()))
    }
}

gen_rep!(
    invite_delete,
    InviteDeleteRep,
    { .. },
    [AlreadyDeleted],
    [NotFound]
);

#[pyclass(extends=InviteDeleteRep)]
pub(crate) struct InviteDeleteRepOk;

#[pymethods]
impl InviteDeleteRepOk {
    #[new]
    fn new() -> PyResult<(Self, InviteDeleteRep)> {
        Ok((Self, InviteDeleteRep(invite_delete::Rep::Ok)))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct InviteListReq(pub invite_list::Req);

crate::binding_utils::gen_proto!(InviteListReq, __repr__);
crate::binding_utils::gen_proto!(InviteListReq, __copy__);
crate::binding_utils::gen_proto!(InviteListReq, __deepcopy__);
crate::binding_utils::gen_proto!(InviteListReq, __richcmp__, eq);

#[pymethods]
impl InviteListReq {
    #[new]
    fn new() -> PyResult<Self> {
        Ok(Self(invite_list::Req))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }
}

gen_rep!(invite_list, InviteListRep, { .. });

#[pyclass(extends=InviteListRep)]
pub(crate) struct InviteListRepOk;

#[pymethods]
impl InviteListRepOk {
    #[new]
    fn new(invitations: Vec<InviteListItem>) -> PyResult<(Self, InviteListRep)> {
        let invitations = invitations.into_iter().map(|inv| inv.0).collect();
        Ok((Self, InviteListRep(invite_list::Rep::Ok { invitations })))
    }

    #[getter]
    fn invitations(_self: PyRef<'_, Self>) -> PyResult<Vec<InviteListItem>> {
        match &_self.as_ref().0 {
            invite_list::Rep::Ok { invitations } => Ok(invitations
                .iter()
                .map(|f| InviteListItem(f.clone()))
                .collect()),
            _ => Err(PyAttributeError::new_err("")),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct InviteInfoReq(pub invite_info::Req);

crate::binding_utils::gen_proto!(InviteInfoReq, __repr__);
crate::binding_utils::gen_proto!(InviteInfoReq, __copy__);
crate::binding_utils::gen_proto!(InviteInfoReq, __deepcopy__);
crate::binding_utils::gen_proto!(InviteInfoReq, __richcmp__, eq);

#[pymethods]
impl InviteInfoReq {
    #[new]
    fn new() -> PyResult<Self> {
        Ok(Self(invite_info::Req))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct ShamirRecoveryRecipient(invite_info::ShamirRecoveryRecipient);

crate::binding_utils::gen_proto!(ShamirRecoveryRecipient, __repr__);
crate::binding_utils::gen_proto!(ShamirRecoveryRecipient, __copy__);
crate::binding_utils::gen_proto!(ShamirRecoveryRecipient, __deepcopy__);
crate::binding_utils::gen_proto!(ShamirRecoveryRecipient, __richcmp__, eq);

#[pymethods]
impl ShamirRecoveryRecipient {
    #[new]
    fn new(user_id: UserID, human_handle: Option<HumanHandle>, shares: u64) -> PyResult<Self> {
        Ok(Self(invite_info::ShamirRecoveryRecipient {
            user_id: user_id.0,
            human_handle: human_handle.map(|x| x.0),
            shares: NonZeroU64::try_from(shares)
                .map_err(|_| PyValueError::new_err("shares must be greater than 0"))?,
        }))
    }
    #[getter]
    fn user_id(&self) -> UserID {
        UserID(self.0.user_id.clone())
    }

    #[getter]
    fn human_handle(&self) -> Option<HumanHandle> {
        self.0.human_handle.clone().map(HumanHandle)
    }

    #[getter]
    fn shares(&self) -> u64 {
        u64::from(self.0.shares)
    }
}

gen_rep!(invite_info, InviteInfoRep, { .. });

#[pyclass(extends=InviteInfoRep)]
pub(crate) struct InviteInfoRepOk;

#[pymethods]
impl InviteInfoRepOk {
    #[new]
    #[args(
        claimer_email = "None",
        greeter_user_id = "None",
        greeter_human_handle = "None",
        threshold = "None",
        recipients = "None"
    )]
    fn new(
        r#type: InvitationType,
        claimer_email: Option<String>,
        greeter_user_id: Option<UserID>,
        greeter_human_handle: Option<HumanHandle>,
        threshold: Option<u64>,
        recipients: Option<Vec<ShamirRecoveryRecipient>>,
    ) -> PyResult<(Self, InviteInfoRep)> {
        match r#type {
            InvitationType(libparsec::types::InvitationType::Device) => Ok((
                Self,
                InviteInfoRep(invite_info::Rep::Ok(
                    invite_info::UserOrDeviceOrShamirRecovery::Device {
                        greeter_user_id: greeter_user_id
                            .ok_or(PyAttributeError::new_err(
                                "Missing greeter_user_id for InviteInfoRep[Device]",
                            ))?
                            .0,
                        greeter_human_handle: greeter_human_handle.map(|x| x.0),
                    },
                )),
            )),
            InvitationType(libparsec::types::InvitationType::User) => Ok((
                Self,
                InviteInfoRep(invite_info::Rep::Ok(
                    invite_info::UserOrDeviceOrShamirRecovery::User {
                        claimer_email: claimer_email.ok_or(PyAttributeError::new_err(
                            "Missing claimer_email for InviteInfoRep[User]",
                        ))?,
                        greeter_user_id: greeter_user_id
                            .ok_or(PyAttributeError::new_err(
                                "Missing greeter_user_id for InviteInfoRep[User]",
                            ))?
                            .0,
                        greeter_human_handle: greeter_human_handle.map(|x| x.0),
                    },
                )),
            )),
            InvitationType(libparsec::types::InvitationType::ShamirRecovery) => Ok((
                Self,
                InviteInfoRep(invite_info::Rep::Ok(
                    invite_info::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                        threshold: NonZeroU64::try_from(
                            threshold
                                .ok_or(PyAttributeError::new_err("Missing threshold argument"))?,
                        )
                        .map_err(|_| PyValueError::new_err("threshold must be greater than 0"))?,
                        recipients: recipients
                            .ok_or(PyAttributeError::new_err("Missing recipients argument"))?
                            .into_iter()
                            .map(|x| x.0)
                            .collect(),
                    },
                )),
            )),
        }
    }

    #[getter]
    fn r#type(_self: PyRef<'_, Self>) -> PyResult<InvitationType> {
        match &_self.as_ref().0 {
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::Device { .. }) => {
                Ok(InvitationType(libparsec::types::InvitationType::Device))
            }
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::User { .. }) => {
                Ok(InvitationType(libparsec::types::InvitationType::User))
            }
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                ..
            }) => Ok(InvitationType(
                libparsec::types::InvitationType::ShamirRecovery,
            )),
            _ => Err(PyAttributeError::new_err("type")),
        }
    }

    #[getter]
    fn greeter_user_id(_self: PyRef<'_, Self>) -> PyResult<UserID> {
        match &_self.as_ref().0 {
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::Device {
                greeter_user_id,
                ..
            }) => Ok(UserID(greeter_user_id.clone())),
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::User {
                greeter_user_id,
                ..
            }) => Ok(UserID(greeter_user_id.clone())),
            _ => Err(PyAttributeError::new_err("")),
        }
    }

    #[getter]
    fn claimer_email(_self: PyRef<'_, Self>) -> PyResult<String> {
        match &_self.as_ref().0 {
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::User {
                claimer_email,
                ..
            }) => Ok(claimer_email.clone()),
            _ => Err(PyAttributeError::new_err(
                "no claimer_email in non device invitation",
            )),
        }
    }

    #[getter]
    fn greeter_human_handle(_self: PyRef<'_, Self>) -> PyResult<Option<HumanHandle>> {
        match &_self.as_ref().0 {
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::Device {
                greeter_human_handle: handle,
                ..
            })
            | invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::User {
                greeter_human_handle: handle,
                ..
            }) => Ok(handle.clone().map(HumanHandle)),
            _ => Err(PyAttributeError::new_err("no greeter_human_handle attr")),
        }
    }

    #[getter]
    fn threshold(_self: PyRef<'_, Self>) -> PyResult<u64> {
        match _self.as_ref().0 {
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                threshold,
                ..
            }) => Ok(u64::from(threshold)),
            _ => Err(PyAttributeError::new_err("no threshold attr")),
        }
    }

    #[getter]
    fn recipients<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyTuple> {
        match &_self.as_ref().0 {
            invite_info::Rep::Ok(invite_info::UserOrDeviceOrShamirRecovery::ShamirRecovery {
                recipients,
                ..
            }) => Ok(PyTuple::new(
                py,
                recipients
                    .clone()
                    .into_iter()
                    .map(|x| ShamirRecoveryRecipient(x).into_py(py)),
            )),
            _ => Err(PyAttributeError::new_err("no recipients attr")),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite1ClaimerWaitPeerReq(pub invite_1_claimer_wait_peer::Req);

crate::binding_utils::gen_proto!(Invite1ClaimerWaitPeerReq, __repr__);
crate::binding_utils::gen_proto!(Invite1ClaimerWaitPeerReq, __copy__);
crate::binding_utils::gen_proto!(Invite1ClaimerWaitPeerReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite1ClaimerWaitPeerReq, __richcmp__, eq);

#[pymethods]
impl Invite1ClaimerWaitPeerReq {
    #[new]
    fn new(claimer_public_key: PublicKey, greeter_user_id: UserID) -> PyResult<Self> {
        let claimer_public_key = claimer_public_key.0;
        let greeter_user_id = greeter_user_id.0;
        Ok(Self(invite_1_claimer_wait_peer::Req {
            claimer_public_key,
            greeter_user_id: Maybe::Present(greeter_user_id),
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn greeter_user_id(&self) -> Option<UserID> {
        match &self.0.greeter_user_id {
            Maybe::Present(x) => Some(UserID(x.clone())),
            Maybe::Absent => None,
        }
    }

    #[getter]
    fn claimer_public_key(&self) -> PublicKey {
        PublicKey(self.0.claimer_public_key.clone())
    }
}

gen_rep!(
    invite_1_claimer_wait_peer,
    Invite1ClaimerWaitPeerRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite1ClaimerWaitPeerRep)]
pub(crate) struct Invite1ClaimerWaitPeerRepOk;

#[pymethods]
impl Invite1ClaimerWaitPeerRepOk {
    #[new]
    fn new(greeter_public_key: PublicKey) -> PyResult<(Self, Invite1ClaimerWaitPeerRep)> {
        let greeter_public_key = greeter_public_key.0;
        Ok((
            Self,
            Invite1ClaimerWaitPeerRep(invite_1_claimer_wait_peer::Rep::Ok { greeter_public_key }),
        ))
    }

    #[getter]
    fn greeter_public_key(_self: PyRef<'_, Self>) -> PyResult<PublicKey> {
        match &_self.as_ref().0 {
            invite_1_claimer_wait_peer::Rep::Ok { greeter_public_key } => {
                Ok(PublicKey(greeter_public_key.clone()))
            }
            _ => Err(PyNotImplementedError::new_err("")),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite1GreeterWaitPeerReq(pub invite_1_greeter_wait_peer::Req);

crate::binding_utils::gen_proto!(Invite1GreeterWaitPeerReq, __repr__);
crate::binding_utils::gen_proto!(Invite1GreeterWaitPeerReq, __copy__);
crate::binding_utils::gen_proto!(Invite1GreeterWaitPeerReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite1GreeterWaitPeerReq, __richcmp__, eq);

#[pymethods]
impl Invite1GreeterWaitPeerReq {
    #[new]
    fn new(token: InvitationToken, greeter_public_key: PublicKey) -> PyResult<Self> {
        let token = token.0;
        let greeter_public_key = greeter_public_key.0;
        Ok(Self(invite_1_greeter_wait_peer::Req {
            token,
            greeter_public_key,
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(&self) -> InvitationToken {
        InvitationToken(self.0.token)
    }

    #[getter]
    fn greeter_public_key(&self) -> PublicKey {
        PublicKey(self.0.greeter_public_key.clone())
    }
}

gen_rep!(
    invite_1_greeter_wait_peer,
    Invite1GreeterWaitPeerRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState],
);

#[pyclass(extends=Invite1GreeterWaitPeerRep)]
pub(crate) struct Invite1GreeterWaitPeerRepOk;

#[pymethods]
impl Invite1GreeterWaitPeerRepOk {
    #[new]
    fn new(claimer_public_key: PublicKey) -> PyResult<(Self, Invite1GreeterWaitPeerRep)> {
        let claimer_public_key = claimer_public_key.0;
        Ok((
            Self,
            Invite1GreeterWaitPeerRep(invite_1_greeter_wait_peer::Rep::Ok { claimer_public_key }),
        ))
    }

    #[getter]
    fn claimer_public_key(_self: PyRef<'_, Self>) -> PyResult<PublicKey> {
        match &_self.as_ref().0 {
            invite_1_greeter_wait_peer::Rep::Ok { claimer_public_key } => {
                Ok(PublicKey(claimer_public_key.clone()))
            }
            _ => Err(PyNotImplementedError::new_err("")),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite2aClaimerSendHashedNonceReq(pub invite_2a_claimer_send_hashed_nonce::Req);

crate::binding_utils::gen_proto!(Invite2aClaimerSendHashedNonceReq, __repr__);
crate::binding_utils::gen_proto!(Invite2aClaimerSendHashedNonceReq, __copy__);
crate::binding_utils::gen_proto!(Invite2aClaimerSendHashedNonceReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite2aClaimerSendHashedNonceReq, __richcmp__, eq);

#[pymethods]
impl Invite2aClaimerSendHashedNonceReq {
    #[new]
    fn new(greeter_user_id: UserID, claimer_hashed_nonce: HashDigest) -> PyResult<Self> {
        let greeter_user_id = Maybe::Present(greeter_user_id.0);
        let claimer_hashed_nonce = claimer_hashed_nonce.0;
        Ok(Self(invite_2a_claimer_send_hashed_nonce::Req {
            greeter_user_id,
            claimer_hashed_nonce,
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn greeter_user_id(&self) -> Option<UserID> {
        match &self.0.greeter_user_id {
            Maybe::Present(x) => Some(UserID(x.clone())),
            Maybe::Absent => None,
        }
    }

    #[getter]
    fn claimer_hashed_nonce(_self: PyRef<'_, Self>) -> HashDigest {
        HashDigest(_self.0.claimer_hashed_nonce.clone())
    }
}

gen_rep!(
    invite_2a_claimer_send_hashed_nonce,
    Invite2aClaimerSendHashedNonceRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState],
);

#[pyclass(extends=Invite2aClaimerSendHashedNonceRep)]
pub(crate) struct Invite2aClaimerSendHashedNonceRepOk;

#[pymethods]
impl Invite2aClaimerSendHashedNonceRepOk {
    #[new]
    fn new(greeter_nonce: BytesWrapper) -> PyResult<(Self, Invite2aClaimerSendHashedNonceRep)> {
        crate::binding_utils::unwrap_bytes!(greeter_nonce);
        Ok((
            Self,
            Invite2aClaimerSendHashedNonceRep(invite_2a_claimer_send_hashed_nonce::Rep::Ok {
                greeter_nonce,
            }),
        ))
    }

    #[getter]
    fn greeter_nonce<'py>(_self: PyRef<'py, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        let greeter_nonce = match &_self.as_ref().0 {
            invite_2a_claimer_send_hashed_nonce::Rep::Ok { greeter_nonce } => greeter_nonce,
            _ => return Err(PyNotImplementedError::new_err("")),
        };

        Ok(PyBytes::new(py, greeter_nonce))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite2aGreeterGetHashedNonceReq(pub invite_2a_greeter_get_hashed_nonce::Req);

crate::binding_utils::gen_proto!(Invite2aGreeterGetHashedNonceReq, __repr__);
crate::binding_utils::gen_proto!(Invite2aGreeterGetHashedNonceReq, __copy__);
crate::binding_utils::gen_proto!(Invite2aGreeterGetHashedNonceReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite2aGreeterGetHashedNonceReq, __richcmp__, eq);

#[pymethods]
impl Invite2aGreeterGetHashedNonceReq {
    #[new]
    fn new(token: InvitationToken) -> PyResult<Self> {
        let token = token.0;
        Ok(Self(invite_2a_greeter_get_hashed_nonce::Req { token }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(&self) -> PyResult<InvitationToken> {
        Ok(InvitationToken(self.0.token))
    }
}

gen_rep!(
    invite_2a_greeter_get_hashed_nonce,
    Invite2aGreeterGetHashedNonceRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite2aGreeterGetHashedNonceRep)]
pub(crate) struct Invite2aGreeterGetHashedNonceRepOk;

#[pymethods]
impl Invite2aGreeterGetHashedNonceRepOk {
    #[new]
    fn new(claimer_hashed_nonce: HashDigest) -> PyResult<(Self, Invite2aGreeterGetHashedNonceRep)> {
        let claimer_hashed_nonce = claimer_hashed_nonce.0;
        Ok((
            Self,
            Invite2aGreeterGetHashedNonceRep(invite_2a_greeter_get_hashed_nonce::Rep::Ok {
                claimer_hashed_nonce,
            }),
        ))
    }

    #[getter]
    fn claimer_hashed_nonce(_self: PyRef<'_, Self>) -> PyResult<HashDigest> {
        match &_self.as_ref().0 {
            invite_2a_greeter_get_hashed_nonce::Rep::Ok {
                claimer_hashed_nonce,
            } => Ok(HashDigest(claimer_hashed_nonce.clone())),
            _ => Err(PyNotImplementedError::new_err("")),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite2bClaimerSendNonceReq(pub invite_2b_claimer_send_nonce::Req);

crate::binding_utils::gen_proto!(Invite2bClaimerSendNonceReq, __repr__);
crate::binding_utils::gen_proto!(Invite2bClaimerSendNonceReq, __copy__);
crate::binding_utils::gen_proto!(Invite2bClaimerSendNonceReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite2bClaimerSendNonceReq, __richcmp__, eq);

#[pymethods]
impl Invite2bClaimerSendNonceReq {
    #[new]
    fn new(greeter_user_id: UserID, claimer_nonce: BytesWrapper) -> PyResult<Self> {
        crate::binding_utils::unwrap_bytes!(claimer_nonce);
        let greeter_user_id = Maybe::Present(greeter_user_id.0);
        Ok(Self(invite_2b_claimer_send_nonce::Req {
            greeter_user_id,
            claimer_nonce,
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn greeter_user_id(&self) -> Option<UserID> {
        match &self.0.greeter_user_id {
            Maybe::Present(x) => Some(UserID(x.clone())),
            Maybe::Absent => None,
        }
    }
    #[getter]
    fn claimer_nonce<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        Ok(PyBytes::new(py, &_self.0.claimer_nonce))
    }
}

gen_rep!(
    invite_2b_claimer_send_nonce,
    Invite2bClaimerSendNonceRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite2bClaimerSendNonceRep)]
pub(crate) struct Invite2bClaimerSendNonceRepOk;

#[pymethods]
impl Invite2bClaimerSendNonceRepOk {
    #[new]
    fn new() -> PyResult<(Self, Invite2bClaimerSendNonceRep)> {
        Ok((
            Self,
            Invite2bClaimerSendNonceRep(invite_2b_claimer_send_nonce::Rep::Ok),
        ))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite2bGreeterSendNonceReq(pub invite_2b_greeter_send_nonce::Req);

crate::binding_utils::gen_proto!(Invite2bGreeterSendNonceReq, __repr__);
crate::binding_utils::gen_proto!(Invite2bGreeterSendNonceReq, __copy__);
crate::binding_utils::gen_proto!(Invite2bGreeterSendNonceReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite2bGreeterSendNonceReq, __richcmp__, eq);

#[pymethods]
impl Invite2bGreeterSendNonceReq {
    #[new]
    fn new(token: InvitationToken, greeter_nonce: BytesWrapper) -> PyResult<Self> {
        crate::binding_utils::unwrap_bytes!(greeter_nonce);
        let token = token.0;
        Ok(Self(invite_2b_greeter_send_nonce::Req {
            token,
            greeter_nonce,
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(_self: PyRef<'_, Self>) -> PyResult<InvitationToken> {
        Ok(InvitationToken(_self.0.token))
    }

    #[getter]
    fn greeter_nonce<'py>(_self: PyRef<'py, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        Ok(PyBytes::new(py, &_self.0.greeter_nonce))
    }
}

gen_rep!(
    invite_2b_greeter_send_nonce,
    Invite2bGreeterSendNonceRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite2bGreeterSendNonceRep)]
pub(crate) struct Invite2bGreeterSendNonceRepOk;

#[pymethods]
impl Invite2bGreeterSendNonceRepOk {
    #[new]
    fn new(claimer_nonce: BytesWrapper) -> PyResult<(Self, Invite2bGreeterSendNonceRep)> {
        crate::binding_utils::unwrap_bytes!(claimer_nonce);
        Ok((
            Self,
            Invite2bGreeterSendNonceRep(invite_2b_greeter_send_nonce::Rep::Ok { claimer_nonce }),
        ))
    }

    #[getter]
    fn claimer_nonce<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        let claimer_nonce = match &_self.as_ref().0 {
            invite_2b_greeter_send_nonce::Rep::Ok { claimer_nonce } => claimer_nonce,
            _ => return Err(PyNotImplementedError::new_err("")),
        };

        Ok(PyBytes::new(py, claimer_nonce))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite3aClaimerSignifyTrustReq(pub invite_3a_claimer_signify_trust::Req);

crate::binding_utils::gen_proto!(Invite3aClaimerSignifyTrustReq, __repr__);
crate::binding_utils::gen_proto!(Invite3aClaimerSignifyTrustReq, __copy__);
crate::binding_utils::gen_proto!(Invite3aClaimerSignifyTrustReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite3aClaimerSignifyTrustReq, __richcmp__, eq);

#[pymethods]
impl Invite3aClaimerSignifyTrustReq {
    #[new]
    fn new(greeter_user_id: UserID) -> PyResult<Self> {
        let greeter_user_id = Maybe::Present(greeter_user_id.0);
        Ok(Self(invite_3a_claimer_signify_trust::Req {
            greeter_user_id,
        }))
    }

    #[getter]
    fn greeter_user_id(&self) -> Option<UserID> {
        match &self.0.greeter_user_id {
            Maybe::Present(x) => Some(UserID(x.clone())),
            Maybe::Absent => None,
        }
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }
}

gen_rep!(
    invite_3a_claimer_signify_trust,
    Invite3aClaimerSignifyTrustRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite3aClaimerSignifyTrustRep)]
pub(crate) struct Invite3aClaimerSignifyTrustRepOk;

#[pymethods]
impl Invite3aClaimerSignifyTrustRepOk {
    #[new]
    fn new() -> PyResult<(Self, Invite3aClaimerSignifyTrustRep)> {
        Ok((
            Self,
            Invite3aClaimerSignifyTrustRep(invite_3a_claimer_signify_trust::Rep::Ok),
        ))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite3aGreeterWaitPeerTrustReq(pub invite_3a_greeter_wait_peer_trust::Req);

crate::binding_utils::gen_proto!(Invite3aGreeterWaitPeerTrustReq, __repr__);
crate::binding_utils::gen_proto!(Invite3aGreeterWaitPeerTrustReq, __copy__);
crate::binding_utils::gen_proto!(Invite3aGreeterWaitPeerTrustReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite3aGreeterWaitPeerTrustReq, __richcmp__, eq);

#[pymethods]
impl Invite3aGreeterWaitPeerTrustReq {
    #[new]
    fn new(token: InvitationToken) -> PyResult<Self> {
        let token = token.0;
        Ok(Self(invite_3a_greeter_wait_peer_trust::Req { token }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(_self: PyRef<'_, Self>) -> PyResult<InvitationToken> {
        Ok(InvitationToken(_self.0.token))
    }
}

gen_rep!(
    invite_3a_greeter_wait_peer_trust,
    Invite3aGreeterWaitPeerTrustRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite3aGreeterWaitPeerTrustRep)]
pub(crate) struct Invite3aGreeterWaitPeerTrustRepOk;

#[pymethods]
impl Invite3aGreeterWaitPeerTrustRepOk {
    #[new]
    fn new() -> PyResult<(Self, Invite3aGreeterWaitPeerTrustRep)> {
        Ok((
            Self,
            Invite3aGreeterWaitPeerTrustRep(invite_3a_greeter_wait_peer_trust::Rep::Ok),
        ))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite3bClaimerWaitPeerTrustReq(pub invite_3b_claimer_wait_peer_trust::Req);

crate::binding_utils::gen_proto!(Invite3bClaimerWaitPeerTrustReq, __repr__);
crate::binding_utils::gen_proto!(Invite3bClaimerWaitPeerTrustReq, __copy__);
crate::binding_utils::gen_proto!(Invite3bClaimerWaitPeerTrustReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite3bClaimerWaitPeerTrustReq, __richcmp__, eq);

#[pymethods]
impl Invite3bClaimerWaitPeerTrustReq {
    #[new]
    fn new(greeter_user_id: UserID) -> PyResult<Self> {
        let greeter_user_id = Maybe::Present(greeter_user_id.0);
        Ok(Self(invite_3b_claimer_wait_peer_trust::Req {
            greeter_user_id,
        }))
    }

    #[getter]
    fn greeter_user_id(&self) -> Option<UserID> {
        match &self.0.greeter_user_id {
            Maybe::Present(x) => Some(UserID(x.clone())),
            Maybe::Absent => None,
        }
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }
}

gen_rep!(
    invite_3b_claimer_wait_peer_trust,
    Invite3bClaimerWaitPeerTrustRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite3bClaimerWaitPeerTrustRep)]
pub(crate) struct Invite3bClaimerWaitPeerTrustRepOk;

#[pymethods]
impl Invite3bClaimerWaitPeerTrustRepOk {
    #[new]
    fn new() -> PyResult<(Self, Invite3bClaimerWaitPeerTrustRep)> {
        Ok((
            Self,
            Invite3bClaimerWaitPeerTrustRep(invite_3b_claimer_wait_peer_trust::Rep::Ok),
        ))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite3bGreeterSignifyTrustReq(pub invite_3b_greeter_signify_trust::Req);

crate::binding_utils::gen_proto!(Invite3bGreeterSignifyTrustReq, __repr__);
crate::binding_utils::gen_proto!(Invite3bGreeterSignifyTrustReq, __copy__);
crate::binding_utils::gen_proto!(Invite3bGreeterSignifyTrustReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite3bGreeterSignifyTrustReq, __richcmp__, eq);

#[pymethods]
impl Invite3bGreeterSignifyTrustReq {
    #[new]
    fn new(token: InvitationToken) -> PyResult<Self> {
        let token = token.0;
        Ok(Self(invite_3b_greeter_signify_trust::Req { token }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(_self: PyRef<'_, Self>) -> PyResult<InvitationToken> {
        Ok(InvitationToken(_self.0.token))
    }
}

gen_rep!(
    invite_3b_greeter_signify_trust,
    Invite3bGreeterSignifyTrustRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite3bGreeterSignifyTrustRep)]
pub(crate) struct Invite3bGreeterSignifyTrustRepOk;

#[pymethods]
impl Invite3bGreeterSignifyTrustRepOk {
    #[new]
    fn new() -> PyResult<(Self, Invite3bGreeterSignifyTrustRep)> {
        Ok((
            Self,
            Invite3bGreeterSignifyTrustRep(invite_3b_greeter_signify_trust::Rep::Ok),
        ))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite4ClaimerCommunicateReq(pub invite_4_claimer_communicate::Req);

crate::binding_utils::gen_proto!(Invite4ClaimerCommunicateReq, __repr__);
crate::binding_utils::gen_proto!(Invite4ClaimerCommunicateReq, __copy__);
crate::binding_utils::gen_proto!(Invite4ClaimerCommunicateReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite4ClaimerCommunicateReq, __richcmp__, eq);

#[pymethods]
impl Invite4ClaimerCommunicateReq {
    #[new]
    fn new(greeter_user_id: UserID, payload: BytesWrapper) -> PyResult<Self> {
        crate::binding_utils::unwrap_bytes!(payload);
        let greeter_user_id = Maybe::Present(greeter_user_id.0);
        Ok(Self(invite_4_claimer_communicate::Req {
            greeter_user_id,
            payload,
        }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn greeter_user_id(&self) -> Option<UserID> {
        match &self.0.greeter_user_id {
            Maybe::Present(x) => Some(UserID(x.clone())),
            Maybe::Absent => None,
        }
    }

    #[getter]
    fn payload<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        Ok(PyBytes::new(py, &_self.0.payload))
    }
}

gen_rep!(
    invite_4_claimer_communicate,
    Invite4ClaimerCommunicateRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState],
);

#[pyclass(extends=Invite4ClaimerCommunicateRep)]
pub(crate) struct Invite4ClaimerCommunicateRepOk;

#[pymethods]
impl Invite4ClaimerCommunicateRepOk {
    #[new]
    fn new(payload: BytesWrapper) -> PyResult<(Self, Invite4ClaimerCommunicateRep)> {
        crate::binding_utils::unwrap_bytes!(payload);
        Ok((
            Self,
            Invite4ClaimerCommunicateRep(invite_4_claimer_communicate::Rep::Ok { payload }),
        ))
    }

    #[getter]
    fn payload<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        let payload = match &_self.as_ref().0 {
            invite_4_claimer_communicate::Rep::Ok { payload } => payload,
            _ => return Err(PyNotImplementedError::new_err("")),
        };

        Ok(PyBytes::new(py, payload))
    }
}

#[pyclass]
#[derive(Clone)]
pub(crate) struct Invite4GreeterCommunicateReq(pub invite_4_greeter_communicate::Req);

crate::binding_utils::gen_proto!(Invite4GreeterCommunicateReq, __repr__);
crate::binding_utils::gen_proto!(Invite4GreeterCommunicateReq, __copy__);
crate::binding_utils::gen_proto!(Invite4GreeterCommunicateReq, __deepcopy__);
crate::binding_utils::gen_proto!(Invite4GreeterCommunicateReq, __richcmp__, eq);

#[pymethods]
impl Invite4GreeterCommunicateReq {
    #[new]
    fn new(token: InvitationToken, payload: BytesWrapper) -> PyResult<Self> {
        crate::binding_utils::unwrap_bytes!(payload);
        let token = token.0;
        Ok(Self(invite_4_greeter_communicate::Req { token, payload }))
    }

    fn dump<'py>(&self, py: Python<'py>) -> ProtocolResult<&'py PyBytes> {
        Ok(PyBytes::new(
            py,
            &self.0.clone().dump().map_err(|e| {
                ProtocolErrorFields(libparsec::protocol::ProtocolError::EncodingError {
                    exc: e.to_string(),
                })
            })?,
        ))
    }

    #[getter]
    fn token(_self: PyRef<'_, Self>) -> PyResult<InvitationToken> {
        Ok(InvitationToken(_self.0.token))
    }

    #[getter]
    fn payload<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        Ok(PyBytes::new(py, &_self.0.payload))
    }
}

gen_rep!(
    invite_4_greeter_communicate,
    Invite4GreeterCommunicateRep,
    { .. },
    [NotFound],
    [AlreadyDeleted],
    [InvalidState]
);

#[pyclass(extends=Invite4GreeterCommunicateRep)]
pub(crate) struct Invite4GreeterCommunicateRepOk;

#[pymethods]
impl Invite4GreeterCommunicateRepOk {
    #[new]
    fn new(payload: BytesWrapper) -> PyResult<(Self, Invite4GreeterCommunicateRep)> {
        crate::binding_utils::unwrap_bytes!(payload);
        Ok((
            Self,
            Invite4GreeterCommunicateRep(invite_4_greeter_communicate::Rep::Ok { payload }),
        ))
    }

    #[getter]
    fn payload<'py>(_self: PyRef<'_, Self>, py: Python<'py>) -> PyResult<&'py PyBytes> {
        let payload = match &_self.as_ref().0 {
            invite_4_greeter_communicate::Rep::Ok { payload } => payload,
            _ => return Err(PyNotImplementedError::new_err("")),
        };

        Ok(PyBytes::new(py, payload))
    }
}