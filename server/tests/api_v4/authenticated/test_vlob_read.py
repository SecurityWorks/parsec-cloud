# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from parsec._parsec import DateTime, DeviceID, OrganizationID, VlobID, authenticated_cmds
from tests.common import Backend, CoolorgRpcClients


async def create_vlob(
    backend: Backend,
    organization_id: OrganizationID,
    author: DeviceID,
    realm_id: VlobID,
    dt: DateTime,
    versions: int = 1,
) -> VlobID:
    vlob_id = VlobID.new()
    for version in range(1, versions + 1):
        v1_blob = f"<block content v{version}>".encode()
        if version == 1:
            outcome = await backend.vlob.create(
                now=dt,
                organization_id=organization_id,
                author=author,
                realm_id=realm_id,
                vlob_id=vlob_id,
                blob=v1_blob,
                timestamp=dt,
                sequester_blob=None,
            )
        else:
            outcome = await backend.vlob.update(
                now=dt,
                organization_id=organization_id,
                author=author,
                vlob_id=vlob_id,
                version=version,
                blob=v1_blob,
                timestamp=dt,
                sequester_blob=None,
            )
        assert outcome is None, outcome
        dt = dt.add(days=1)
    return vlob_id


async def test_authenticated_vlob_read_ok(coolorg: CoolorgRpcClients, backend: Backend) -> None:
    dt = DateTime(2020, 1, 1)
    vlob1_id = await create_vlob(
        backend=backend,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        realm_id=coolorg.wksp1_id,
        dt=dt,
        versions=3,
    )
    vlob2_id = await create_vlob(
        backend=backend,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        realm_id=coolorg.wksp1_id,
        dt=dt,
    )
    await create_vlob(
        backend=backend,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        realm_id=coolorg.wksp1_id,
        dt=dt,
    )

    rep = await coolorg.alice.vlob_read(realm_id=coolorg.wksp1_id, vlobs=[vlob1_id, vlob2_id])
    assert rep == authenticated_cmds.v4.vlob_read.RepOk(
        vlobs=[
            (vlob1_id, coolorg.alice.device_id, 3, DateTime(2020, 1, 3), b"<block content v3>"),
            (vlob2_id, coolorg.alice.device_id, 1, DateTime(2020, 1, 1), b"<block content v1>"),
        ]
    )
