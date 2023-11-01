# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import assert_never

import httpx
from structlog.stdlib import get_logger

from parsec._parsec import (
    DateTime,
    DeviceID,
    OrganizationID,
    SequesterServiceID,
    UserID,
    VlobID,
    authenticated_cmds,
)
from parsec.api import api
from parsec.ballpark import RequireGreaterTimestamp, TimestampOutOfBallpark
from parsec.client_context import AuthenticatedClientContext

logger = get_logger()


@dataclass(slots=True)
class SequesterServiceNotAvailable:
    service_id: SequesterServiceID


@dataclass(slots=True)
class RejectedBySequesterService:
    service_id: SequesterServiceID
    reason: str


VlobCreateBadOutcome = Enum(
    "VlobCreateBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "REALM_NOT_FOUND",
        "VLOB_ALREADY_EXISTS",
        "ORGANIZATION_NOT_SEQUESTERED",
        "SEQUESTER_INCONSISTENCY",
    ),
)
VlobUpdateBadOutcome = Enum(
    "VlobUpdateBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "VLOB_NOT_FOUND",
        "ORGANIZATION_NOT_SEQUESTERED",
        "SEQUESTER_INCONSISTENCY",
        "SEQUESTER_SERVICE_UNAVAILABLE",
    ),
)
VlobReadAsUserBadOutcome = Enum(
    "VlobReadBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "REALM_NOT_FOUND",
    ),
)
VlobPollChangesAsUserBadOutcome = Enum(
    "VlobPollChangesBadOutcome",
    (
        "ORGANIZATION_NOT_FOUND",
        "ORGANIZATION_EXPIRED",
        "AUTHOR_NOT_FOUND",
        "AUTHOR_REVOKED",
        "AUTHOR_NOT_ALLOWED",
        "REALM_NOT_FOUND",
    ),
)
VlobListVersionsBadOutcome = Enum("VlobListVersionsBadOutcome", ("ORGANIZATION_NOT_FOUND",))


class BaseVlobComponent:
    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client

    #
    # Public methods
    #

    async def create(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_id: VlobID,
        vlob_id: VlobID,
        timestamp: DateTime,
        blob: bytes,
        # Sequester is a special case, so gives it a default version to simplify tests
        sequester_blob: dict[SequesterServiceID, bytes] | None = None,
    ) -> (
        None
        | VlobCreateBadOutcome
        | TimestampOutOfBallpark
        | RequireGreaterTimestamp
        | RejectedBySequesterService
        | SequesterServiceNotAvailable
    ):
        raise NotImplementedError

    async def update(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        vlob_id: VlobID,
        version: int,
        timestamp: DateTime,
        blob: bytes,
        # Sequester is a special case, so gives it a default version to simplify tests
        sequester_blob: dict[SequesterServiceID, bytes] | None = None,
    ) -> (
        None
        | VlobUpdateBadOutcome
        | TimestampOutOfBallpark
        | RequireGreaterTimestamp
        | RejectedBySequesterService
        | SequesterServiceNotAvailable
    ):
        raise NotImplementedError

    async def read_as_user(
        self,
        organization_id: OrganizationID,
        author: UserID,
        realm_id: VlobID,
        vlobs: list[VlobID],
    ) -> list[tuple[VlobID, DeviceID, int, DateTime, bytes]] | VlobReadAsUserBadOutcome:
        raise NotImplementedError

    async def poll_changes_as_user(
        self,
        organization_id: OrganizationID,
        author: UserID,
        realm_id: VlobID,
        checkpoint: int,
    ) -> tuple[int, list[tuple[VlobID, int]]] | VlobPollChangesAsUserBadOutcome:
        raise NotImplementedError

    async def list_versions(
        self, organization_id: OrganizationID, author: DeviceID, vlob_id: VlobID
    ) -> dict[int, tuple[DateTime, DeviceID]] | VlobListVersionsBadOutcome:
        raise NotImplementedError

    async def test_dump_vlobs(
        self, organization_id: OrganizationID
    ) -> dict[VlobID, list[tuple[DeviceID, DateTime, VlobID, bytes]]]:
        raise NotImplementedError

    async def _sequester_service_send_webhook(
        self,
        webhook_url: str,
        service_id: SequesterServiceID,
        organization_id: OrganizationID,
        sequester_blob: bytes,
    ) -> None | SequesterServiceNotAvailable | RejectedBySequesterService:
        # Proceed webhook service before storage (guarantee data are not stored if they are rejected)
        try:
            ret = await self._http_client.post(
                webhook_url,
                params={
                    "organization_id": organization_id.str,
                    "service_id": service_id.hex,
                },
                content=sequester_blob,
            )
            if ret.status_code == 400:
                raw_body = await ret.aread()
                try:
                    body = json.loads(raw_body)
                    if not isinstance(body, dict) or not isinstance(body.get("reason"), str):
                        raise ValueError
                    reason = body["reason"]

                except (json.JSONDecodeError, ValueError):
                    logger.warning(
                        "Invalid rejection reason body returned by webhook",
                        organization_id=organization_id.str,
                        service_id=service_id.hex,
                        body=raw_body,
                    )
                    reason = "File rejected (no reason)"
                return RejectedBySequesterService(
                    service_id=service_id,
                    reason=reason,
                )

            elif not ret.is_success:
                logger.warning(
                    "Invalid HTTP status returned by webhook",
                    organization_id=organization_id.str,
                    service_id=service_id.hex,
                    status=ret.status_code,
                )
                return SequesterServiceNotAvailable(
                    service_id=service_id,
                )

        except OSError as exc:
            logger.warning(
                "Cannot reach webhook server",
                organization_id=organization_id.str,
                service_id=service_id.hex,
                exc_info=exc,
            )
            return SequesterServiceNotAvailable(
                service_id=service_id,
            )

    #
    # API commands
    #

    @api
    async def api_vlob_create(
        self, client_ctx: AuthenticatedClientContext, req: authenticated_cmds.latest.vlob_create.Req
    ) -> authenticated_cmds.latest.vlob_create.Rep:
        """
        This API call, when successful, performs the writing of a new vlob version to the database.
        Before adding new entries, extra care should be taken in order to guarantee the consistency in
        the ordering of the different timestamps stored in the database.

        See the `api_vlob_update` docstring for more information about the checks performed and the
        error returned in case those checks failed.
        """
        outcome = await self.create(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            realm_id=req.realm_id,
            vlob_id=req.vlob_id,
            timestamp=req.timestamp,
            blob=req.blob,
            sequester_blob=req.sequester_blob,
        )
        match outcome:
            case None:
                return authenticated_cmds.latest.vlob_create.RepOk()
            case VlobCreateBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.vlob_create.RepAuthorNotAllowed()
            case VlobCreateBadOutcome.REALM_NOT_FOUND:
                return authenticated_cmds.latest.vlob_create.RepRealmNotFound()
            case VlobCreateBadOutcome.VLOB_ALREADY_EXISTS:
                return authenticated_cmds.latest.vlob_create.RepVlobAlreadyExists()
            case VlobCreateBadOutcome.ORGANIZATION_NOT_SEQUESTERED:
                return authenticated_cmds.latest.vlob_create.RepOrganizationNotSequestered()
            case VlobCreateBadOutcome.SEQUESTER_INCONSISTENCY:
                return authenticated_cmds.latest.vlob_create.RepSequesterInconsistency()
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.vlob_create.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.vlob_create.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case RejectedBySequesterService() as error:
                return authenticated_cmds.latest.vlob_create.RepRejectedBySequesterService(
                    service_id=error.service_id,
                    reason=error.reason,
                )
            case SequesterServiceNotAvailable():
                return authenticated_cmds.latest.vlob_create.RepSequesterServiceUnavailable()
            case VlobCreateBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case VlobCreateBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case VlobCreateBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case VlobCreateBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_vlob_update(
        self, client_ctx: AuthenticatedClientContext, req: authenticated_cmds.latest.vlob_update.Req
    ) -> authenticated_cmds.latest.vlob_update.Rep:
        """
        This API call, when successful, performs the writing of a new vlob version to the database.
        Before adding new entries, extra care should be taken in order to guarantee the consistency in
        the ordering of the different timestamps stored in the database.

        See the `api_vlob_update` docstring for more information about the checks performed and the
        error returned in case those checks failed.
        """
        outcome = await self.update(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            vlob_id=req.vlob_id,
            version=req.version,
            timestamp=req.timestamp,
            blob=req.blob,
            sequester_blob=req.sequester_blob,
        )
        match outcome:
            case None:
                return authenticated_cmds.latest.vlob_update.RepOk()
            case VlobUpdateBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.vlob_update.RepAuthorNotAllowed()
            case VlobUpdateBadOutcome.VLOB_NOT_FOUND:
                return authenticated_cmds.latest.vlob_update.RepVlobNotFound()
            case VlobUpdateBadOutcome.ORGANIZATION_NOT_SEQUESTERED:
                return authenticated_cmds.latest.vlob_update.RepOrganizationNotSequestered()
            case VlobUpdateBadOutcome.SEQUESTER_INCONSISTENCY:
                return authenticated_cmds.latest.vlob_update.RepSequesterInconsistency()
            case VlobUpdateBadOutcome.SEQUESTER_SERVICE_UNAVAILABLE:
                return authenticated_cmds.latest.vlob_update.RepSequesterServiceUnavailable()
            case TimestampOutOfBallpark() as error:
                return authenticated_cmds.latest.vlob_update.RepTimestampOutOfBallpark(
                    server_timestamp=error.server_timestamp,
                    client_timestamp=error.client_timestamp,
                    ballpark_client_early_offset=error.ballpark_client_early_offset,
                    ballpark_client_late_offset=error.ballpark_client_late_offset,
                )
            case RequireGreaterTimestamp() as error:
                return authenticated_cmds.latest.vlob_update.RepRequireGreaterTimestamp(
                    strictly_greater_than=error.strictly_greater_than
                )
            case RejectedBySequesterService() as error:
                return authenticated_cmds.latest.vlob_update.RepRejectedBySequesterService(
                    service_id=error.service_id,
                    reason=error.reason,
                )
            case SequesterServiceNotAvailable():
                return authenticated_cmds.latest.vlob_update.RepSequesterServiceUnavailable()
            case VlobUpdateBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case VlobUpdateBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case VlobUpdateBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case VlobUpdateBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_vlob_read(
        self, client_ctx: AuthenticatedClientContext, req: authenticated_cmds.latest.vlob_read.Req
    ) -> authenticated_cmds.latest.vlob_read.Rep:
        if len(req.vlobs) > 1000:
            return authenticated_cmds.latest.vlob_read.RepTooManyElements()

        outcome = await self.read_as_user(
            organization_id=client_ctx.organization_id,
            author=client_ctx.user_id,
            realm_id=req.realm_id,
            vlobs=req.vlobs,
        )
        match outcome:
            case list() as vlobs:
                return authenticated_cmds.latest.vlob_read.RepOk(vlobs=vlobs)
            case VlobReadAsUserBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.vlob_read.RepAuthorNotAllowed()
            case VlobReadAsUserBadOutcome.REALM_NOT_FOUND:
                return authenticated_cmds.latest.vlob_read.RepRealmNotFound()
            case VlobReadAsUserBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case VlobReadAsUserBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case VlobReadAsUserBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case VlobReadAsUserBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)

    @api
    async def api_vlob_poll_changes(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.vlob_poll_changes.Req,
    ) -> authenticated_cmds.latest.vlob_poll_changes.Rep:
        outcome = await self.poll_changes_as_user(
            organization_id=client_ctx.organization_id,
            author=client_ctx.user_id,
            realm_id=req.realm_id,
            checkpoint=req.last_checkpoint,
        )
        match outcome:
            case (current_checkpoint, changes):
                return authenticated_cmds.latest.vlob_poll_changes.RepOk(
                    current_checkpoint=current_checkpoint, changes=changes
                )
            case VlobPollChangesAsUserBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.vlob_poll_changes.RepAuthorNotAllowed()
            case VlobPollChangesAsUserBadOutcome.REALM_NOT_FOUND:
                return authenticated_cmds.latest.vlob_poll_changes.RepRealmNotFound()
            case VlobPollChangesAsUserBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case VlobPollChangesAsUserBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case VlobPollChangesAsUserBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case VlobPollChangesAsUserBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()
            case unknown:
                assert_never(unknown)
