import pytest
import trio
from trio.testing import wait_all_tasks_blocked

from parsec.signals import get_signal
from parsec.core.backend_events_manager import BackendEventsManager

from tests.common import connect_signal_as_event
from tests.open_tcp_stream_mock_wrapper import offline


@pytest.fixture
async def backend_event_manager(nursery, signal_ns, running_backend, alice):
    em = BackendEventsManager(alice, running_backend.addr)
    await em.init(nursery)
    event_subscribed = connect_signal_as_event("backend.event.subscribed")
    await event_subscribed.wait()
    try:
        yield em

    finally:
        await em.teardown()


async def subscribe_event(device, event):
    get_signal("backend.event.subscribe").send(device.id, event=event)
    await wait_event_subscribed(device, {(event, None)})


async def wait_event_subscribed(device, expected_events):
    event_subscribed = connect_signal_as_event("backend.event.subscribed")
    with trio.fail_after(1.0):
        await event_subscribed.wait()
    event_subscribed.cb.assert_called_with(device.id, events=expected_events)


@pytest.mark.trio
async def test_subscribe_on_init(nursery, signal_ns, running_backend, alice):
    em = BackendEventsManager(alice, running_backend.addr)

    get_signal("backend.event.subscribe").send(alice.id, event="ping")

    await em.init(nursery)

    await wait_event_subscribed(alice, {("ping", None)})


@pytest.mark.trio
async def test_subscribe_event(running_backend, alice, backend_event_manager):
    await subscribe_event(alice, "ping")

    ping_received = connect_signal_as_event("ping")

    running_backend.backend.signal_ns.signal("ping").send("bob@test", msg="hello from bob")

    with trio.fail_after(1.0):
        await ping_received.wait()
    ping_received.cb.assert_called_with("bob@test", event="ping", msg="hello from bob")


@pytest.mark.trio
async def test_unsbuscribe_event(running_backend, alice, backend_event_manager):
    await subscribe_event(alice, "ping")

    get_signal("backend.event.unsubscribe").send(alice.id, event="ping")

    await wait_event_subscribed(alice, set())

    def on_ping(*args):
        raise RuntimeError("Expected not to receive this event !")

    get_signal("ping").connect(on_ping)

    running_backend.backend.signal_ns.signal("ping").send("bob@test", msg="hello from bob")

    # Nothing occured ? Then we're good !
    await wait_all_tasks_blocked(cushion=0.01)


@pytest.mark.trio
async def test_unsubscribe_unknown_event_does_nothing(signal_ns, alice, backend_event_manager):
    event_subscribed = connect_signal_as_event("backend.event.subscribed")

    get_signal("backend.event.unsubscribe").send(alice.id, event="dummy")

    await wait_all_tasks_blocked(cushion=0.01)

    assert not event_subscribed.is_set()


@pytest.mark.trio
async def test_subscribe_already_subscribed_event_does_nothing(
    signal_ns, alice, backend_event_manager
):
    await subscribe_event(alice, "ping")

    # Second subscribe is useless, event listener shouldn't be restarted

    event_subscribed = connect_signal_as_event("backend.event.subscribed")

    get_signal("backend.event.subscribe").send(alice.id, event="ping")

    await wait_all_tasks_blocked(cushion=0.01)

    assert not event_subscribed.is_set()


@pytest.mark.trio
async def test_backend_switch_offline(mock_clock, running_backend, alice, backend_event_manager):
    mock_clock.rate = 1.0

    await subscribe_event(alice, "ping")

    backend_offline = connect_signal_as_event("backend.offline")

    with offline(running_backend.addr):
        with trio.fail_after(1.0):
            await backend_offline.wait()
        backend_online = connect_signal_as_event("backend.online")
        event_subscribed = connect_signal_as_event("backend.event.subscribed")

    # Backend event manager waits before retrying to connect
    mock_clock.jump(5.0)

    with trio.fail_after(1.0):
        await backend_online.wait()
        await event_subscribed.wait()

    # Make sure event system still works as expected
    ping_received = connect_signal_as_event("ping")
    running_backend.backend.signal_ns.signal("ping").send("bob@test", msg="hello from bob")
    with trio.fail_after(1.0):
        await ping_received.wait()
    ping_received.cb.assert_called_with("bob@test", event="ping", msg="hello from bob")
