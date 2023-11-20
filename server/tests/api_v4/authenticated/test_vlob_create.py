# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from unittest.mock import ANY

from parsec._parsec import DateTime, VlobID, authenticated_cmds
from parsec.events import EventVlob
from tests.common import Backend, CoolorgRpcClients


async def test_authenticated_vlob_create_ok(coolorg: CoolorgRpcClients, backend: Backend) -> None:
    vlob_id = VlobID.new()
    initial_dump = await backend.vlob.test_dump_vlobs(organization_id=coolorg.organization_id)

    v1_blob = b"<block content>"
    v1_timestamp = DateTime.now()
    with backend.event_bus.spy() as spy:
        rep = await coolorg.alice.vlob_create(
            realm_id=coolorg.wksp1_id,
            vlob_id=vlob_id,
            blob=v1_blob,
            timestamp=v1_timestamp,
            sequester_blob=None,
        )
        assert rep == authenticated_cmds.v4.vlob_create.RepOk()

        await spy.wait_event_occurred(
            EventVlob(
                organization_id=coolorg.organization_id,
                author=coolorg.alice.device_id,
                realm_id=coolorg.wksp1_id,
                timestamp=v1_timestamp,
                vlob_id=vlob_id,
                version=1,
                blob=v1_blob,
                last_common_certificate_timestamp=DateTime(2000, 1, 6),
                last_realm_certificate_timestamp=DateTime(2000, 1, 10),
            )
        )

    dump = await backend.vlob.test_dump_vlobs(organization_id=coolorg.organization_id)
    assert dump == {
        **initial_dump,
        vlob_id: [(coolorg.alice.device_id, ANY, coolorg.wksp1_id, v1_blob)],
    }


# TODO: check that blob bigger than EVENT_VLOB_MAX_BLOB_SIZE doesn't get in the event
