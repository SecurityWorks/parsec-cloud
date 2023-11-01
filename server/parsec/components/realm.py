# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import assert_never

from parsec._parsec import (
    DateTime,
    DeviceID,
    OrganizationID,
    RealmRole,
    RealmRoleCertificate,
    UserID,
    VerifyKey,
    VlobID,
    authenticated_cmds,
)
from parsec.api import api
from parsec.ballpark import (
    RequireGreaterTimestamp,
    TimestampOutOfBallpark,
    timestamps_in_the_ballpark,
)
from parsec.client_context import AuthenticatedClientContext


@dataclass(slots=True)
class RealmStats:
    blocks_size: int
    vlobs_size: int


@dataclass(slots=True, repr=False)
class RealmGrantedRole:
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.user_id.str} {self.role})"

    certificate: bytes
    realm_id: VlobID
    user_id: UserID
    role: RealmRole | None
    granted_by: DeviceID | None
    granted_on: DateTime


RealmCreateValidateBadOutcome = Enum(
    "RealmCreateValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "TIMESTAMP_MISMATCH",
        "INVALID_ROLE",
        "USER_ID_MISMATCH",
    ),
)


def realm_create_validate(
    now: DateTime,
    expected_author: DeviceID,
    author_verify_key: VerifyKey,
    realm_role_certificate: bytes,
) -> RealmRoleCertificate | TimestampOutOfBallpark | RealmCreateValidateBadOutcome:
    try:
        data = RealmRoleCertificate.verify_and_load(
            realm_role_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return RealmCreateValidateBadOutcome.INVALID_CERTIFICATE

    match timestamps_in_the_ballpark(data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    assert (
        data.author is not None
    )  # TODO: remove me once RealmRoleCertificate's author is corrected
    if data.author.user_id != data.user_id:
        return RealmCreateValidateBadOutcome.USER_ID_MISMATCH

    if data.role != RealmRole.OWNER:
        return RealmCreateValidateBadOutcome.INVALID_ROLE

    return data


RealmShareValidateBadOutcome = Enum(
    "RealmShareValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "TIMESTAMP_MISMATCH",
        "CANNOT_SELF_SHARE",
    ),
)


def realm_share_validate(
    now: DateTime,
    expected_author: DeviceID,
    author_verify_key: VerifyKey,
    realm_role_certificate: bytes,
) -> RealmRoleCertificate | TimestampOutOfBallpark | RealmShareValidateBadOutcome:
    try:
        data = RealmRoleCertificate.verify_and_load(
            realm_role_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return RealmShareValidateBadOutcome.INVALID_CERTIFICATE

    match timestamps_in_the_ballpark(data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    if data.author == data.user_id:
        return RealmShareValidateBadOutcome.CANNOT_SELF_SHARE

    return data


RealmUnshareValidateBadOutcome = Enum(
    "RealmUnshareValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "TIMESTAMP_MISMATCH",
        "INVALID_ROLE",
        "CANNOT_SELF_UNSHARE",
    ),
)


def realm_unshare_validate(
    now: DateTime,
    expected_author: DeviceID,
    author_verify_key: VerifyKey,
    realm_role_certificate: bytes,
) -> RealmRoleCertificate | TimestampOutOfBallpark | RealmUnshareValidateBadOutcome:
    try:
        data = RealmRoleCertificate.verify_and_load(
            realm_role_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return RealmUnshareValidateBadOutcome.INVALID_CERTIFICATE

    match timestamps_in_the_ballpark(data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    if data.author == data.user_id:
        return RealmUnshareValidateBadOutcome.CANNOT_SELF_UNSHARE

    if data.role is not None:
        return RealmUnshareValidateBadOutcome.INVALID_ROLE

    return data


RealmCreateStoreBadOutcome = Enum(
    "RealmCreateStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "REALM_ALREADY_EXISTS",
    ),
)
RealmShareStoreBadOutcome = Enum(
    "RealmShareStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "REALM_NOT_FOUND",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "USER_NOT_FOUND",
        "USER_REVOKED",
        "ROLE_INCOMPATIBLE_WITH_OUTSIDER",
        "ROLE_ALREADY_GRANTED",
        "BAD_KEY_INDEX",
    ),
)
RealmUnshareStoreBadOutcome = Enum(
    "RealmUnshareStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "REALM_NOT_FOUND",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "USER_NOT_FOUND",
        "USER_ALREADY_UNSHARED",
    ),
)
RealmGetStatsAsUserBadOutcome = Enum(
    "RealmGetStatsAsBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "REALM_NOT_FOUND",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
    ),
)
RealmGetStatsBadOutcome = Enum(
    "RealmGetStatsBadOutcome", ("ORGANIZATION_NOT_FOUND", "REALM_NOT_FOUND")
)
RealmGetCurrentRealmsForUserBadOutcome = Enum(
    "RealmGetRealmsForUserBadOutcome", ("ORGANIZATION_NOT_FOUND", "USER_NOT_FOUND")
)
RealmDumpRealmsGrantedRolesBadOutcome = Enum(
    "RealmDumpRealmsGrantedRolesBadOutcome", ("ORGANIZATION_NOT_FOUND",)
)


class BaseRealmComponent:
    #
    # Public methods
    #

    async def create(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_role_certificate: bytes,
    ) -> (
        RealmRoleCertificate
        | RealmCreateValidateBadOutcome
        | TimestampOutOfBallpark
        | RealmCreateStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def share(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_role_certificate: bytes,
        recipient_keys_bundle_access: bytes,
    ) -> (
        RealmRoleCertificate
        | RealmShareValidateBadOutcome
        | TimestampOutOfBallpark
        | RealmShareStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def unshare(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_role_certificate: bytes,
    ) -> (
        RealmRoleCertificate
        | RealmUnshareValidateBadOutcome
        | TimestampOutOfBallpark
        | RealmUnshareStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def get_stats_as_user(
        self, organization_id: OrganizationID, author: DeviceID, realm_id: VlobID
    ) -> RealmStats | RealmGetStatsAsUserBadOutcome:
        raise NotImplementedError

    async def get_stats(
        self, organization_id: OrganizationID, realm_id: VlobID
    ) -> RealmStats | RealmGetStatsBadOutcome:
        raise NotImplementedError

    async def get_current_realms_for_user(
        self, organization_id: OrganizationID, user: UserID
    ) -> dict[VlobID, RealmRole] | RealmGetCurrentRealmsForUserBadOutcome:
        raise NotImplementedError

    async def dump_realms_granted_roles(
        self, organization_id: OrganizationID
    ) -> list[RealmGrantedRole] | RealmDumpRealmsGrantedRolesBadOutcome:
        raise NotImplementedError

    #
    # API commands
    #

    @api
    async def api_realm_create(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.realm_create.Req,
    ) -> authenticated_cmds.latest.realm_create.Rep:
        outcome = await self.create(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            realm_role_certificate=req.realm_role_certificate,
        )
        match outcome:
            case RealmRoleCertificate():
                return authenticated_cmds.latest.realm_create.RepOk()
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.realm_create.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.realm_create.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RealmCreateValidateBadOutcome():
                return authenticated_cmds.latest.realm_create.RepInvalidCertificate()
            case RealmCreateStoreBadOutcome.REALM_ALREADY_EXISTS:
                return authenticated_cmds.latest.realm_create.RepRealmAlreadyExists()
            case RealmCreateStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case RealmCreateStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case RealmCreateStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case RealmCreateStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_realm_share(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.realm_share.Req,
    ) -> authenticated_cmds.latest.realm_share.Rep:
        outcome = await self.share(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            realm_role_certificate=req.realm_role_certificate,
            recipient_keys_bundle_access=req.recipient_keys_bundle_access,
        )
        match outcome:
            case RealmRoleCertificate():
                return authenticated_cmds.latest.realm_share.RepOk()
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.realm_share.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.realm_share.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RealmShareValidateBadOutcome():
                return authenticated_cmds.latest.realm_share.RepInvalidCertificate()
            case RealmShareStoreBadOutcome.BAD_KEY_INDEX:
                return authenticated_cmds.latest.realm_share.RepBadKeyIndex()
            case RealmShareStoreBadOutcome.REALM_NOT_FOUND:
                return authenticated_cmds.latest.realm_share.RepRealmNotFound()
            case RealmShareStoreBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.realm_share.RepAuthorNotAllowed()
            case RealmShareStoreBadOutcome.USER_NOT_FOUND:
                return authenticated_cmds.latest.realm_share.RepUserNotFound()
            case RealmShareStoreBadOutcome.USER_REVOKED:
                return authenticated_cmds.latest.realm_share.RepUserRevoked()
            case RealmShareStoreBadOutcome.ROLE_INCOMPATIBLE_WITH_OUTSIDER:
                return authenticated_cmds.latest.realm_share.RepRoleIncompatibleWithOutsider()
            case RealmShareStoreBadOutcome.ROLE_ALREADY_GRANTED:
                return authenticated_cmds.latest.realm_share.RepRoleAlreadyGranted()
            case RealmShareStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case RealmShareStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case RealmShareStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case RealmShareStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_realm_unshare(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.realm_unshare.Req,
    ) -> authenticated_cmds.latest.realm_unshare.Rep:
        outcome = await self.unshare(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            realm_role_certificate=req.realm_role_certificate,
        )
        match outcome:
            case RealmRoleCertificate():
                return authenticated_cmds.latest.realm_unshare.RepOk()
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.realm_unshare.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.realm_unshare.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RealmUnshareValidateBadOutcome():
                return authenticated_cmds.latest.realm_unshare.RepInvalidCertificate()
            case RealmUnshareStoreBadOutcome.REALM_NOT_FOUND:
                return authenticated_cmds.latest.realm_unshare.RepRealmNotFound()
            case RealmUnshareStoreBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.realm_unshare.RepAuthorNotAllowed()
            case RealmUnshareStoreBadOutcome.USER_NOT_FOUND:
                return authenticated_cmds.latest.realm_unshare.RepUserNotFound()
            case RealmUnshareStoreBadOutcome.USER_ALREADY_UNSHARED:
                return authenticated_cmds.latest.realm_unshare.RepUserAlreadyUnshared()
            case RealmUnshareStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case RealmUnshareStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case RealmUnshareStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case RealmUnshareStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)
