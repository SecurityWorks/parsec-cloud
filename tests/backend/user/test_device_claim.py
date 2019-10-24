# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPLv3 2019 Scille SAS

import pytest
import trio
from pendulum import Pendulum
from async_generator import asynccontextmanager

from parsec.api.protocol import (
    DeviceID,
    device_get_invitation_creator_serializer,
    device_claim_serializer,
)
from parsec.backend.user import Device, DeviceInvitation, PEER_EVENT_MAX_WAIT


@pytest.fixture
async def alice_nd_invitation(backend, alice):
    invitation = DeviceInvitation(
        DeviceID(f"{alice.user_id}@new_device"), alice.device_id, Pendulum(2000, 1, 2)
    )
    await backend.user.create_device_invitation(alice.organization_id, invitation)
    return invitation


async def device_get_invitation_creator(sock, **kwargs):
    await sock.send(
        device_get_invitation_creator_serializer.req_dumps(
            {"cmd": "device_get_invitation_creator", **kwargs}
        )
    )
    raw_rep = await sock.recv()
    rep = device_get_invitation_creator_serializer.rep_loads(raw_rep)
    return rep


@asynccontextmanager
async def device_claim(sock, **kwargs):
    reps = []
    await sock.send(device_claim_serializer.req_dumps({"cmd": "device_claim", **kwargs}))
    yield reps
    raw_rep = await sock.recv()
    rep = device_claim_serializer.rep_loads(raw_rep)
    reps.append(rep)


@pytest.mark.trio
async def test_device_claim_ok(
    monkeypatch, backend, anonymous_backend_sock, alice, alice_nd_invitation, freeze_time
):
    device_invitation_retreived = trio.Event()

    vanilla_claim_device_invitation = backend.user.claim_device_invitation

    async def _mocked_claim_device_invitation(*args, **kwargs):
        ret = await vanilla_claim_device_invitation(*args, **kwargs)
        device_invitation_retreived.set()
        return ret

    monkeypatch.setattr(backend.user, "claim_device_invitation", _mocked_claim_device_invitation)

    with freeze_time(alice_nd_invitation.created_on):
        async with device_claim(
            anonymous_backend_sock,
            invited_device_id=alice_nd_invitation.device_id,
            encrypted_claim=b"<foo>",
        ) as prep:

            # `backend.user.create_device` will destroy the device invitation,
            # so make sure we retreived it before
            await device_invitation_retreived.wait()

            # No the device we are waiting for
            await backend.user.create_device(
                alice.organization_id,
                Device(
                    device_id=DeviceID(f"{alice.user_id}@dummy"),
                    device_certificate=b"<alice@dummy certificate>",
                    device_certifier=alice.device_id,
                ),
                encrypted_answer=b"<alice@dummy answer>",
            )

            await backend.user.create_device(
                alice.organization_id,
                Device(
                    device_id=alice_nd_invitation.device_id,
                    device_certificate=b"<alice@new_device certificate>",
                    device_certifier=alice.device_id,
                ),
                encrypted_answer=b"<alice@new_device answer>",
            )

    assert prep[0] == {
        "status": "ok",
        "encrypted_answer": b"<alice@new_device answer>",
        "device_certificate": b"<alice@new_device certificate>",
    }


@pytest.mark.trio
async def test_device_claim_timeout(
    mock_clock, backend, anonymous_backend_sock, alice_nd_invitation, freeze_time
):
    with freeze_time(alice_nd_invitation.created_on), backend.event_bus.listen() as spy:
        async with device_claim(
            anonymous_backend_sock,
            invited_device_id=alice_nd_invitation.device_id,
            encrypted_claim=b"<foo>",
        ) as prep:

            await spy.wait_with_timeout("event.connected", {"event_name": "device.created"})
            mock_clock.jump(PEER_EVENT_MAX_WAIT + 1)

    assert prep[0] == {
        "status": "timeout",
        "reason": "Timeout while waiting for invitation creator to answer.",
    }


@pytest.mark.trio
async def test_device_claim_denied(
    backend, anonymous_backend_sock, alice, alice_nd_invitation, freeze_time
):
    with freeze_time(alice_nd_invitation.created_on), backend.event_bus.listen() as spy:
        async with device_claim(
            anonymous_backend_sock,
            invited_device_id=alice_nd_invitation.device_id,
            encrypted_claim=b"<foo>",
        ) as prep:

            await spy.wait_with_timeout(
                "event.connected", {"event_name": "device.invitation.cancelled"}
            )
            backend.event_bus.send(
                "device.created",
                organization_id=alice.organization_id,
                device_id="dummy@foo",
                device_certificate=b"<dummy@foo certificate>",
                encrypted_answer=b"<dummy>",
            )
            backend.event_bus.send(
                "device.invitation.cancelled",
                organization_id=alice.organization_id,
                device_id=alice_nd_invitation.device_id,
            )

    assert prep[0] == {"status": "denied", "reason": "Invitation creator rejected us."}


@pytest.mark.trio
async def test_device_claim_unknown(anonymous_backend_sock, mallory):
    async with device_claim(
        anonymous_backend_sock, invited_device_id=mallory.device_id, encrypted_claim=b"<foo>"
    ) as prep:

        pass

    assert prep[0] == {"status": "not_found"}


@pytest.mark.trio
async def test_device_claim_already_exists(
    mock_clock, backend, anonymous_backend_sock, alice, alice_nd_invitation, freeze_time
):
    await backend.user.create_device(
        alice.organization_id,
        Device(
            device_id=alice_nd_invitation.device_id,
            device_certificate=b"<foo>",
            device_certifier=alice.device_id,
        ),
    )

    with freeze_time(alice_nd_invitation.created_on):
        async with device_claim(
            anonymous_backend_sock,
            invited_device_id=alice_nd_invitation.device_id,
            encrypted_claim=b"<foo>",
        ) as prep:

            pass

    assert prep[0] == {"status": "not_found"}


@pytest.mark.trio
async def test_device_claim_other_organization(
    backend, sock_from_other_organization_factory, alice, alice_nd_invitation
):
    # Organizations should be isolated
    async with sock_from_other_organization_factory(backend, anonymous=True) as sock:
        async with device_claim(
            sock, invited_device_id=alice_nd_invitation.device_id, encrypted_claim=b"<foo>"
        ) as prep:
            pass
    assert prep[0] == {"status": "not_found"}
