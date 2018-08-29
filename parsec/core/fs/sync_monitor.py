import trio
from trio.hazmat import current_clock
from functools import partial
import logbook

from parsec.core.base import BaseAsyncComponent
from parsec.core.backend_connection import BackendNotAvailable


logger = logbook.Logger("parsec.core.fs.sync_monitor")


MIN_WAIT = 1
MAX_WAIT = 60


def timestamp():
    # Use time from trio clock to easily mock it
    return current_clock().current_time()


class SyncMonitor(BaseAsyncComponent):
    def __init__(self, syncer, signal_ns):
        super().__init__()
        self.syncer = syncer
        self.signal_ns = signal_ns
        self._task_info = None
        self._updated_entries = {}
        self._new_event = trio.Event()
        self._not_syncing_event = trio.Event()
        self._not_syncing_event.set()

    def is_syncing(self):
        return self._not_syncing_event.is_set()

    async def wait_not_syncing(self):
        await self._not_syncing_event.wait()

    async def _init(self, nursery):
        self._task_info = await nursery.start(self._task)

    async def _teardown(self):
        cancel_scope, closed_event = self._task_info
        cancel_scope.cancel()
        await closed_event.wait()
        self._task_info = None

    async def _task(self, *, task_status=trio.TASK_STATUS_IGNORED):
        backend_online_event = trio.Event()

        def _on_backend_online(*args):
            backend_online_event.set()

        self.signal_ns.signal("backend.online").connect(_on_backend_online, weak=True)

        def _on_backend_offline(*args):
            backend_online_event.clear()
            event_listener_scope.cancel()

        self.signal_ns.signal("backend.offline").connect(_on_backend_offline, weak=True)

        # `_listen_sync_loop` is going to connect to `fs.entry.updated` signal
        # we must want for this before calling ourself started, hence we must
        # provide it with a callback.
        first_started_cb_call = True

        def started_cb():
            nonlocal first_started_cb_call
            if first_started_cb_call:
                task_status.started((nursery.cancel_scope, closed_event))
                first_started_cb_call = False

        closed_event = trio.Event()
        try:
            async with trio.open_nursery() as nursery:
                while True:
                    try:
                        with trio.open_cancel_scope() as event_listener_scope:
                            self._not_syncing_event.clear()
                            try:
                                await self.syncer.full_sync()
                            finally:
                                self._not_syncing_event.set()
                            await self._listen_sync_loop(started_cb)

                    except BackendNotAvailable:
                        started_cb()
                        await backend_online_event.wait()
        finally:
            closed_event.set()

    async def _listen_sync_loop(self, started_cb):
        updated_entries = {}
        new_event = trio.Event()

        def _on_entry_updated(sender, id):
            try:
                first_updated, _ = updated_entries[id]
                last_updated = timestamp()
            except KeyError:
                first_updated = last_updated = timestamp()
            updated_entries[id] = (first_updated, last_updated)
            new_event.set()

        self.signal_ns.signal("fs.entry.updated").connect(_on_entry_updated, weak=True)

        async with trio.open_nursery() as nursery:
            while True:
                started_cb()
                await new_event.wait()
                new_event.clear()
                await self._listen_sync_step(updated_entries)

                if updated_entries:

                    async def _wait():
                        await trio.sleep(MIN_WAIT)
                        new_event.set()

                    nursery.start_soon(_wait)

    async def _listen_sync_step(self, updated_entries):
        now = timestamp()

        for id, (first_updated, last_updated) in updated_entries.items():
            if now - first_updated > MAX_WAIT:
                self._not_syncing_event.clear()
                try:
                    await self.syncer.sync_by_id(id)
                finally:
                    self._not_syncing_event.set()
                break

        else:
            for id, (_, last_updated) in updated_entries.items():
                if now - last_updated > MIN_WAIT:
                    self._not_syncing_event.clear()
                    try:
                        await self.syncer.sync_by_id(id)
                    finally:
                        self._not_syncing_event.set()
                    break

            else:
                id = None

        if id:
            _, new_last_updated = updated_entries[id]
            # This entry has been modified again during the sync
            if new_last_updated != last_updated:
                updated_entries[id] = (last_updated, new_last_updated)
            else:
                del updated_entries[id]
