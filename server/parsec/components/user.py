# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import assert_never

from parsec._parsec import (
    DateTime,
    DeviceCertificate,
    DeviceID,
    DeviceName,
    OrganizationID,
    RevokedUserCertificate,
    UserCertificate,
    UserID,
    UserProfile,
    UserUpdateCertificate,
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
class CertificatesBundle:
    common: list[bytes]
    sequester: list[bytes]
    shamir: list[bytes]
    realm: dict[VlobID, list[bytes]]


@dataclass(slots=True)
class UserDump:
    user_id: UserID
    devices: list[DeviceName]
    current_profile: UserProfile
    is_revoked: bool


UserCreateUserValidateBadOutcome = Enum(
    "UserCreateUserValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "TIMESTAMP_MISMATCH",
        "USER_ID_MISMATCH",
        "INVALID_REDACTED",
        "REDACTED_MISMATCH",
    ),
)


def user_create_user_validate(
    now: DateTime,
    expected_author: DeviceID | None,
    author_verify_key: VerifyKey,
    user_certificate: bytes,
    device_certificate: bytes,
    redacted_user_certificate: bytes,
    redacted_device_certificate: bytes,
) -> (
    tuple[UserCertificate, DeviceCertificate]
    | TimestampOutOfBallpark
    | UserCreateUserValidateBadOutcome
):
    try:
        d_data = DeviceCertificate.verify_and_load(
            device_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )
        u_data = UserCertificate.verify_and_load(
            user_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )
        ru_data = UserCertificate.verify_and_load(
            redacted_user_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )
        rd_data = DeviceCertificate.verify_and_load(
            redacted_device_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return UserCreateUserValidateBadOutcome.INVALID_CERTIFICATE

    if u_data.timestamp != d_data.timestamp:
        return UserCreateUserValidateBadOutcome.TIMESTAMP_MISMATCH

    match timestamps_in_the_ballpark(u_data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    if u_data.user_id != d_data.device_id.user_id:
        return UserCreateUserValidateBadOutcome.USER_ID_MISMATCH

    if not ru_data.is_redacted:
        return UserCreateUserValidateBadOutcome.INVALID_REDACTED

    if not rd_data.is_redacted:
        return UserCreateUserValidateBadOutcome.INVALID_REDACTED

    if not u_data.redacted_compare(ru_data):
        return UserCreateUserValidateBadOutcome.REDACTED_MISMATCH

    if not d_data.redacted_compare(rd_data):
        return UserCreateUserValidateBadOutcome.REDACTED_MISMATCH

    return u_data, d_data


UserCreateDeviceValidateBadOutcome = Enum(
    "UserCreateDeviceValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "USER_ID_MISMATCH",
        "INVALID_REDACTED",
        "REDACTED_MISMATCH",
    ),
)


def user_create_device_validate(
    now: DateTime,
    expected_author: DeviceID,
    author_verify_key: VerifyKey,
    device_certificate: bytes,
    redacted_device_certificate: bytes,
) -> DeviceCertificate | TimestampOutOfBallpark | UserCreateDeviceValidateBadOutcome:
    try:
        data = DeviceCertificate.verify_and_load(
            device_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

        redacted_data = DeviceCertificate.verify_and_load(
            redacted_device_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return UserCreateDeviceValidateBadOutcome.INVALID_CERTIFICATE

    match timestamps_in_the_ballpark(data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    if data.device_id.user_id != expected_author.user_id:
        return UserCreateDeviceValidateBadOutcome.USER_ID_MISMATCH

    if not redacted_data.is_redacted:
        return UserCreateDeviceValidateBadOutcome.INVALID_REDACTED

    if not data.redacted_compare(redacted_data):
        return UserCreateDeviceValidateBadOutcome.REDACTED_MISMATCH

    return data


UserRevokeUserValidateBadOutcome = Enum(
    "UserRevokeUserValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "INVALID_USER_PROFILE",
        "CANNOT_SELF_REVOKE",
    ),
)


def user_revoke_user_validate(
    now: DateTime,
    expected_author: DeviceID,
    author_verify_key: VerifyKey,
    revoked_user_certificate: bytes,
) -> RevokedUserCertificate | TimestampOutOfBallpark | UserRevokeUserValidateBadOutcome:
    try:
        data = RevokedUserCertificate.verify_and_load(
            signed=revoked_user_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return UserRevokeUserValidateBadOutcome.INVALID_CERTIFICATE

    match timestamps_in_the_ballpark(data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    if expected_author.user_id == data.user_id:
        return UserRevokeUserValidateBadOutcome.CANNOT_SELF_REVOKE

    return data


UserUpdateUserValidateBadOutcome = Enum(
    "UserUpdateUserValidateBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "INVALID_USER_PROFILE",
        "CANNOT_SELF_REVOKE",
    ),
)


def user_update_user_validate(
    now: DateTime,
    expected_author: DeviceID,
    author_verify_key: VerifyKey,
    user_update_certificate: bytes,
) -> UserUpdateCertificate | TimestampOutOfBallpark | UserUpdateUserValidateBadOutcome:
    try:
        data = UserUpdateCertificate.verify_and_load(
            signed=user_update_certificate,
            author_verify_key=author_verify_key,
            expected_author=expected_author,
        )

    except ValueError:
        return UserUpdateUserValidateBadOutcome.INVALID_CERTIFICATE

    match timestamps_in_the_ballpark(data.timestamp, now):
        case TimestampOutOfBallpark() as error:
            return error

    if expected_author.user_id == data.user_id:
        return UserUpdateUserValidateBadOutcome.CANNOT_SELF_REVOKE

    return data


UserCreateUserStoreBadOutcome = Enum(
    "UserCreateUserStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "ACTIVE_USERS_LIMIT_REACHED",
        "USER_ALREADY_EXISTS",
        "HUMAN_HANDLE_ALREADY_TAKEN",
    ),
)
UserCreateDeviceStoreBadOutcome = Enum(
    "UserCreateDeviceStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "DEVICE_ALREADY_EXISTS",
    ),
)
UserRevokeUserStoreBadOutcome = Enum(
    "UserRevokeUserStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "USER_NOT_FOUND",
        "USER_ALREADY_REVOKED",
    ),
)
UserUpdateUserStoreBadOutcome = Enum(
    "UserUpdateUserStoreBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "USER_NOT_FOUND",
        "USER_REVOKED",
        "USER_NO_CHANGES",
    ),
)
UserGetCertificatesAsUserBadOutcome = Enum(
    "UserGetCertificatesBadOutcome",
    ("ORGANIZATION_NOT_FOUND", "ORGANIZATION_EXPIRED", "AUTHOR_NOT_FOUND", "AUTHOR_REVOKED"),
)
UserGetActiveDeviceVerifyKeyBadOutcome = Enum(
    "UserGetActiveDeviceVerifyKeyBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "DEVICE_NOT_FOUND",
        "USER_REVOKED",
    ),
)


class BaseUserComponent:
    #
    # Public methods
    #

    async def create_user(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        author_verify_key: VerifyKey,
        user_certificate: bytes,
        redacted_user_certificate: bytes,
        device_certificate: bytes,
        redacted_device_certificate: bytes,
    ) -> (
        tuple[UserCertificate, DeviceCertificate]
        | UserCreateUserValidateBadOutcome
        | UserCreateUserStoreBadOutcome
        | TimestampOutOfBallpark
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def create_device(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        author_verify_key: VerifyKey,
        device_certificate: bytes,
        redacted_device_certificate: bytes,
    ) -> (
        DeviceCertificate
        | UserCreateDeviceValidateBadOutcome
        | UserCreateDeviceStoreBadOutcome
        | TimestampOutOfBallpark
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def revoke_user(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        author_verify_key: VerifyKey,
        revoked_user_certificate: bytes,
    ) -> (
        RevokedUserCertificate
        | UserRevokeUserValidateBadOutcome
        | UserRevokeUserStoreBadOutcome
        | TimestampOutOfBallpark
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def update_user(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        author_verify_key: VerifyKey,
        user_update_certificate: bytes,
    ) -> (
        UserUpdateCertificate
        | UserUpdateUserValidateBadOutcome
        | UserUpdateUserStoreBadOutcome
        | TimestampOutOfBallpark
        | RequireGreaterTimestamp
    ):
        raise NotImplementedError

    async def get_certificates_as_user(
        self,
        organization_id: OrganizationID,
        author: UserID,
        common_after: DateTime | None,
        sequester_after: DateTime | None,
        shamir_after: DateTime | None,
        realm_after: dict[VlobID, DateTime],
    ) -> CertificatesBundle | UserGetCertificatesAsUserBadOutcome:
        raise NotImplementedError

    async def get_active_device_verify_key(
        self, organization_id: OrganizationID, device_id: DeviceID
    ) -> VerifyKey | UserGetActiveDeviceVerifyKeyBadOutcome:
        raise NotImplementedError

    async def test_dump_current_users(
        self, organization_id: OrganizationID
    ) -> dict[UserID, UserDump]:
        raise NotImplementedError

    #
    # API commands
    #

    @api
    async def api_certificate_get(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.certificate_get.Req,
    ) -> authenticated_cmds.latest.certificate_get.Rep:
        outcome = await self.get_certificates_as_user(
            client_ctx.organization_id,
            author=client_ctx.device_id.user_id,
            common_after=req.common_after,
            sequester_after=req.sequester_after,
            shamir_after=req.shamir_after,
            realm_after=req.realm_after,
        )
        match outcome:
            case CertificatesBundle() as certificates:
                return authenticated_cmds.latest.certificate_get.RepOk(
                    common_certificates=certificates.common,
                    sequester_certificates=certificates.sequester,
                    shamir_certificates=certificates.shamir,
                    realm_certificates=certificates.realm,
                )
            case UserGetCertificatesAsUserBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case UserGetCertificatesAsUserBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case UserGetCertificatesAsUserBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case UserGetCertificatesAsUserBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_user_create(
        self, client_ctx: AuthenticatedClientContext, req: authenticated_cmds.latest.user_create.Req
    ) -> authenticated_cmds.latest.user_create.Rep:
        outcome = await self.create_user(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            author_verify_key=client_ctx.device_verify_key,
            user_certificate=req.user_certificate,
            redacted_user_certificate=req.redacted_user_certificate,
            device_certificate=req.device_certificate,
            redacted_device_certificate=req.redacted_device_certificate,
        )
        match outcome:
            case (_, _):
                return authenticated_cmds.latest.user_create.RepOk()
            case UserCreateUserStoreBadOutcome.HUMAN_HANDLE_ALREADY_TAKEN:
                return authenticated_cmds.latest.user_create.RepHumanHandleAlreadyTaken()
            case UserCreateUserStoreBadOutcome.USER_ALREADY_EXISTS:
                return authenticated_cmds.latest.user_create.RepUserAlreadyExists()
            case UserCreateUserStoreBadOutcome.ACTIVE_USERS_LIMIT_REACHED:
                return authenticated_cmds.latest.user_create.RepActiveUsersLimitReached()
            case UserCreateUserStoreBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.user_create.RepAuthorNotAllowed()
            case UserCreateUserValidateBadOutcome():
                return authenticated_cmds.latest.user_create.RepInvalidCertificate()
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.user_create.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.user_create.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case UserCreateUserStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case UserCreateUserStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case UserCreateUserStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case UserCreateUserStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_device_create(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.device_create.Req,
    ) -> authenticated_cmds.latest.device_create.Rep:
        outcome = await self.create_device(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            author_verify_key=client_ctx.device_verify_key,
            device_certificate=req.device_certificate,
            redacted_device_certificate=req.redacted_device_certificate,
        )
        match outcome:
            case DeviceCertificate():
                return authenticated_cmds.latest.device_create.RepOk()
            case UserCreateDeviceStoreBadOutcome.DEVICE_ALREADY_EXISTS:
                return authenticated_cmds.latest.device_create.RepDeviceAlreadyExists()
            case UserCreateDeviceValidateBadOutcome():
                return authenticated_cmds.latest.device_create.RepInvalidCertificate()
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.device_create.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.device_create.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case UserCreateDeviceStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case UserCreateDeviceStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case UserCreateDeviceStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case UserCreateDeviceStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_user_update(
        self, client_ctx: AuthenticatedClientContext, req: authenticated_cmds.latest.user_update.Req
    ) -> authenticated_cmds.latest.user_update.Rep:
        outcome = await self.update_user(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            author_verify_key=client_ctx.device_verify_key,
            user_update_certificate=req.user_update_certificate,
        )
        match outcome:
            case UserUpdateCertificate():
                return authenticated_cmds.latest.user_update.RepOk()
            case UserUpdateUserStoreBadOutcome.USER_NOT_FOUND:
                return authenticated_cmds.latest.user_update.RepUserNotFound()
            case UserUpdateUserStoreBadOutcome.USER_REVOKED:
                return authenticated_cmds.latest.user_update.RepUserRevoked()
            case UserUpdateUserStoreBadOutcome.USER_NO_CHANGES:
                return authenticated_cmds.latest.user_update.RepUserNoChanges()
            case UserUpdateUserStoreBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.user_update.RepAuthorNotAllowed()
            case UserUpdateUserValidateBadOutcome():
                return authenticated_cmds.latest.user_update.RepInvalidCertificate()
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.user_update.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.user_update.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case UserUpdateUserStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case UserUpdateUserStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case UserUpdateUserStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case UserUpdateUserStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_user_revoke(
        self, client_ctx: AuthenticatedClientContext, req: authenticated_cmds.latest.user_revoke.Req
    ) -> authenticated_cmds.latest.user_revoke.Rep:
        outcome = await self.revoke_user(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            author_verify_key=client_ctx.device_verify_key,
            revoked_user_certificate=req.revoked_user_certificate,
        )
        match outcome:
            case RevokedUserCertificate():
                return authenticated_cmds.latest.user_revoke.RepOk()
            case UserRevokeUserStoreBadOutcome.USER_NOT_FOUND:
                return authenticated_cmds.latest.user_revoke.RepUserAlreadyRevoked()
            case UserRevokeUserStoreBadOutcome.USER_ALREADY_REVOKED:
                return authenticated_cmds.latest.user_revoke.RepUserAlreadyRevoked()
            case UserRevokeUserStoreBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.user_revoke.RepAuthorNotAllowed()
            case UserRevokeUserValidateBadOutcome():
                return authenticated_cmds.latest.user_revoke.RepInvalidCertificate()
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.user_revoke.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.user_revoke.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case UserRevokeUserStoreBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case UserRevokeUserStoreBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case UserRevokeUserStoreBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case UserRevokeUserStoreBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)
