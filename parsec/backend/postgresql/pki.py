# Parsec Cloud (https://parsec.cloud) Copyright (c) BSLv1.1 (eventually AGPLv3) 2016-2021 Scille SAS

import hashlib
from typing import List
from uuid import UUID
from pendulum import DateTime

from parsec.api.protocol import OrganizationID
from parsec.api.protocol.pki import PkiEnrollmentStatus
from parsec.backend.user import UserActiveUsersLimitReached, UserAlreadyExistsError
from parsec.backend.user_type import User, Device
from parsec.backend.pki import (
    PkiEnrollmentActiveUsersLimitReached,
    PkiEnrollmentAlreadyExistError,
    PkiEnrollmentCertificateAlreadySubmittedError,
    PkiEnrollmentIdAlreadyUsedError,
    PkiEnrollmentInfo,
    PkiEnrollmentInfoAccepted,
    PkiEnrollmentInfoCancelled,
    PkiEnrollmentInfoRejected,
    PkiEnrollmentInfoSubmitted,
    PkiEnrollmentListItem,
    BasePkiEnrollmentComponent,
    PkiEnrollmentNoLongerAvailableError,
    PkiEnrollmentNotFoundError,
)
from parsec.backend.postgresql import PGHandler
from parsec.backend.postgresql.utils import Q, q_organization_internal_id, q_device_internal_id


_q_insert_certificate = Q(
    f"""
    INSERT INTO pki_certificate (certificate_id, request_id, request_timestamp, request_object)
    VALUES (
        $certificate_id,
        $request_id,
        $request_timestamp,
        $request_object,

    )
    """
)

# TODO update request shall reset reply ?
_q_update_certificate_request = Q(
    f"""
    UPDATE pki_certificate
    SET
        request_id = $request_id,
        request_timestamp=$request_timestamp,
        request_object=$request_object,
        reply_object=$reply_object,
        reply_timesamp=$reply_timestamp,
        reply_user_id=reply_user_id,
    WHERE certificate_id=certificate_id
"""
)

_q_update_certificate_reply = Q(
    f"""
    UPDATE pki_certificate
    SET
        reply_object=$reply_object,
        reply_timesamp=$reply_timestamp,
        reply_user_id=reply_user_id,
    WHERE certificate_id=certificate_id
    """
)

_q_get_certificate = Q(
    f"""
    SELECT *
    FROM pki_certificate
    WHERE
        certificate_id=$certificate_id
    ORDER BY _id ASC
    """
)

_q_get_certificates = Q(
    f"""
    SELECT *
    FROM pki_certificate
    ORDER BY _id ASC
    """
)

_q_get_pki_enrollment_from_certificate_sha1 = Q(
    f"""
    SELECT * FROM pki_enrollment
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND submitter_der_x509_certificate_sha1=$submitter_der_x509_certificate_sha1
    )
    ORDER BY enrollment_state ASC
    """
)

_q_get_pki_enrollment_from_enrollment_id = Q(
    f"""
    SELECT * FROM pki_enrollment
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND enrollment_id=$enrollment_id
    )
    """
)

_q_get_pki_enrollment = Q(
    f"""
    SELECT * FROM pki_enrollment
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND enrollment_id=$enrollment_id
    )
    """
)

_q_get_pki_enrollment_from_state = Q(
    f"""
    SELECT * FROM pki_enrollment
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND enrollment_state=$state
    )
    ORDER BY _id ASC
    """
)


_q_submit_pki_enrollment = Q(
    f"""
    INSERT INTO pki_enrollment(
        organization,
        enrollment_id,
        submitter_der_x509_certificate,
        submitter_der_x509_certificate_sha1,
        submit_payload_signature,
        submit_payload,
        enrollment_state,
        submitted_on
    )
    VALUES(
        { q_organization_internal_id("$organization_id") },
        $enrollment_id,
        $submitter_der_x509_certificate,
        $submitter_der_x509_certificate_sha1,
        $submit_payload_signature,
        $submit_payload,
        $enrollment_state,
        $submitted_on
    )

    """
)

_q_cancel_pki_enrollment = Q(
    f"""
    UPDATE pki_enrollment
    SET
        enrollment_state=$enrollment_state,
        info_cancelled.cancelled_on=$cancelled_on
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND enrollment_id=$enrollment_id
    )
    """
)


_q_reject_pki_enrollment = Q(
    f"""
    UPDATE pki_enrollment
    SET
        enrollment_state=$enrollment_state,
        info_rejected.rejected_on=$rejected_on
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND enrollment_id=$enrollment_id
    )
    """
)

_q_accept_pki_enrollment = Q(
    f"""
    UPDATE pki_enrollment
    SET
        enrollment_state=$enrollment_state,
        info_accepted.accepted_on=$accepted_on,
        info_accepted.accepter_der_x509_certificate=$accepter_der_x509_certificate,
        info_accepted.accept_payload_signature=$accept_payload_signature,
        info_accepted.accept_payload=$accept_payload,
        accepter={q_device_internal_id(organization_id="$organization_id", device_id="$accepter")},
        accepted={q_device_internal_id(organization_id="$organization_id", device_id="$accepted")}
    WHERE (
        organization = { q_organization_internal_id("$organization_id") }
        AND enrollment_id=$enrollment_id
    )
    """
)


def _build_enrollment_info(entry) -> PkiEnrollmentInfo:
    if entry["enrollment_state"] == PkiEnrollmentStatus.SUBMITTED.value:
        return PkiEnrollmentInfoSubmitted(
            enrollment_id=entry["enrollment_id"], submitted_on=entry["submitted_on"]
        )
    elif entry["enrollment_state"] == PkiEnrollmentStatus.CANCELLED.value:
        return PkiEnrollmentInfoCancelled(
            enrollment_id=entry["enrollment_id"],
            submitted_on=entry["submitted_on"],
            cancelled_on=entry["info_cancelled"]["cancelled_on"],
        )
    elif entry["enrollment_state"] == PkiEnrollmentStatus.REJECTED.value:
        return PkiEnrollmentInfoRejected(
            enrollment_id=entry["enrollment_id"],
            submitted_on=entry["submitted_on"],
            rejected_on=entry["info_rejected"]["rejected_on"],
        )
    elif entry["enrollment_state"] == PkiEnrollmentStatus.SUBMITTED.value:
        return PkiEnrollmentInfoAccepted(
            enrollment_id=entry["enrollment_id"],
            submitted_on=entry["submitted_on"],
            accepted_on=entry["info_accepted"]["accepted_on"],
            accepter_der_x509_certificate=entry["info_accepted"]["accepter_der_x509_certificate"],
            accept_payload_signature=entry["info_accepted"]["accept_payload_signature"],
            accept_payload=entry["info_accepted"]["accept_payload"],
        )
    else:
        assert False


class PGPkiEnrollmentComponent(BasePkiEnrollmentComponent):
    def __init__(self, dbh: PGHandler):
        self.dbh = dbh

    def register_components(self, **other_components):
        self._user_component = other_components["user"]

    async def submit(
        self,
        organization_id: OrganizationID,
        enrollment_id: UUID,
        force: bool,
        submitter_der_x509_certificate: bytes,
        submit_payload_signature: bytes,
        submit_payload: bytes,
        submitted_on: DateTime,
    ) -> None:
        """
        Raises:
            PkiEnrollmentCertificateAlreadySubmittedError
            PkiEnrollmentAlreadyEnrolledError
        """
        submitter_der_x509_certificate_sha1 = hashlib.sha1(submitter_der_x509_certificate).digest()
        async with self.dbh.pool.acquire() as conn, conn.transaction():
            # Assert enrollment_id not used
            row = await conn.fetchrow(
                *_q_get_pki_enrollment(
                    organization_id=organization_id.str, enrollment_id=enrollment_id
                )
            )
            if row:
                raise PkiEnrollmentIdAlreadyUsedError()

            # Try to retrieve the last attempt with this x509 certificate
            rep = await conn.fetch(
                *_q_get_pki_enrollment_from_certificate_sha1(
                    organization_id=organization_id.str,
                    submitter_der_x509_certificate_sha1=submitter_der_x509_certificate_sha1,
                )
            )
            for row in rep:
                enrollment_state = row["enrollment_state"]
                if enrollment_state == PkiEnrollmentStatus.SUBMITTED.value:
                    if force:
                        await conn.execute(
                            *_q_cancel_pki_enrollment(
                                organization_id=organization_id.str,
                                enrollment_id=row["enrollment_id"],
                                enrollment_state=PkiEnrollmentStatus.CANCELLED.value,
                                cancelled_on=submitted_on,
                            )
                        )
                    else:
                        raise PkiEnrollmentCertificateAlreadySubmittedError(
                            submitted_on=row["submitted_on"]
                        )
                elif enrollment_state in [
                    PkiEnrollmentStatus.REJECTED.value,
                    PkiEnrollmentStatus.CANCELLED.value,
                ]:
                    # Previous attempt was unsuccessful, so we are clear to submit a new attempt !
                    pass
                elif enrollment_state == PkiEnrollmentStatus.ACCEPTED.value:
                    # Previous attempt end successfully, we are not allowed to submit
                    # unless the created user has been revoked
                    assert row["accepted"] is not None and row["accepter"] is not None
                    # TODO check user
                else:
                    assert False
            # TODO Request ID error
            await conn.execute(
                *_q_submit_pki_enrollment(
                    organization_id=organization_id.str,
                    enrollment_id=enrollment_id,
                    submitter_der_x509_certificate=submitter_der_x509_certificate,
                    submitter_der_x509_certificate_sha1=submitter_der_x509_certificate_sha1,
                    submit_payload_signature=submit_payload_signature,
                    submit_payload=submit_payload,
                    enrollment_state=PkiEnrollmentStatus.SUBMITTED.value,
                    submitted_on=submitted_on,
                )
            )

    async def info(self, organization_id: OrganizationID, enrollment_id: UUID) -> PkiEnrollmentInfo:
        """
        Raises:
            PkiEnrollmentNotFoundError
        """
        async with self.dbh.pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                *_q_get_pki_enrollment_from_enrollment_id(
                    organization_id=organization_id.str, enrollment_id=enrollment_id
                )
            )
            if not row:
                raise PkiEnrollmentNotFoundError()
            else:
                return _build_enrollment_info(row)

    async def list(self, organization_id: OrganizationID) -> List[PkiEnrollmentListItem]:
        """
        Raises: Nothing !
        """

        async with self.dbh.pool.acquire() as conn, conn.transaction():

            entries = await conn.fetch(
                *_q_get_pki_enrollment_from_state(
                    organization_id=organization_id.str, state=PkiEnrollmentStatus.SUBMITTED.value
                )
            )
            return [
                PkiEnrollmentListItem(
                    enrollment_id=entry["enrollment_id"],
                    submitted_on=entry["submitted_on"],
                    submitter_der_x509_certificate=entry["submitter_der_x509_certificate"],
                    submit_payload_signature=entry["submit_payload_signature"],
                    submit_payload=entry["submit_payload"],
                )
                for entry in entries
            ]

    async def reject(
        self, organization_id: OrganizationID, enrollment_id: UUID, rejected_on: DateTime
    ) -> None:
        """
        Raises:
            PkiEnrollmentNotFoundError
            PkiEnrollmentNoLongerAvailableError
        """

        async with self.dbh.pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                *_q_get_pki_enrollment(
                    organization_id=organization_id.str, enrollment_id=enrollment_id
                )
            )
            if not row:
                raise PkiEnrollmentNotFoundError()
            if row["enrollment_state"] != PkiEnrollmentStatus.SUBMITTED.value:
                raise PkiEnrollmentNoLongerAvailableError()

            await conn.execute(
                *_q_reject_pki_enrollment(
                    organization_id=organization_id.str,
                    enrollment_id=enrollment_id,
                    enrollment_state=PkiEnrollmentStatus.REJECTED.value,
                    rejected_on=rejected_on,
                )
            )

    async def accept(
        self,
        organization_id: OrganizationID,
        enrollment_id: UUID,
        accepter_der_x509_certificate: bytes,
        accept_payload_signature: bytes,
        accept_payload: bytes,
        accepted_on: DateTime,
        user: User,
        first_device: Device,
    ) -> None:
        """
        Raises:
            PkiEnrollmentNotFoundError
            PkiEnrollmentNoLongerAvailableError
            PkiEnrollmentAlreadyExistError
            PkiEnrollmentActiveUsersLimitReached
        """
        async with self.dbh.pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                *_q_get_pki_enrollment(
                    organization_id=organization_id.str, enrollment_id=enrollment_id
                )
            )
            if not row:
                raise PkiEnrollmentNotFoundError()
            if row["enrollment_state"] != PkiEnrollmentStatus.SUBMITTED.value:
                raise PkiEnrollmentNoLongerAvailableError()

            try:
                await self._user_component.create_user(
                    organization_id=organization_id, user=user, first_device=first_device
                )

            except UserAlreadyExistsError as exc:
                raise PkiEnrollmentAlreadyExistError from exc

            except UserActiveUsersLimitReached as exc:
                raise PkiEnrollmentActiveUsersLimitReached from exc

            assert user.user_certifier is not None
            await conn.execute(
                *_q_accept_pki_enrollment(
                    enrollment_state=PkiEnrollmentStatus.ACCEPTED.value,
                    organization_id=organization_id.str,
                    enrollment_id=enrollment_id,
                    accepted_on=accepted_on,
                    accepter_der_x509_certificate=accepter_der_x509_certificate,
                    accept_payload_signature=accept_payload_signature,
                    accept_payload=accept_payload,
                    accepter=user.user_certifier.str,
                    accepted=first_device.device_id.str,
                )
            )

    # async def pki_enrollment_request(
    #     self,
    #     organization_id: OrganizationID,
    #     certificate_id: bytes,
    #     request_id: UUID,
    #     request_object: PkiEnrollmentRequest,
    #     force_flag: bool = False,
    # ) -> DateTime:

    #     async with self.dbh.pool.acquire() as conn, conn.transaction():
    #         data = await conn.fetch(*_q_get_certificate(certificate_id=certificate_id))
    #         if len(data):
    #             existing_certificate = build_certificate_from_db(data[0])
    #             if existing_certificate.reply_object and existing_certificate.reply_user_id:
    #                 raise PkiCertificateAlreadyEnrolledError(
    #                     existing_certificate.request_timestamp,
    #                     f"Certificate {str(certificate_id)} already attributed",
    #                 )

    #             if not force_flag:
    #                 raise PkiCertificateAlreadyRequestedError(
    #                     existing_certificate.reply_timestamp,
    #                     f"Certificate {str(certificate_id)} already used in request {request_id}",
    #                 )
    #             else:
    #                 request_timestamp = pendulum.now()
    #                 await conn.fetchval(
    #                     *_q_update_certificate_request(
    #                         certificate_id=certificate_id,
    #                         request_id=request_id,
    #                         request_timestamp=request_timestamp,
    #                         request_object=request_object.dump(),
    #                     )
    #                 )
    #                 return request_timestamp

    #         ## TODO # Check human handle already used
    #         ## for pki_certificate in self._pki_certificates.values():
    #         ##     if (
    #         ##         pki_certificate.request_object.requested_human_handle
    #         ##         == request_object.requested_human_handle
    #         ##     ):
    #         ##         raise PkiCertificateEmailAlreadyAttributedError(
    #         ##             f"email f{request_object.requested_human_handle} already attributed"
    #         ##         )
    #         else:
    #             request_timestamp = pendulum.now()
    #             await conn.fetchval(
    #                 *_q_insert_certificate(
    #                     certificate_id=certificate_id,
    #                     request_id=request_id,
    #                     request_timestamp=request_timestamp,
    #                     request_object=request_object.dump(),
    #                 )
    #             )
    #             return request_timestamp

    # async def pki_enrollment_get_requests(self) -> List[Tuple[str, str, PkiEnrollmentRequest]]:
    #     async with self.dbh.pool.acquire() as conn, conn.transaction():
    #         data = await conn.fetch(*_q_get_certificates())

    #     return [(d[1], d[2], d[3]) for d in data]

    # async def pki_enrollment_reply(
    #     self,
    #     certificate_id: str,
    #     request_id: str,
    #     reply_object: PkiEnrollmentReply,
    #     user_id: Optional[str] = None,
    # ) -> DateTime:
    #     async with self.dbh.pool.acquire() as conn, conn.transaction():
    #         data = await conn.fetch(*_q_get_certificate(certificate_id=certificate_id))
    #         if not len(data):
    #             raise PkiCertificateNotFoundError(f"Certificate {certificate_id} not found")
    #         pki_certificate = build_certificate_from_db(data[0])
    #         if pki_certificate.request_id != request_id:
    #             raise PkiCertificateRequestNotFoundError(
    #                 f"Request {request_id} not found for certificate {certificate_id}"
    #             )
    #         reply_timestamp = pendulum.now()
    #         await conn.fetchval(
    #             *_q_update_certificate_reply(
    #                 certificate_id=certificate_id,
    #                 reply_object=reply_object.dump(),
    #                 reply_user_id=user_id,
    #                 reply_timestamp=reply_timestamp,
    #             )
    #         )
    #         return reply_timestamp

    # async def pki_enrollment_get_reply(
    #     self, certificate_id, request_id
    # ) -> Tuple[Optional[PkiEnrollmentReply], Optional[DateTime], DateTime, Optional[str]]:
    #     async with self.dbh.pool.acquire() as conn, conn.transaction():
    #         data = await conn.fetch(*_q_get_certificate(certificate_id=certificate_id))
    #         if not len(data):
    #             raise PkiCertificateNotFoundError(f"Certificate {certificate_id} not found")
    #         pki_certificate = build_certificate_from_db(data[0])
    #         if pki_certificate.request_id != request_id:
    #             raise PkiCertificateRequestNotFoundError(
    #                 f"Request {request_id} not found for certificate {certificate_id}"
    #             )
    #     return (
    #         data[0][7],  # reply_object
    #         data[0][6],  # reply_timestamp
    #         data[0][3],  # request_timestamp
    #         data[0][5],  # user_id
    #     )
