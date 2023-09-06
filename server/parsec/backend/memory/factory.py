# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

import math
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Tuple
from uuid import uuid4

import trio

from parsec.backend.blockstore import blockstore_factory
from parsec.backend.config import BackendConfig
from parsec.backend.events import BackendEvent, EventsComponent
from parsec.backend.memory.block import MemoryBlockComponent
from parsec.backend.memory.invite import MemoryInviteComponent
from parsec.backend.memory.message import MemoryMessageComponent
from parsec.backend.memory.organization import MemoryOrganizationComponent
from parsec.backend.memory.ping import MemoryPingComponent
from parsec.backend.memory.pki import MemoryPkiEnrollmentComponent
from parsec.backend.memory.realm import MemoryRealmComponent
from parsec.backend.memory.sequester import MemorySequesterComponent
from parsec.backend.memory.user import MemoryUserComponent
from parsec.backend.memory.vlob import MemoryVlobComponent
from parsec.backend.webhooks import WebhooksComponent
from parsec.event_bus import EventBus
from parsec.utils import open_service_nursery


@asynccontextmanager
async def components_factory(  # type: ignore[misc]
    config: BackendConfig, event_bus: EventBus
) -> AsyncGenerator[dict[str, Any], None]:
    send_events_channel, receive_events_channel = trio.open_memory_channel[
        Tuple[str, BackendEvent]
    ](math.inf)

    async def _send_event(event: BackendEvent) -> None:
        event_id = uuid4().hex
        await send_events_channel.send((event_id, event))

    webhooks = WebhooksComponent(config)
    organization = MemoryOrganizationComponent(_send_event, webhooks, config)
    user = MemoryUserComponent(_send_event, event_bus)
    invite = MemoryInviteComponent(_send_event, event_bus, config)
    message = MemoryMessageComponent(_send_event)
    realm = MemoryRealmComponent(_send_event)
    vlob = MemoryVlobComponent(_send_event)
    ping = MemoryPingComponent(_send_event)
    pki = MemoryPkiEnrollmentComponent(_send_event)
    sequester = MemorySequesterComponent()
    block = MemoryBlockComponent()
    blockstore = blockstore_factory(config.blockstore_config)
    events = EventsComponent(realm, send_event=_send_event)

    components = {
        "events": events,
        "webhooks": webhooks,
        "organization": organization,
        "user": user,
        "invite": invite,
        "message": message,
        "realm": realm,
        "vlob": vlob,
        "ping": ping,
        "pki": pki,
        "sequester": sequester,
        "block": block,
        "blockstore": blockstore,
    }
    for component in components.values():
        method = getattr(component, "register_components", None)
        if method is not None:
            method(**components)

    async def _dispatch_event() -> None:
        async for (event_id, event) in receive_events_channel:
            await trio.sleep(0)
            events.add_event_to_cache(event_id, event)
            event_bus.send(type(event), event_id=event_id, payload=event)

    async with open_service_nursery() as nursery:
        nursery.start_soon(_dispatch_event)
        try:
            yield components

        finally:
            nursery.cancel_scope.cancel()