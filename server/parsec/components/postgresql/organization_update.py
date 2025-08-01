# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from functools import lru_cache

from parsec._parsec import (
    ActiveUsersLimit,
    DateTime,
    OrganizationID,
)
from parsec.components.organization import (
    OrganizationUpdateBadOutcome,
    TosLocale,
    TosUrl,
)
from parsec.components.postgresql import AsyncpgConnection
from parsec.components.postgresql.events import send_signal
from parsec.components.postgresql.utils import (
    Q,
    SqlQueryParam,
)
from parsec.config import AccountVaultStrategy, AllowedClientAgent
from parsec.events import EventOrganizationExpired, EventOrganizationTosUpdated
from parsec.types import Unset, UnsetType


@lru_cache
def _q_update_factory(
    with_is_expired: bool,
    with_active_users_limit: bool,
    with_user_profile_outsider_allowed: bool,
    with_minimum_archiving_period: bool,
    with_tos: bool,
    with_allowed_client_agent: bool,
    with_account_vault_strategy: bool,
) -> Q:
    fields = []
    if with_is_expired:
        fields.append("is_expired = $is_expired")
        fields.append("_expired_on = (CASE WHEN $is_expired THEN NOW() ELSE NULL END)")
    if with_active_users_limit:
        fields.append("active_users_limit = $active_users_limit")
    if with_user_profile_outsider_allowed:
        fields.append("user_profile_outsider_allowed = $user_profile_outsider_allowed")
    if with_minimum_archiving_period:
        fields.append("minimum_archiving_period = $minimum_archiving_period")
    if with_tos:
        fields.append("tos_updated_on = $tos_updated_on")
        fields.append("tos_per_locale_urls = $tos_per_locale_urls")
    if with_allowed_client_agent:
        fields.append("allowed_client_agent = $allowed_client_agent")
    if with_account_vault_strategy:
        fields.append("account_vault_strategy = $account_vault_strategy")

    return Q(
        f"""
            UPDATE organization
            SET
            {", ".join(fields)}
            WHERE organization_id = $organization_id
            RETURNING is_expired
        """
    )


async def organization_update(
    conn: AsyncpgConnection,
    now: DateTime,
    id: OrganizationID,
    is_expired: UnsetType | bool = Unset,
    active_users_limit: UnsetType | ActiveUsersLimit = Unset,
    user_profile_outsider_allowed: UnsetType | bool = Unset,
    minimum_archiving_period: UnsetType | int = Unset,
    tos: UnsetType | None | dict[TosLocale, TosUrl] = Unset,
    allowed_client_agent: UnsetType | AllowedClientAgent = Unset,
    account_vault_strategy: UnsetType | AccountVaultStrategy = Unset,
) -> None | OrganizationUpdateBadOutcome:
    with_is_expired = is_expired is not Unset
    with_active_users_limit = active_users_limit is not Unset
    with_user_profile_outsider_allowed = user_profile_outsider_allowed is not Unset
    with_minimum_archiving_period = minimum_archiving_period is not Unset
    with_tos = tos is not Unset
    with_allowed_client_agent = allowed_client_agent is not Unset
    with_account_vault_strategy = account_vault_strategy is not Unset

    if (
        not with_is_expired
        and not with_active_users_limit
        and not with_user_profile_outsider_allowed
        and not with_minimum_archiving_period
        and not with_tos
        and not with_allowed_client_agent
        and not with_account_vault_strategy
    ):
        # Nothing to update
        return

    fields: dict[str, SqlQueryParam] = {}
    if with_is_expired:
        fields["is_expired"] = is_expired
    if with_active_users_limit:
        assert isinstance(active_users_limit, ActiveUsersLimit)
        fields["active_users_limit"] = active_users_limit.to_maybe_int()
    if with_user_profile_outsider_allowed:
        fields["user_profile_outsider_allowed"] = user_profile_outsider_allowed
    if with_minimum_archiving_period:
        fields["minimum_archiving_period"] = minimum_archiving_period
    if with_tos:
        if tos is None:
            fields["tos_updated_on"] = None
            fields["tos_per_locale_urls"] = None
        else:
            fields["tos_updated_on"] = now
            fields["tos_per_locale_urls"] = tos
    if with_allowed_client_agent:
        fields["allowed_client_agent"] = allowed_client_agent.value
    if with_account_vault_strategy:
        fields["account_vault_strategy"] = account_vault_strategy.value

    q = _q_update_factory(
        with_is_expired=with_is_expired,
        with_active_users_limit=with_active_users_limit,
        with_user_profile_outsider_allowed=with_user_profile_outsider_allowed,
        with_minimum_archiving_period=with_minimum_archiving_period,
        with_tos=with_tos,
        with_allowed_client_agent=with_allowed_client_agent,
        with_account_vault_strategy=with_account_vault_strategy,
    )

    now_is_expired = await conn.fetchval(*q(organization_id=id.str, **fields))
    match now_is_expired:
        case bool():
            pass
        case None:
            return OrganizationUpdateBadOutcome.ORGANIZATION_NOT_FOUND
        case unknown:
            assert False, unknown

    # TODO: the event is triggered even if the orga was already expired, is this okay ?
    if now_is_expired:
        await send_signal(conn, EventOrganizationExpired(organization_id=id))

    if tos is not Unset:
        await send_signal(conn, EventOrganizationTosUpdated(organization_id=id))
