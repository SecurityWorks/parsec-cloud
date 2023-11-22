# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPL-3.0 2016-present Scille SAS
from __future__ import annotations

import pytest

from parsec._parsec import (
    DateTime,
    RealmStatusRepNotAllowed,
    RealmStatusRepOk,
    RealmStatusRepRealmDeleted,
)
from parsec.api.data import RealmRoleCertificate
from parsec.api.protocol import RealmRole
from tests.backend.common import realm_status, realm_update_roles


@pytest.mark.trio
async def test_status(bob_ws, alice_ws, alice, bob, maybe_archived_realm):
    rep = await realm_status(alice_ws, maybe_archived_realm)
    assert rep == RealmStatusRepOk(
        in_maintenance=False,
        maintenance_type=None,
        maintenance_started_by=None,
        maintenance_started_on=None,
        encryption_revision=1,
    )
    # Cheap test on no access
    rep = await realm_status(bob_ws, maybe_archived_realm)
    assert isinstance(rep, RealmStatusRepNotAllowed)
    # Also test lesser role have access
    await realm_update_roles(
        alice_ws,
        RealmRoleCertificate(
            author=alice.device_id,
            timestamp=DateTime.now(),
            realm_id=maybe_archived_realm,
            user_id=bob.user_id,
            role=RealmRole.READER,
        ).dump_and_sign(alice.signing_key),
    )
    rep = await realm_status(bob_ws, maybe_archived_realm)
    assert rep == RealmStatusRepOk(
        in_maintenance=False,
        maintenance_type=None,
        maintenance_started_by=None,
        maintenance_started_on=None,
        encryption_revision=1,
    )


@pytest.mark.trio
async def test_status_deleted(alice_ws, deleted_realm):
    rep = await realm_status(alice_ws, deleted_realm)
    assert rep == RealmStatusRepRealmDeleted()