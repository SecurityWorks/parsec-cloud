# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
import anyio
import pytest

from parsec._parsec import InvitationToken, authenticated_cmds, invited_cmds
from tests.common import CoolorgRpcClients
from tests.common.invite import pass_state_3b_greeter_signify_trust

Response = authenticated_cmds.v4.invite_4_greeter_communicate.Rep | None


@pytest.mark.parametrize("run_order", ("greeter_first", "claimer_first"))
async def test_authenticated_invite_4_greeter_communicate_ok(
    run_order: str, coolorg: CoolorgRpcClients
) -> None:
    rep: Response = None
    claimer_payload = b"claimer-payload"
    greeter_payload = b"greeter-payload"

    await pass_state_3b_greeter_signify_trust(coolorg.invited_alice_dev3, coolorg.alice)

    async def claimer_step_4(cancel_scope: anyio.CancelScope):
        rep = await coolorg.invited_alice_dev3.invite_4_claimer_communicate(claimer_payload)
        assert rep == invited_cmds.v4.invite_4_claimer_communicate.RepOk(
            payload=greeter_payload, last=True
        )

    async def greeter_step_4(cancel_scope: anyio.CancelScope):
        nonlocal rep
        rep = await coolorg.alice.invite_4_greeter_communicate(
            coolorg.invited_alice_dev3.token, greeter_payload, True
        )
        cancel_scope.cancel()

    match run_order:
        case "greeter_first":
            first = greeter_step_4
            second = claimer_step_4
        case "claimer_first":
            first = claimer_step_4
            second = greeter_step_4
        case unknown:
            assert False, unknown

    async with anyio.create_task_group() as tg:
        tg.start_soon(first, tg.cancel_scope)

        await second(tg.cancel_scope)

    assert rep == authenticated_cmds.v4.invite_4_greeter_communicate.RepOk(payload=claimer_payload)


async def test_authenticated_invite_4_greeter_communicate_invitation_not_found(
    coolorg: CoolorgRpcClients,
) -> None:
    rep = await coolorg.alice.invite_4_greeter_communicate(InvitationToken.new(), b"payload", True)
    assert rep == authenticated_cmds.v4.invite_4_greeter_communicate.RepInvitationNotFound()


async def test_authenticated_invite_4_greeter_communicate_invitation_deleted(
    coolorg: CoolorgRpcClients,
) -> None:
    await coolorg.alice.invite_cancel(coolorg.invited_alice_dev3.token)

    rep = await coolorg.alice.invite_4_greeter_communicate(
        coolorg.invited_alice_dev3.token, b"payload", True
    )
    assert rep == authenticated_cmds.v4.invite_4_greeter_communicate.RepInvitationDeleted()


async def test_authenticated_invite_4_greeter_communicate_enrollment_wrong_state(
    coolorg: CoolorgRpcClients,
) -> None:
    rep = await coolorg.alice.invite_4_greeter_communicate(
        coolorg.invited_alice_dev3.token, b"payload", True
    )
    assert rep == authenticated_cmds.v4.invite_4_greeter_communicate.RepEnrollmentWrongState()
