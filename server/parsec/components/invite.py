# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

import smtplib
import ssl
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from email.header import Header
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum, auto

import anyio

from parsec._parsec import (
    DateTime,
    DeviceID,
    HashDigest,
    HumanHandle,
    InvitationStatus,
    InvitationToken,
    InvitationType,
    OrganizationID,
    ParsecInvitationAddr,
    PublicKey,
    UserID,
    authenticated_cmds,
    invited_cmds,
)
from parsec.api import api
from parsec.client_context import AuthenticatedClientContext, InvitedClientContext
from parsec.components.events import EventBus
from parsec.config import BackendConfig, EmailConfig, MockedEmailConfig, SmtpEmailConfig
from parsec.events import (
    Event,
    EventEnrollmentConduit,
    EventInvitation,
    InvitationStatusField,
)
from parsec.logging import get_logger
from parsec.templates import get_template
from parsec.types import BadOutcomeEnum

logger = get_logger()


class ConduitState(Enum):
    STATE_1_WAIT_PEERS = "1_WAIT_PEERS"
    STATE_2_1_CLAIMER_HASHED_NONCE = "2_1_CLAIMER_HASHED_NONCE"
    STATE_2_2_GREETER_NONCE = "2_2_GREETER_NONCE"
    STATE_2_3_CLAIMER_NONCE = "2_3_CLAIMER_NONCE"
    STATE_3_1_CLAIMER_TRUST = "3_1_CLAIMER_TRUST"
    STATE_3_2_GREETER_TRUST = "3_2_GREETER_TRUST"
    STATE_4_COMMUNICATE = "4_COMMUNICATE"


NEXT_CONDUIT_STATE = {
    ConduitState.STATE_1_WAIT_PEERS: ConduitState.STATE_2_1_CLAIMER_HASHED_NONCE,
    ConduitState.STATE_2_1_CLAIMER_HASHED_NONCE: ConduitState.STATE_2_2_GREETER_NONCE,
    ConduitState.STATE_2_2_GREETER_NONCE: ConduitState.STATE_2_3_CLAIMER_NONCE,
    ConduitState.STATE_2_3_CLAIMER_NONCE: ConduitState.STATE_3_1_CLAIMER_TRUST,
    ConduitState.STATE_3_1_CLAIMER_TRUST: ConduitState.STATE_3_2_GREETER_TRUST,
    ConduitState.STATE_3_2_GREETER_TRUST: ConduitState.STATE_4_COMMUNICATE,
    ConduitState.STATE_4_COMMUNICATE: ConduitState.STATE_4_COMMUNICATE,
}


@dataclass(slots=True)
class ConduitListenCtx:
    organization_id: OrganizationID
    token: InvitationToken
    greeter: UserID
    is_greeter: bool
    state: ConduitState
    payload: bytes
    peer_payload: bytes | None
    is_last_exchange: bool


@dataclass(slots=True)
class UserInvitation:
    TYPE = InvitationType.USER
    claimer_email: str
    created_by_user_id: UserID
    created_by_device_id: DeviceID
    created_by_human_handle: HumanHandle
    token: InvitationToken
    created_on: DateTime
    status: InvitationStatus


@dataclass(slots=True)
class DeviceInvitation:
    TYPE = InvitationType.DEVICE
    created_by_user_id: UserID
    created_by_device_id: DeviceID
    created_by_human_handle: HumanHandle
    token: InvitationToken
    created_on: DateTime
    status: InvitationStatus


Invitation = UserInvitation | DeviceInvitation


def generate_invite_email(
    from_addr: str,
    to_addr: str,
    reply_to: str | None,
    greeter_name: str | None,  # None for device invitation
    organization_id: OrganizationID,
    invitation_url: str,
    server_url: str,
) -> Message:
    # Quick fix to have a similar behavior between Rust and Python
    if server_url.endswith("/"):
        server_url = server_url[:-1]
    html = get_template("invitation_mail.html").render(
        greeter=greeter_name,
        organization_id=organization_id.str,
        invitation_url=invitation_url,
        server_url=server_url,
    )
    text = get_template("invitation_mail.txt").render(
        greeter=greeter_name,
        organization_id=organization_id.str,
        invitation_url=invitation_url,
        server_url=server_url,
    )

    # mail settings
    message = MIMEMultipart("alternative")
    if greeter_name:
        message["Subject"] = f"[Parsec] { greeter_name } invited you to { organization_id.str }"
    else:
        message["Subject"] = f"[Parsec] New device invitation to { organization_id.str }"
    message["From"] = from_addr
    message["To"] = to_addr
    if reply_to is not None and greeter_name is not None:
        # Contrary to the other address fields, the greeter name can include non-ascii characters
        # Example: "Jean-José" becomes "=?utf-8?q?Jean-Jos=C3=A9?="
        encoded_greeter_name = Header(greeter_name.encode("utf-8"), "utf-8").encode()
        message["Reply-To"] = f"{encoded_greeter_name} <{reply_to}>"

    # Turn parts into MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    return message


class SendEmailBadOutcome(BadOutcomeEnum):
    SERVER_UNAVAILABLE = auto()
    RECIPIENT_REFUSED = auto()
    BAD_SMTP_CONFIG = auto()


def _smtp_send_email(
    email_config: SmtpEmailConfig, to_addr: str, message: Message
) -> None | SendEmailBadOutcome:
    try:
        context = ssl.create_default_context()
        if email_config.use_ssl:
            server: smtplib.SMTP | smtplib.SMTP_SSL = smtplib.SMTP_SSL(
                email_config.host, email_config.port, context=context
            )
        else:
            server = smtplib.SMTP(email_config.host, email_config.port)

        with server:
            if email_config.use_tls and not email_config.use_ssl:
                if server.starttls(context=context)[0] != 220:
                    logger.warning("Email TLS connection isn't encrypted")
            if email_config.host_user and email_config.host_password:
                server.login(email_config.host_user, email_config.host_password)
            server.sendmail(email_config.sender, to_addr, message.as_string())

    except smtplib.SMTPConnectError:
        return SendEmailBadOutcome.SERVER_UNAVAILABLE
    except smtplib.SMTPRecipientsRefused:
        return SendEmailBadOutcome.RECIPIENT_REFUSED
    except smtplib.SMTPException as exc:
        logger.warning("SMTP error", exc_info=exc, to_addr=to_addr, subject=message["Subject"])
        return SendEmailBadOutcome.BAD_SMTP_CONFIG
    except Exception:
        # Fail-safe: since the device/user has been created, we don't want to fail too hard
        logger.exception(
            "Unexpected exception while sending an email", to_addr=to_addr, message=message
        )
        return SendEmailBadOutcome.BAD_SMTP_CONFIG


def _mocked_send_email(
    email_config: MockedEmailConfig, to_addr: str, message: Message
) -> None | SendEmailBadOutcome:
    tmpfile_fd, tmpfile_path = tempfile.mkstemp(
        prefix="tmp-email-", suffix=".html", dir=email_config.tmpdir
    )
    del tmpfile_fd  # Unused
    tmpfile = open(tmpfile_path, "w")
    tmpfile.write(message.as_string())
    print(
        f"""\
A request to send an e-mail to {to_addr} has been triggered and mocked.
The mail file can be found here: {tmpfile.name}\n""",
        tmpfile.name,
        file=sys.stderr,
    )


async def send_email(
    email_config: EmailConfig, to_addr: str, message: Message
) -> None | SendEmailBadOutcome:
    if isinstance(email_config, SmtpEmailConfig):
        _send_email = _smtp_send_email
    else:
        _send_email = _mocked_send_email

    return await anyio.to_thread.run_sync(_send_email, email_config, to_addr, message)


class InviteConduitExchangeBadOutcome(BadOutcomeEnum):
    ORGANIZATION_NOT_FOUND = auto()
    ORGANIZATION_EXPIRED = auto()
    AUTHOR_NOT_FOUND = auto()
    AUTHOR_REVOKED = auto()
    ENROLLMENT_WRONG_STATE = auto()
    INVITATION_NOT_FOUND = auto()
    INVITATION_DELETED = auto()


class InviteNewForUserBadOutcome(BadOutcomeEnum):
    ORGANIZATION_NOT_FOUND = auto()
    ORGANIZATION_EXPIRED = auto()
    AUTHOR_NOT_FOUND = auto()
    AUTHOR_REVOKED = auto()
    AUTHOR_NOT_ALLOWED = auto()
    CLAIMER_EMAIL_ALREADY_ENROLLED = auto()


class InviteNewForDeviceBadOutcome(BadOutcomeEnum):
    ORGANIZATION_NOT_FOUND = auto()
    ORGANIZATION_EXPIRED = auto()
    AUTHOR_NOT_FOUND = auto()
    AUTHOR_REVOKED = auto()


class InviteCancelBadOutcome(BadOutcomeEnum):
    ORGANIZATION_NOT_FOUND = auto()
    ORGANIZATION_EXPIRED = auto()
    AUTHOR_NOT_FOUND = auto()
    AUTHOR_REVOKED = auto()
    INVITATION_NOT_FOUND = auto()
    INVITATION_ALREADY_DELETED = auto()


class InviteListBadOutcome(BadOutcomeEnum):
    ORGANIZATION_NOT_FOUND = auto()
    ORGANIZATION_EXPIRED = auto()
    AUTHOR_NOT_FOUND = auto()
    AUTHOR_REVOKED = auto()


class InviteAsInvitedInfoBadOutcome(BadOutcomeEnum):
    ORGANIZATION_NOT_FOUND = auto()
    ORGANIZATION_EXPIRED = auto()
    INVITATION_NOT_FOUND = auto()
    INVITATION_DELETED = auto()


class BaseInviteComponent:
    def __init__(self, event_bus: EventBus, config: BackendConfig):
        self._event_bus = event_bus
        self._config = config
        # We use the `invite.status_changed` event to keep a list of all the
        # invitation claimers connected across all Parsec server instances.
        #
        # This is useful to display the invitations ready to be greeted.
        # Note we rely on a per-server list in memory instead of storing this
        # information in database so that we default to no claimer present
        # (which is the most likely when a server is restarted) .
        #
        # However there are multiple ways this list can go out of sync:
        # - a claimer can be connected to a server, then another server starts
        # - the server the claimer is connected to crashes without being able
        #   to notify the other servers
        # - a claimer open multiple connections at the same time, then is
        #   considered disconnected as soon as he closes one of his connections
        #
        # This is considered "fine enough" given all the claimer has to do
        # to fix this is to retry a connection, which precisely the kind of
        # "I.T., have you tried to turn it off and on again ?" a human is
        # expected to do ;-)
        self._claimers_ready: dict[OrganizationID, set[InvitationToken]] = defaultdict(set)
        self._event_bus.connect(self._on_event)
        # Note we don't have a `__del__` to disconnect from the event bus: the lifetime
        # of this component is basically equivalent of the one of the event bus anyway

    def _on_event(self, event: Event) -> None:
        if isinstance(event, EventInvitation):
            if event.status == InvitationStatus.READY:
                self._claimers_ready[event.organization_id].add(event.token)
            else:  # Invitation deleted or back to idle
                self._claimers_ready[event.organization_id].discard(event.token)

    # Used by `new_for_user` implementations
    async def _send_user_invitation_email(
        self,
        organization_id: OrganizationID,
        token: InvitationToken,
        claimer_email: str,
        greeter_human_handle: HumanHandle,
    ) -> None | SendEmailBadOutcome:
        if not self._config.server_addr:
            return SendEmailBadOutcome.BAD_SMTP_CONFIG

        invitation_url = ParsecInvitationAddr.build(
            server_addr=self._config.server_addr,
            organization_id=organization_id,
            invitation_type=InvitationType.USER,
            token=token,
        ).to_http_redirection_url()

        message = generate_invite_email(
            from_addr=self._config.email_config.sender,
            to_addr=claimer_email,
            greeter_name=greeter_human_handle.label,
            reply_to=greeter_human_handle.email,
            organization_id=organization_id,
            invitation_url=invitation_url,
            server_url=self._config.server_addr.to_http_url(),
        )

        return await send_email(
            email_config=self._config.email_config,
            to_addr=claimer_email,
            message=message,
        )

    # Used by `new_for_device` implementations
    async def _send_device_invitation_email(
        self,
        organization_id: OrganizationID,
        token: InvitationToken,
        email: str,
    ) -> None | SendEmailBadOutcome:
        if not self._config.server_addr:
            return SendEmailBadOutcome.BAD_SMTP_CONFIG

        invitation_url = ParsecInvitationAddr.build(
            server_addr=self._config.server_addr,
            organization_id=organization_id,
            invitation_type=InvitationType.DEVICE,
            token=token,
        ).to_http_redirection_url()

        message = generate_invite_email(
            from_addr=self._config.email_config.sender,
            to_addr=email,
            greeter_name=None,
            reply_to=None,
            organization_id=organization_id,
            invitation_url=invitation_url,
            server_url=self._config.server_addr.to_http_url(),
        )

        return await send_email(
            email_config=self._config.email_config,
            to_addr=email,
            message=message,
        )

    #
    # Public methods
    #

    async def conduit_exchange(
        self,
        organization_id: OrganizationID,
        greeter: UserID | None,  # None for claimer
        token: InvitationToken,
        state: ConduitState,
        payload: bytes,
        last: bool = False,
    ) -> tuple[bytes, bool] | InviteConduitExchangeBadOutcome:
        # Conduit exchange is done in two steps:
        # First we "talk" by providing our payload and retrieve the peer's
        # payload if he has talked prior to us.
        # Then we "listen" by waiting for the peer to provide his payload if we
        # have talked first, or to confirm us it has received our payload if we
        # have talked after him.
        filter_organization_id = organization_id
        filter_token = token

        def _event_filter(
            event: Event,
        ) -> bool:
            match event:
                case (EventEnrollmentConduit() | EventInvitation()) as event:
                    return (
                        event.organization_id == filter_organization_id
                        and event.token == filter_token
                    )
                case _:
                    return False

        with self._event_bus.create_waiter(filter=_event_filter) as waiter:
            outcome = await self._conduit_talk(
                organization_id=organization_id,
                token=token,
                is_greeter=greeter is not None,
                state=state,
                payload=payload,
                last=last,
            )
            match outcome:
                case ConduitListenCtx() as listen_ctx:
                    pass
                case InviteConduitExchangeBadOutcome() as error:
                    return error

            if greeter is None and state == ConduitState.STATE_1_WAIT_PEERS:
                await self._claimer_joined(
                    organization_id=organization_id, greeter=listen_ctx.greeter, token=token
                )

            try:
                # Unlike what it name may imply, `_conduit_listen` doesn't wait for the peer
                # to answer (it returns `None` instead), so we wait for some events to occur
                # before calling:
                # - `EventEnrollmentConduitUpdated`: Triggered when the peer has completed it own
                #   talk step, `_conduit_listen` will most likely return the peer payload now.
                # - `EventInvitationStatusUpdated`: Triggered if the peer reset the invitation
                #   or if the invitation has been deleted, in any case `_conduit_listen` will
                #   detect the listen is not longer possible and return an error accordingly.
                while True:
                    await waiter.wait()
                    waiter.clear()
                    outcome = await self._conduit_listen(DateTime.now(), listen_ctx)
                    match outcome:
                        case (peer_payload, last):
                            return peer_payload, last
                        case InviteConduitExchangeBadOutcome() as error:
                            return error
                        case None:
                            continue

            finally:
                if greeter is None and state == ConduitState.STATE_1_WAIT_PEERS:
                    # When claimer left, it's most likely because it's connection is getting closed.
                    # Hence it's hazardous to send the event directly from this coroutine (it
                    # requires cancellation shielding), and instead the `send_nowait` will
                    # delegate the work to a dedicated coroutine.
                    status = InvitationStatusField.IDLE  # pyright: ignore [reportAttributeAccessIssue]
                    self._event_bus.send_nowait(
                        EventInvitation(
                            organization_id=organization_id,
                            token=token,
                            greeter=listen_ctx.greeter,
                            status=status,
                        )
                    )

    async def _conduit_talk(
        self,
        organization_id: OrganizationID,
        token: InvitationToken,
        is_greeter: bool,
        state: ConduitState,
        payload: bytes,
        last: bool,  # Only for greeter
    ) -> ConduitListenCtx | InviteConduitExchangeBadOutcome:
        raise NotImplementedError

    async def _conduit_listen(
        self,
        now: DateTime,
        ctx: ConduitListenCtx,
    ) -> tuple[bytes, bool] | None | InviteConduitExchangeBadOutcome:
        """
        Returns ``None`` is listen is still needed
        """
        raise NotImplementedError

    async def _claimer_joined(
        self, organization_id: OrganizationID, token: InvitationToken, greeter: UserID
    ) -> None:
        raise NotImplementedError

    async def _claimer_left(
        self, organization_id: OrganizationID, token: InvitationToken, greeter: UserID
    ) -> None:
        raise NotImplementedError

    async def new_for_user(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        claimer_email: str,
        send_email: bool,
        # Only needed for testbed template
        force_token: InvitationToken | None = None,
    ) -> tuple[InvitationToken, None | SendEmailBadOutcome] | InviteNewForUserBadOutcome:
        raise NotImplementedError

    async def new_for_device(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        send_email: bool,
        # Only needed for testbed template
        force_token: InvitationToken | None = None,
    ) -> tuple[InvitationToken, None | SendEmailBadOutcome] | InviteNewForDeviceBadOutcome:
        raise NotImplementedError

    async def cancel(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        token: InvitationToken,
    ) -> None | InviteCancelBadOutcome:
        raise NotImplementedError

    async def list(
        self, organization_id: OrganizationID, author: DeviceID
    ) -> list[Invitation] | InviteListBadOutcome:
        raise NotImplementedError

    async def info_as_invited(
        self, organization_id: OrganizationID, token: InvitationToken
    ) -> Invitation | InviteAsInvitedInfoBadOutcome:
        raise NotImplementedError

    async def test_dump_all_invitations(
        self, organization_id: OrganizationID
    ) -> dict[UserID, list[Invitation]]:
        raise NotImplementedError

    #
    # API commands
    #

    @api
    async def api_invite_new_user(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_new_user.Req,
    ) -> authenticated_cmds.latest.invite_new_user.Rep:
        outcome = await self.new_for_user(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            claimer_email=req.claimer_email,
            send_email=req.send_email,
        )
        match outcome:
            case (InvitationToken() as token, None):
                email_sent = (
                    authenticated_cmds.latest.invite_new_user.InvitationEmailSentStatus.SUCCESS
                )
            case (
                InvitationToken() as token,
                SendEmailBadOutcome.BAD_SMTP_CONFIG
                | SendEmailBadOutcome.SERVER_UNAVAILABLE,
            ):
                email_sent = authenticated_cmds.latest.invite_new_user.InvitationEmailSentStatus.SERVER_UNAVAILABLE
            case (InvitationToken() as token, SendEmailBadOutcome.RECIPIENT_REFUSED):
                email_sent = authenticated_cmds.latest.invite_new_user.InvitationEmailSentStatus.RECIPIENT_REFUSED
            case InviteNewForUserBadOutcome.AUTHOR_NOT_ALLOWED:
                return authenticated_cmds.latest.invite_new_user.RepAuthorNotAllowed()
            case InviteNewForUserBadOutcome.CLAIMER_EMAIL_ALREADY_ENROLLED:
                return authenticated_cmds.latest.invite_new_user.RepClaimerEmailAlreadyEnrolled()
            case InviteNewForUserBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteNewForUserBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteNewForUserBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteNewForUserBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

        return authenticated_cmds.latest.invite_new_user.RepOk(
            token=token,
            email_sent=email_sent,
        )

    @api
    async def api_invite_new_device(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_new_device.Req,
    ) -> authenticated_cmds.latest.invite_new_device.Rep:
        outcome = await self.new_for_device(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            send_email=req.send_email,
        )
        match outcome:
            case (InvitationToken() as token, None):
                email_sent = (
                    authenticated_cmds.latest.invite_new_device.InvitationEmailSentStatus.SUCCESS
                )
            case (
                InvitationToken() as token,
                SendEmailBadOutcome.BAD_SMTP_CONFIG
                | SendEmailBadOutcome.SERVER_UNAVAILABLE,
            ):
                email_sent = authenticated_cmds.latest.invite_new_device.InvitationEmailSentStatus.SERVER_UNAVAILABLE
            case (InvitationToken() as token, SendEmailBadOutcome.RECIPIENT_REFUSED):
                email_sent = authenticated_cmds.latest.invite_new_device.InvitationEmailSentStatus.RECIPIENT_REFUSED
            case InviteNewForDeviceBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteNewForDeviceBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteNewForDeviceBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteNewForDeviceBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

        return authenticated_cmds.latest.invite_new_device.RepOk(
            token=token,
            email_sent=email_sent,
        )

    @api
    async def api_invite_cancel(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_cancel.Req,
    ) -> authenticated_cmds.latest.invite_cancel.Rep:
        outcome = await self.cancel(
            now=DateTime.now(),
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
            token=req.token,
        )
        match outcome:
            case None:
                return authenticated_cmds.latest.invite_cancel.RepOk()
            case InviteCancelBadOutcome.INVITATION_NOT_FOUND:
                return authenticated_cmds.latest.invite_cancel.RepInvitationNotFound()
            case InviteCancelBadOutcome.INVITATION_ALREADY_DELETED:
                return authenticated_cmds.latest.invite_cancel.RepInvitationAlreadyDeleted()
            case InviteCancelBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteCancelBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteCancelBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteCancelBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_list(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_list.Req,
    ) -> authenticated_cmds.latest.invite_list.Rep:
        outcome = await self.list(
            organization_id=client_ctx.organization_id,
            author=client_ctx.device_id,
        )
        match outcome:
            case list() as invitations:
                pass
            case InviteListBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteListBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteListBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteListBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

        cooked_invitations = []
        for invitation in invitations:
            match invitation:
                case UserInvitation():
                    cooked = authenticated_cmds.latest.invite_list.InviteListItemUser(
                        token=invitation.token,
                        created_on=invitation.created_on,
                        claimer_email=invitation.claimer_email,
                        status=invitation.status,
                    )
                case DeviceInvitation():
                    cooked = authenticated_cmds.latest.invite_list.InviteListItemDevice(
                        token=invitation.token,
                        created_on=invitation.created_on,
                        status=invitation.status,
                    )
            cooked_invitations.append(cooked)

        return authenticated_cmds.latest.invite_list.RepOk(invitations=cooked_invitations)

    @api
    async def api_invite_info(
        self, client_ctx: InvitedClientContext, req: invited_cmds.latest.invite_info.Req
    ) -> invited_cmds.latest.invite_info.Rep:
        outcome = await self.info_as_invited(
            organization_id=client_ctx.organization_id, token=client_ctx.token
        )
        match outcome:
            case UserInvitation() as invitation:
                return invited_cmds.latest.invite_info.RepOk(
                    invited_cmds.latest.invite_info.UserOrDeviceUser(
                        claimer_email=invitation.claimer_email,
                        greeter_user_id=invitation.created_by_user_id,
                        greeter_human_handle=invitation.created_by_human_handle,
                    )
                )
            case DeviceInvitation() as invitation:
                return invited_cmds.latest.invite_info.RepOk(
                    invited_cmds.latest.invite_info.UserOrDeviceDevice(
                        greeter_user_id=invitation.created_by_user_id,
                        greeter_human_handle=invitation.created_by_human_handle,
                    )
                )
            case InviteAsInvitedInfoBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteAsInvitedInfoBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteAsInvitedInfoBadOutcome.INVITATION_NOT_FOUND:
                return client_ctx.invitation_invalid_abort()
            case InviteAsInvitedInfoBadOutcome.INVITATION_DELETED:
                return client_ctx.invitation_invalid_abort()

    @api
    async def api_invite_1_claimer_wait_peer(
        self,
        client_ctx: InvitedClientContext,
        req: invited_cmds.latest.invite_1_claimer_wait_peer.Req,
    ) -> invited_cmds.latest.invite_1_claimer_wait_peer.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_1_WAIT_PEERS,
            payload=req.claimer_public_key.encode(),
        )
        match outcome:
            case (greeter_public_key, _):
                return invited_cmds.latest.invite_1_claimer_wait_peer.RepOk(
                    PublicKey(greeter_public_key)
                )
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                    | InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE
                ) as unexpected
            ):
                assert False, unexpected

    @api
    async def api_invite_1_greeter_wait_peer(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_1_greeter_wait_peer.Req,
    ) -> authenticated_cmds.latest.invite_1_greeter_wait_peer.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_1_WAIT_PEERS,
            payload=req.greeter_public_key.encode(),
        )
        match outcome:
            case (claimer_public_key_raw, _):
                return authenticated_cmds.latest.invite_1_greeter_wait_peer.RepOk(
                    PublicKey(claimer_public_key_raw)
                )
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE as unexpected:
                assert False, unexpected
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return authenticated_cmds.latest.invite_1_greeter_wait_peer.RepInvitationNotFound()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return authenticated_cmds.latest.invite_1_greeter_wait_peer.RepInvitationDeleted()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_2a_claimer_send_hash_nonce(
        self,
        client_ctx: InvitedClientContext,
        req: invited_cmds.latest.invite_2a_claimer_send_hashed_nonce.Req,
    ) -> invited_cmds.latest.invite_2a_claimer_send_hashed_nonce.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_2_1_CLAIMER_HASHED_NONCE,
            payload=req.claimer_hashed_nonce.digest,
        )
        match outcome:
            case (_, _):
                pass
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return invited_cmds.latest.invite_2a_claimer_send_hashed_nonce.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                ) as unexpected
            ):
                assert False, unexpected

        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_2_2_GREETER_NONCE,
            payload=b"",
        )
        match outcome:
            case (greeter_nonce, _):
                return invited_cmds.latest.invite_2a_claimer_send_hashed_nonce.RepOk(greeter_nonce)
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return invited_cmds.latest.invite_2a_claimer_send_hashed_nonce.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                ) as unexpected
            ):
                assert False, unexpected

    @api
    async def api_invite_2a_greeter_get_hashed_nonce(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_2a_greeter_get_hashed_nonce.Req,
    ) -> authenticated_cmds.latest.invite_2a_greeter_get_hashed_nonce.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_2_1_CLAIMER_HASHED_NONCE,
            payload=b"",
        )
        match outcome:
            case (claimer_hashed_nonce_raw, _):
                # Should not fail given data is check on DB insertion
                claimer_hashed_nonce = HashDigest(claimer_hashed_nonce_raw)
                return authenticated_cmds.latest.invite_2a_greeter_get_hashed_nonce.RepOk(
                    claimer_hashed_nonce
                )
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return authenticated_cmds.latest.invite_2a_greeter_get_hashed_nonce.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return authenticated_cmds.latest.invite_2a_greeter_get_hashed_nonce.RepInvitationNotFound()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return authenticated_cmds.latest.invite_2a_greeter_get_hashed_nonce.RepInvitationDeleted()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_2b_greeter_send_nonce(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_2b_greeter_send_nonce.Req,
    ) -> authenticated_cmds.latest.invite_2b_greeter_send_nonce.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_2_2_GREETER_NONCE,
            payload=req.greeter_nonce,
        )
        match outcome:
            case (_, _):
                pass
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return (
                    authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepEnrollmentWrongState()
                )
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return (
                    authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepInvitationNotFound()
                )
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepInvitationDeleted()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_2_3_CLAIMER_NONCE,
            payload=b"",
        )
        match outcome:
            case (claimer_nonce, _):
                return authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepOk(claimer_nonce)
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return (
                    authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepEnrollmentWrongState()
                )
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return (
                    authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepInvitationNotFound()
                )
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return authenticated_cmds.latest.invite_2b_greeter_send_nonce.RepInvitationDeleted()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_2b_claimer_send_nonce(
        self,
        client_ctx: InvitedClientContext,
        req: invited_cmds.latest.invite_2b_claimer_send_nonce.Req,
    ) -> invited_cmds.latest.invite_2b_claimer_send_nonce.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_2_3_CLAIMER_NONCE,
            payload=req.claimer_nonce,
        )
        match outcome:
            case (_, _):
                return invited_cmds.latest.invite_2b_claimer_send_nonce.RepOk()
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return invited_cmds.latest.invite_2b_claimer_send_nonce.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                ) as unexpected
            ):
                assert False, unexpected

    @api
    async def api_invite_3a_greeter_wait_peer_trust(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_3a_greeter_wait_peer_trust.Req,
    ) -> authenticated_cmds.latest.invite_3a_greeter_wait_peer_trust.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_3_1_CLAIMER_TRUST,
            payload=b"",
        )
        match outcome:
            case (_, _):
                return authenticated_cmds.latest.invite_3a_greeter_wait_peer_trust.RepOk()
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return authenticated_cmds.latest.invite_3a_greeter_wait_peer_trust.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return authenticated_cmds.latest.invite_3a_greeter_wait_peer_trust.RepInvitationNotFound()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return authenticated_cmds.latest.invite_3a_greeter_wait_peer_trust.RepInvitationDeleted()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_3b_claimer_wait_peer_trust(
        self,
        client_ctx: InvitedClientContext,
        req: invited_cmds.latest.invite_3b_claimer_wait_peer_trust.Req,
    ) -> invited_cmds.latest.invite_3b_claimer_wait_peer_trust.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_3_2_GREETER_TRUST,
            payload=b"",
        )
        match outcome:
            case (_, _):
                return invited_cmds.latest.invite_3b_claimer_wait_peer_trust.RepOk()
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return (
                    invited_cmds.latest.invite_3b_claimer_wait_peer_trust.RepEnrollmentWrongState()
                )
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                ) as unexpected
            ):
                assert False, unexpected

    @api
    async def api_invite_3b_greeter_signify_trust(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_3b_greeter_signify_trust.Req,
    ) -> authenticated_cmds.latest.invite_3b_greeter_signify_trust.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_3_2_GREETER_TRUST,
            payload=b"",
        )
        match outcome:
            case (_, _):
                return authenticated_cmds.latest.invite_3b_greeter_signify_trust.RepOk()
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return authenticated_cmds.latest.invite_3b_greeter_signify_trust.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return authenticated_cmds.latest.invite_3b_greeter_signify_trust.RepInvitationNotFound()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return (
                    authenticated_cmds.latest.invite_3b_greeter_signify_trust.RepInvitationDeleted()
                )
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_3a_claimer_signify_trust(
        self,
        client_ctx: InvitedClientContext,
        req: invited_cmds.latest.invite_3a_claimer_signify_trust.Req,
    ) -> invited_cmds.latest.invite_3a_claimer_signify_trust.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_3_1_CLAIMER_TRUST,
            payload=b"",
        )
        match outcome:
            case (_, _):
                return invited_cmds.latest.invite_3a_claimer_signify_trust.RepOk()
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return invited_cmds.latest.invite_3a_claimer_signify_trust.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                ) as unexpected
            ):
                assert False, unexpected

    @api
    async def api_invite_4_greeter_communicate(
        self,
        client_ctx: AuthenticatedClientContext,
        req: authenticated_cmds.latest.invite_4_greeter_communicate.Req,
    ) -> authenticated_cmds.latest.invite_4_greeter_communicate.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=client_ctx.user_id,
            token=req.token,
            state=ConduitState.STATE_4_COMMUNICATE,
            payload=req.payload,
            last=req.last,
        )
        match outcome:
            case (answer_payload, _):
                return authenticated_cmds.latest.invite_4_greeter_communicate.RepOk(
                    payload=answer_payload
                )
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return (
                    authenticated_cmds.latest.invite_4_greeter_communicate.RepEnrollmentWrongState()
                )
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                return (
                    authenticated_cmds.latest.invite_4_greeter_communicate.RepInvitationNotFound()
                )
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                return authenticated_cmds.latest.invite_4_greeter_communicate.RepInvitationDeleted()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND:
                client_ctx.author_not_found_abort()
            case InviteConduitExchangeBadOutcome.AUTHOR_REVOKED:
                client_ctx.author_revoked_abort()

    @api
    async def api_invite_4_claimer_communicate(
        self,
        client_ctx: InvitedClientContext,
        req: invited_cmds.latest.invite_4_claimer_communicate.Req,
    ) -> invited_cmds.latest.invite_4_claimer_communicate.Rep:
        outcome = await self.conduit_exchange(
            organization_id=client_ctx.organization_id,
            greeter=None,
            token=client_ctx.token,
            state=ConduitState.STATE_4_COMMUNICATE,
            payload=req.payload,
        )
        match outcome:
            case (answer_payload, last):
                return invited_cmds.latest.invite_4_claimer_communicate.RepOk(
                    payload=answer_payload, last=last
                )
            case InviteConduitExchangeBadOutcome.ENROLLMENT_WRONG_STATE:
                return invited_cmds.latest.invite_4_claimer_communicate.RepEnrollmentWrongState()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_NOT_FOUND:
                client_ctx.organization_not_found_abort()
            case InviteConduitExchangeBadOutcome.ORGANIZATION_EXPIRED:
                client_ctx.organization_expired_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_NOT_FOUND:
                client_ctx.invitation_invalid_abort()
            case InviteConduitExchangeBadOutcome.INVITATION_DELETED:
                client_ctx.invitation_invalid_abort()
            case (
                (
                    InviteConduitExchangeBadOutcome.AUTHOR_NOT_FOUND
                    | InviteConduitExchangeBadOutcome.AUTHOR_REVOKED
                ) as unexpected
            ):
                assert False, unexpected
