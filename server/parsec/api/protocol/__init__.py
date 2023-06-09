# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPL-3.0 2016-present Scille SAS
from __future__ import annotations

from parsec._parsec import (
    BlockID,
    DeviceName,
    EnrollmentID,
    InvitationStatus,
    InvitationToken,
    InvitationType,
    RealmID,
    RealmRole,
    SequesterServiceID,
    UserProfile,
    VlobID,
    anonymous_cmds,
    authenticated_cmds,
    invited_cmds,
)
from parsec.api.protocol.base import (
    ApiCommandSerializer,
    IncompatibleAPIVersionsError,
    InvalidMessageError,
    MessageSerializationError,
    packb,
    settle_compatible_versions,
    unpackb,
)

# TODO: Tests should use the json schema instead of this
from parsec.api.protocol.cmds import (
    ANONYMOUS_CMDS,
    AUTHENTICATED_CMDS,
    INVITED_CMDS,
)
from parsec.api.protocol.handshake import (
    AuthenticatedClientHandshake,
    BaseClientHandshake,
    HandshakeBadAdministrationToken,
    HandshakeBadIdentity,
    HandshakeError,
    HandshakeFailedChallenge,
    HandshakeOrganizationExpired,
    HandshakeOutOfBallparkError,
    HandshakeRevokedDevice,
    HandshakeRVKMismatch,
    HandshakeType,
    InvitedClientHandshake,
    ServerHandshake,
)
from parsec.api.protocol.legacy_reexport import *  # noqa: F403
from parsec.api.protocol.types import (
    DeviceID,
    DeviceIDField,
    DeviceLabel,
    DeviceLabelField,
    HumanHandle,
    HumanHandleField,
    InvitationTokenField,
    InvitationTypeField,
    OrganizationID,
    OrganizationIDField,
    UserID,
    UserIDField,
    UserProfileField,
)

__all__ = (
    "AUTHENTICATED_CMDS",
    "INVITED_CMDS",
    "ANONYMOUS_CMDS",
    "authenticated_cmds",
    "invited_cmds",
    "anonymous_cmds",
    "MessageSerializationError",
    "InvalidMessageError",
    "packb",
    "unpackb",
    "HandshakeError",
    "HandshakeFailedChallenge",
    "HandshakeBadAdministrationToken",
    "HandshakeBadIdentity",
    "HandshakeOrganizationExpired",
    "HandshakeRVKMismatch",
    "HandshakeRevokedDevice",
    "HandshakeOutOfBallparkError",
    "ApiCommandSerializer",
    "IncompatibleAPIVersionsError",
    "settle_compatible_versions",
    "ServerHandshake",
    "HandshakeType",
    "BaseClientHandshake",
    "AuthenticatedClientHandshake",
    "InvitedClientHandshake",
    # Types
    "UserID",
    "DeviceID",
    "DeviceName",
    "OrganizationID",
    "HumanHandle",
    "UserIDField",
    "DeviceIDField",
    "OrganizationIDField",
    "HumanHandleField",
    "UserProfileField",
    "UserProfile",
    "DeviceLabelField",
    "DeviceLabel",
    "VlobID",
    "BlockID",
    "RealmID",
    "RealmRole",
    "InvitationToken",
    "InvitationTokenField",
    "InvitationType",
    "InvitationTypeField",
    "InvitationStatus",
    "EnrollmentID",
    "SequesterServiceID",
)
