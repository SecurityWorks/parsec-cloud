# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS


from parsec._parsec import (
    DateTime,
    EmailAddress,
    InvitationStatus,
    ShamirRecoveryDeletionCertificate,
    authenticated_cmds,
)
from tests.common import (
    Backend,
    CoolorgRpcClients,
    HttpCommonErrorsTester,
    MinimalorgRpcClients,
    ShamirOrgRpcClients,
    bob_becomes_admin,
)


async def test_authenticated_invite_list_ok_with_shamir_recovery(
    shamirorg: ShamirOrgRpcClients,
    backend: Backend,
) -> None:
    expected_invitations = [
        authenticated_cmds.latest.invite_list.InviteListItemShamirRecovery(
            created_on=shamirorg.shamir_invited_alice.event.created_on,
            created_by=authenticated_cmds.latest.invite_list.InvitationCreatedByUser(
                user_id=shamirorg.bob.user_id,
                human_handle=shamirorg.bob.human_handle,
            ),
            status=InvitationStatus.PENDING,
            claimer_user_id=shamirorg.alice.user_id,
            shamir_recovery_created_on=shamirorg.alice_brief_certificate.timestamp,
            token=shamirorg.shamir_invited_alice.token,
        )
    ]

    rep = await shamirorg.alice.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == []

    rep = await shamirorg.bob.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == expected_invitations

    rep = await shamirorg.mike.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == expected_invitations

    rep = await shamirorg.mallory.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == expected_invitations


async def test_authenticated_invite_list_ok(
    minimalorg: MinimalorgRpcClients, backend: Backend
) -> None:
    expected_invitations = []

    # IDLE device invitation
    t1 = DateTime(2020, 1, 1)
    outcome = await backend.invite.new_for_device(
        now=t1,
        organization_id=minimalorg.organization_id,
        author=minimalorg.alice.device_id,
        send_email=False,
    )
    assert isinstance(outcome, tuple)
    expected_invitations.append(
        authenticated_cmds.latest.invite_list.InviteListItemDevice(
            created_on=t1,
            created_by=authenticated_cmds.latest.invite_list.InvitationCreatedByUser(
                user_id=minimalorg.alice.user_id,
                human_handle=minimalorg.alice.human_handle,
            ),
            status=InvitationStatus.PENDING,
            token=outcome[0],
        )
    )

    # IDLE user invitation
    t2 = DateTime(2020, 1, 2)
    outcome = await backend.invite.new_for_user(
        now=t2,
        organization_id=minimalorg.organization_id,
        author=minimalorg.alice.device_id,
        claimer_email=EmailAddress("zack@example.invalid"),
        send_email=False,
    )
    assert isinstance(outcome, tuple)
    expected_invitations.append(
        authenticated_cmds.latest.invite_list.InviteListItemUser(
            created_on=t2,
            created_by=authenticated_cmds.latest.invite_list.InvitationCreatedByUser(
                user_id=minimalorg.alice.user_id,
                human_handle=minimalorg.alice.human_handle,
            ),
            status=InvitationStatus.PENDING,
            claimer_email=EmailAddress("zack@example.invalid"),
            token=outcome[0],
        )
    )

    # DELETED user invitation
    t4 = DateTime(2020, 1, 4)
    outcome = await backend.invite.new_for_user(
        now=t4,
        organization_id=minimalorg.organization_id,
        author=minimalorg.alice.device_id,
        claimer_email=EmailAddress("deleted@example.invalid"),
        send_email=False,
    )
    assert isinstance(outcome, tuple)
    t5 = DateTime(2020, 1, 5)
    await backend.invite.cancel(
        now=t5,
        organization_id=minimalorg.organization_id,
        author=minimalorg.alice.device_id,
        token=outcome[0],
    )
    expected_invitations.append(
        authenticated_cmds.latest.invite_list.InviteListItemUser(
            created_on=t4,
            created_by=authenticated_cmds.latest.invite_list.InvitationCreatedByUser(
                user_id=minimalorg.alice.user_id,
                human_handle=minimalorg.alice.human_handle,
            ),
            status=InvitationStatus.CANCELLED,
            claimer_email=EmailAddress("deleted@example.invalid"),
            token=outcome[0],
        )
    )

    rep = await minimalorg.alice.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == expected_invitations


async def test_authenticated_invite_list_with_deleted_shamir(
    shamirorg: ShamirOrgRpcClients,
) -> None:
    # Get invitations
    rep = await shamirorg.bob.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    (previous_invitation,) = rep.invitations
    assert isinstance(
        previous_invitation, authenticated_cmds.latest.invite_list.InviteListItemShamirRecovery
    )

    # Delete Alice shamir recovery
    dt = DateTime.now()
    author = shamirorg.alice
    brief = shamirorg.alice_brief_certificate
    deletion = ShamirRecoveryDeletionCertificate(
        author=author.device_id,
        timestamp=dt,
        setup_to_delete_timestamp=brief.timestamp,
        setup_to_delete_user_id=brief.user_id,
        share_recipients=set(brief.per_recipient_shares.keys()),
    ).dump_and_sign(author.signing_key)
    rep = await shamirorg.alice.shamir_recovery_delete(deletion)
    assert rep == authenticated_cmds.latest.shamir_recovery_delete.RepOk()

    # Expected invitation
    expected = authenticated_cmds.latest.invite_list.InviteListItemShamirRecovery(
        token=previous_invitation.token,
        created_on=previous_invitation.created_on,
        created_by=authenticated_cmds.latest.invite_list.InvitationCreatedByUser(
            user_id=shamirorg.bob.user_id,
            human_handle=shamirorg.bob.human_handle,
        ),
        claimer_user_id=previous_invitation.claimer_user_id,
        shamir_recovery_created_on=previous_invitation.shamir_recovery_created_on,
        status=InvitationStatus.CANCELLED,
    )

    # Check invitations
    rep = await shamirorg.bob.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    (invitation,) = rep.invitations
    assert invitation == expected


async def test_authenticated_invite_list_with_shared_user_invitations(
    coolorg: CoolorgRpcClients, backend: Backend
) -> None:
    # Bob has no invitations
    rep = await coolorg.bob.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == []

    # Save alice's user invitations
    rep = await coolorg.alice.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    expected_invitations = [
        invitation
        for invitation in rep.invitations
        if isinstance(invitation, authenticated_cmds.latest.invite_list.InviteListItemUser)
    ]

    # Bob becomes admin
    await bob_becomes_admin(coolorg, backend)

    # Bob has the same user invitations as Alice
    rep = await coolorg.bob.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == expected_invitations

    # Alice creates a new user invite
    t2 = DateTime.now()
    outcome = await backend.invite.new_for_user(
        now=t2,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        claimer_email=EmailAddress("another_zack@example.invalid"),
        send_email=False,
    )
    assert isinstance(outcome, tuple)
    expected_invitations.append(
        authenticated_cmds.latest.invite_list.InviteListItemUser(
            created_on=t2,
            created_by=authenticated_cmds.latest.invite_list.InvitationCreatedByUser(
                user_id=coolorg.alice.user_id,
                human_handle=coolorg.alice.human_handle,
            ),
            status=InvitationStatus.PENDING,
            claimer_email=EmailAddress("another_zack@example.invalid"),
            token=outcome[0],
        )
    )

    # Bob sees the new invitation
    rep = await coolorg.bob.invite_list()
    assert isinstance(rep, authenticated_cmds.latest.invite_list.RepOk)
    assert rep.invitations == expected_invitations


async def test_authenticated_invite_list_http_common_errors(
    coolorg: CoolorgRpcClients, authenticated_http_common_errors_tester: HttpCommonErrorsTester
) -> None:
    async def do():
        await coolorg.alice.invite_list()

    await authenticated_http_common_errors_tester(do)
