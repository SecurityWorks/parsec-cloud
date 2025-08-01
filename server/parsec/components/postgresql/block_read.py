# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from collections.abc import Buffer

from parsec._parsec import (
    BlockID,
    DateTime,
    DeviceID,
    OrganizationID,
    VlobID,
)
from parsec.components.block import (
    BlockReadBadOutcome,
    BlockReadResult,
)
from parsec.components.blockstore import (
    BaseBlockStoreComponent,
    BlockStoreReadBadOutcome,
)
from parsec.components.postgresql import AsyncpgPool
from parsec.components.postgresql.utils import (
    Q,
)
from parsec.logging import get_logger

logger = get_logger()


# `block_read` being performance critical, we rely on a single big query
# that fetches everything in one go.
_q_read_fetch_data = Q(
    """
WITH my_organization AS (
    SELECT
        _id,
        is_expired
    FROM organization
    WHERE
        organization_id = $organization_id
        -- Only consider bootstrapped organizations
        AND root_verify_key IS NOT NULL
    LIMIT 1
),

my_device AS (
    SELECT
        _id,
        user_
    FROM device
    WHERE
        organization = (SELECT my_organization._id FROM my_organization)
        AND device_id = $device_id
    LIMIT 1
),

my_user AS (
    SELECT
        _id,
        (revoked_on IS NOT NULL) AS revoked
    FROM user_
    WHERE _id = (SELECT my_device.user_ FROM my_device)
    LIMIT 1
),

my_realm AS (
    SELECT _id
    FROM realm
    WHERE
        organization = (SELECT my_organization._id FROM my_organization)
        AND realm_id = $realm_id
    LIMIT 1
),

my_block AS (
    SELECT
        _id,
        realm,
        key_index
    FROM block
    WHERE
        organization = (SELECT my_organization._id FROM my_organization)
        AND realm = (SELECT my_realm._id FROM my_realm)
        AND block_id = $block_id
    LIMIT 1
)

SELECT
    (SELECT _id FROM my_organization) AS organization_internal_id,
    (SELECT is_expired FROM my_organization) AS organization_is_expired,
    (SELECT _id FROM my_device) AS device_internal_id,
    (SELECT revoked FROM my_user) AS user_is_revoked,
    (
        SELECT last_timestamp
        FROM realm_topic
        WHERE
            organization = (SELECT my_organization._id FROM my_organization)
            AND realm = (SELECT my_realm._id FROM my_realm)
        LIMIT 1
    ) AS last_realm_certificate_timestamp,
    COALESCE(
        (
            SELECT role IS NOT NULL
            FROM realm_user_role
            WHERE
                user_ = (SELECT my_user._id FROM my_user)
                AND realm = (SELECT my_realm._id FROM my_realm)
            ORDER BY certified_on DESC
            LIMIT 1
        ),
        FALSE
    ) AS user_can_read,
    (SELECT key_index FROM my_block) AS block_key_index
"""
)


async def block_read(
    blockstore: BaseBlockStoreComponent,
    pool: AsyncpgPool,
    organization_id: OrganizationID,
    author: DeviceID,
    realm_id: VlobID,
    block_id: BlockID,
) -> BlockReadResult | BlockReadBadOutcome:
    # We shouldn't keep topics lock during step 2:
    # - Step 2 can take a long time (e.g. with a RAID blockstore configuration).
    # - In case of PostgreSQL blockstore (only used for testing), this can create
    #   a deadlock in case of too many concurrent `block_create` given the
    #   blockstore is waiting on the PostgreSQL connection pool.
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            *_q_read_fetch_data(
                organization_id=organization_id.str,
                device_id=author,
                realm_id=realm_id,
                block_id=block_id,
            )
        )
    assert row is not None

    # 1.1) Check organization

    match row["organization_internal_id"]:
        case int():
            pass
        case None:
            return BlockReadBadOutcome.ORGANIZATION_NOT_FOUND
        case _:
            assert False, row

    match row["organization_is_expired"]:
        case False:
            pass
        case True:
            return BlockReadBadOutcome.ORGANIZATION_EXPIRED
        case _:
            assert False, row

    # 1.2) Check device & user

    match row["device_internal_id"]:
        case int():
            pass
        case None:
            return BlockReadBadOutcome.AUTHOR_NOT_FOUND
        case _:
            assert False, row

    match row["user_is_revoked"]:
        case False:
            pass
        case True:
            return BlockReadBadOutcome.AUTHOR_REVOKED
        case _:
            assert False, row

    # 1.2) Check realm

    match row["last_realm_certificate_timestamp"]:
        case DateTime() as last_realm_certificate_timestamp:
            pass
        case None:
            return BlockReadBadOutcome.REALM_NOT_FOUND
        case _:
            assert False, row

    # 1.3) Check block

    match row["block_key_index"]:
        case int() as block_key_index:
            pass
        case None:
            return BlockReadBadOutcome.BLOCK_NOT_FOUND
        case _:
            assert False, row

    match row["user_can_read"]:
        case True:
            pass
        case False:
            return BlockReadBadOutcome.AUTHOR_NOT_ALLOWED
        case _:
            assert False, row

    # 2) Checks are good, we can retrieve the block

    outcome = await blockstore.read(organization_id, block_id)
    match outcome:
        case Buffer() as block:
            return BlockReadResult(
                block=block,
                key_index=block_key_index,
                needed_realm_certificate_timestamp=last_realm_certificate_timestamp,
            )
        case BlockStoreReadBadOutcome.BLOCK_NOT_FOUND:
            # Weird, the block exists in the database but not in the blockstore
            logger.warning(
                "Block present in database but not in object storage",
                organization_id=organization_id,
                realm_id=realm_id,
                block_id=block_id,
            )
            return BlockReadBadOutcome.STORE_UNAVAILABLE
        case BlockStoreReadBadOutcome.STORE_UNAVAILABLE:
            return BlockReadBadOutcome.STORE_UNAVAILABLE
