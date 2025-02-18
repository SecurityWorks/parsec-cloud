# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import asyncio

import pytest

from parsec._parsec import (
    DateTime,
    HashAlgorithm,
    RealmKeyRotationCertificate,
    RealmRole,
    RevokedUserCertificate,
    SecretKey,
    SecretKeyAlgorithm,
    UserProfile,
    VlobID,
    authenticated_cmds,
)
from parsec.events import EventRealmCertificate
from tests.common import (
    Backend,
    CoolorgRpcClients,
    HttpCommonErrorsTester,
    generate_realm_role_certificate,
    get_last_realm_certificate_timestamp,
)
from tests.common.data import alice_gives_profile


@pytest.mark.parametrize(
    "kind",
    ("as_admin", "as_standard"),
)
async def test_authenticated_realm_create_ok(
    coolorg: CoolorgRpcClients, backend: Backend, kind: str
) -> None:
    match kind:
        case "as_admin":
            author = coolorg.alice
        case "as_standard":
            author = coolorg.bob
        case unknown:
            assert False, unknown

    certif = generate_realm_role_certificate(
        coolorg,
        author=author.device_id,
        user_id=author.user_id,
        role=RealmRole.OWNER,
        realm_id=VlobID.new(),
    )

    expected_topics = await backend.organization.test_dump_topics(coolorg.organization_id)
    expected_topics.realms[certif.realm_id] = certif.timestamp

    with backend.event_bus.spy() as spy:
        rep = await author.realm_create(
            realm_role_certificate=certif.dump_and_sign(author.signing_key)
        )
        assert rep == authenticated_cmds.latest.realm_create.RepOk()
        await spy.wait_event_occurred(
            EventRealmCertificate(
                organization_id=coolorg.organization_id,
                timestamp=certif.timestamp,
                realm_id=certif.realm_id,
                user_id=certif.user_id,
                role_removed=False,
            )
        )

    topics = await backend.organization.test_dump_topics(coolorg.organization_id)
    assert topics == expected_topics


async def test_authenticated_realm_create_realm_already_exists(
    coolorg: CoolorgRpcClients,
) -> None:
    certif = generate_realm_role_certificate(
        coolorg, user_id=coolorg.alice.user_id, role=RealmRole.OWNER
    )
    rep = await coolorg.alice.realm_create(
        realm_role_certificate=certif.dump_and_sign(coolorg.alice.signing_key)
    )
    assert rep == authenticated_cmds.latest.realm_create.RepRealmAlreadyExists(
        last_realm_certificate_timestamp=get_last_realm_certificate_timestamp(
            testbed_template=coolorg.testbed_template,
            realm_id=coolorg.wksp1_id,
        )
    )


@pytest.mark.parametrize(
    "kind",
    (
        "dummy_data",
        "bad_author",
    ),
)
async def test_authenticated_realm_create_invalid_certificate(
    coolorg: CoolorgRpcClients,
    kind: str,
) -> None:
    match kind:
        case "dummy_data":
            certif = b"<dummy data>"

        case "bad_author":
            certif = generate_realm_role_certificate(
                coolorg,
                author=coolorg.bob.device_id,
                user_id=coolorg.bob.user_id,
                role=RealmRole.OWNER,
                realm_id=VlobID.new(),
            ).dump_and_sign(coolorg.bob.signing_key)

        case unknown:
            assert False, unknown

    rep = await coolorg.alice.realm_create(realm_role_certificate=certif)
    assert rep == authenticated_cmds.latest.realm_create.RepInvalidCertificate()


async def test_authenticated_realm_create_timestamp_out_of_ballpark(
    coolorg: CoolorgRpcClients,
    timestamp_out_of_ballpark: DateTime,
) -> None:
    certif = generate_realm_role_certificate(
        coolorg,
        user_id=coolorg.alice.user_id,
        role=RealmRole.OWNER,
        realm_id=VlobID.new(),
        timestamp=timestamp_out_of_ballpark,
    )
    rep = await coolorg.alice.realm_create(
        realm_role_certificate=certif.dump_and_sign(coolorg.alice.signing_key)
    )
    assert isinstance(rep, authenticated_cmds.latest.realm_create.RepTimestampOutOfBallpark)
    assert rep.ballpark_client_early_offset == 300.0
    assert rep.ballpark_client_late_offset == 320.0
    assert rep.client_timestamp == timestamp_out_of_ballpark


async def test_authenticated_realm_create_isolated_from_other_realms(
    coolorg: CoolorgRpcClients,
    backend: Backend,
) -> None:
    t0 = DateTime.now()
    t1 = t0.add(seconds=1)

    # 1) Perform certificate & vlob changes in another realm...

    outcome = await backend.realm.rotate_key(
        now=t0,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        author_verify_key=coolorg.alice.signing_key.verify_key,
        keys_bundle=b"",
        per_participant_keys_bundle_access={
            coolorg.alice.user_id: b"<alice keys bundle access>",
            coolorg.bob.user_id: b"<bob keys bundle access>",
        },
        realm_key_rotation_certificate=RealmKeyRotationCertificate(
            author=coolorg.alice.device_id,
            timestamp=t0,
            hash_algorithm=HashAlgorithm.SHA256,
            encryption_algorithm=SecretKeyAlgorithm.BLAKE2B_XSALSA20_POLY1305,
            key_index=2,
            realm_id=coolorg.wksp1_id,
            key_canary=SecretKey.generate().encrypt(b""),
        ).dump_and_sign(coolorg.alice.signing_key),
    )
    assert isinstance(outcome, RealmKeyRotationCertificate)

    outcome = await backend.vlob.create(
        now=t1,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        realm_id=coolorg.wksp1_id,
        vlob_id=VlobID.new(),
        key_index=2,
        timestamp=t1,
        blob=b"<dummy>",
    )
    assert outcome is None

    # 2) ...this shouldn't impact our operation realms are isolated from each others

    certif = generate_realm_role_certificate(
        coolorg,
        user_id=coolorg.alice.user_id,
        role=RealmRole.OWNER,
        realm_id=VlobID.new(),
        timestamp=t0,
    )
    rep = await coolorg.alice.realm_create(
        realm_role_certificate=certif.dump_and_sign(coolorg.alice.signing_key)
    )

    assert rep == authenticated_cmds.latest.realm_create.RepOk()


@pytest.mark.parametrize(
    "timestamp_offset",
    (pytest.param(0, id="same_timestamp"), pytest.param(1, id="previous_timestamp")),
)
async def test_authenticated_realm_create_require_greater_timestamp(
    coolorg: CoolorgRpcClients,
    backend: Backend,
    timestamp_offset: int,
) -> None:
    last_certificate_timestamp = DateTime.now()
    same_or_previous_timestamp = last_certificate_timestamp.subtract(seconds=timestamp_offset)

    # 1) Perform a a key rotation to add a new certificate at last_certificate_timestamp

    outcome = await backend.user.revoke_user(
        now=last_certificate_timestamp,
        organization_id=coolorg.organization_id,
        author=coolorg.alice.device_id,
        author_verify_key=coolorg.alice.signing_key.verify_key,
        revoked_user_certificate=RevokedUserCertificate(
            author=coolorg.alice.device_id,
            timestamp=last_certificate_timestamp,
            user_id=coolorg.mallory.user_id,
        ).dump_and_sign(coolorg.alice.signing_key),
    )
    assert isinstance(outcome, RevokedUserCertificate)

    # 2) Try to create a realm with same or previous timestamp

    certif = generate_realm_role_certificate(
        coolorg,
        user_id=coolorg.alice.user_id,
        role=RealmRole.OWNER,
        realm_id=VlobID.new(),
        timestamp=same_or_previous_timestamp,
    )
    rep = await coolorg.alice.realm_create(
        realm_role_certificate=certif.dump_and_sign(coolorg.alice.signing_key)
    )
    assert rep == authenticated_cmds.latest.realm_create.RepRequireGreaterTimestamp(
        strictly_greater_than=last_certificate_timestamp
    )


@pytest.mark.parametrize(
    "kind",
    (
        "never_allowed",
        "no_longer_allowed",
        "realm_already_exists_and_not_allowed",
    ),
)
async def test_authenticated_realm_create_author_not_allowed(
    coolorg: CoolorgRpcClients,
    backend: Backend,
    kind: str,
) -> None:
    match kind:
        case "never_allowed":
            # Mallory starts as `OUTSIDER`
            author = coolorg.mallory
            realm_id = VlobID.new()
            pass

        case "no_longer_allowed":
            await alice_gives_profile(coolorg, backend, coolorg.bob.user_id, UserProfile.OUTSIDER)
            author = coolorg.bob
            realm_id = VlobID.new()

        case "realm_already_exists_and_not_allowed":
            author = coolorg.mallory
            realm_id = coolorg.wksp1_id

        case _:
            assert False

    certif = generate_realm_role_certificate(
        coolorg,
        author=author.device_id,
        user_id=author.user_id,
        role=RealmRole.OWNER,
        realm_id=realm_id,
    )
    rep = await author.realm_create(realm_role_certificate=certif.dump_and_sign(author.signing_key))
    assert rep == authenticated_cmds.v5.realm_create.RepAuthorNotAllowed()


async def test_authenticated_realm_create_http_common_errors(
    coolorg: CoolorgRpcClients,
    authenticated_http_common_errors_tester: HttpCommonErrorsTester,
) -> None:
    async def do():
        certif = generate_realm_role_certificate(
            coolorg,
            user_id=coolorg.alice.user_id,
            role=RealmRole.OWNER,
            realm_id=VlobID.new(),
        )
        await coolorg.alice.realm_create(
            realm_role_certificate=certif.dump_and_sign(coolorg.alice.signing_key)
        )

    await authenticated_http_common_errors_tester(do)


async def test_authenticated_realm_create_concurrency(
    coolorg: CoolorgRpcClients,
    backend: Backend,
) -> None:
    now = DateTime.now()

    # Generate 10 certificates
    certifs = [
        generate_realm_role_certificate(
            coolorg,
            user_id=coolorg.alice.user_id,
            role=RealmRole.OWNER,
            realm_id=VlobID.new(),
            timestamp=now,
        )
        for _ in range(10)
    ]

    # Create 2 requests for each certificate
    coroutines = [
        coolorg.alice.realm_create(
            realm_role_certificate=certif.dump_and_sign(coolorg.alice.signing_key)
        )
        for certif in certifs
        for _ in range(2)
    ]

    # Run all requests concurrently
    reps = await asyncio.gather(*coroutines, return_exceptions=True)

    # We expect 10 successful responses
    ok_reps = [rep for rep in reps if rep == authenticated_cmds.latest.realm_create.RepOk()]
    assert len(ok_reps) == 10

    # We expect 10 bad key index or require greater timestamp responses
    non_ok_reps = [
        rep
        for rep in reps
        if isinstance(rep, authenticated_cmds.latest.realm_create.RepRealmAlreadyExists)
    ]
    assert len(non_ok_reps) == 10
