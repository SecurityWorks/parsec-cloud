import trio
import pendulum
from unittest.mock import Mock
from inspect import iscoroutinefunction
from copy import deepcopy

from parsec.core.local_db import LocalDB, LocalDBMissingEntry
from parsec.networking import CookedSocket


class InMemoryLocalDB(LocalDB):
    def __init__(self):
        self._data = {}

    def get(self, access):
        try:
            return deepcopy(self._data[access["id"]])
        except KeyError:
            raise LocalDBMissingEntry(access)

    def set(self, access, manifest):
        self._data[access["id"]] = deepcopy(manifest)

    def clear(self, access):
        del self._data[access["id"]]


def freeze_time(timestr):
    return pendulum.test(pendulum.parse(timestr))


class AsyncMock(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        spec = kwargs.get("spec")
        if spec:
            for field in dir(spec):
                if iscoroutinefunction(getattr(spec, field)):
                    getattr(self, field).is_async = True

    async def __async_call(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if getattr(self, "is_async", False) is True:
            if iscoroutinefunction(self.side_effect):
                return self.side_effect(*args, **kwargs)

            else:
                return self.__async_call(*args, **kwargs)

        else:
            return super().__call__(*args, **kwargs)


class FreezeTestOnBrokenStreamCookedSocket(CookedSocket):
    """
    When a server crashes during test, it is possible the client coroutine
    receives a `trio.BrokenStreamError` exception. Hence we end up with two
    exceptions: the server crash (i.e. the original exception we are interested
    into) and the client not receiving an answer.
    The solution is simply to freeze the coroutine receiving the broken stream
    error until it will be cancelled by the original exception bubbling up.
    """

    async def send(self, msg):
        try:
            return await super().send(msg)

        except trio.BrokenStreamError as exc:
            # Wait here until this coroutine is cancelled
            await trio.sleep_forever()

    async def recv(self):
        try:
            return await super().recv()

        except trio.BrokenStreamError as exc:
            # Wait here until this coroutine is cancelled
            await trio.sleep_forever()


def connect_signal_as_event(signal_ns, signal_name):
    event = trio.Event()
    callback = Mock(spec_set=())
    callback.side_effect = lambda *args, **kwargs: event.set()

    event.cb = callback  # Prevent weakref destruction
    signal_ns.signal(signal_name).connect(callback, weak=True)
    return event
