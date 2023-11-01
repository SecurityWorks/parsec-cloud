# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from typing import override

from parsec._parsec import (
    DateTime,
    DeviceID,
    OrganizationID,
    RealmRoleCertificate,
    UserID,
    UserProfile,
    VlobID,
)
from parsec.ballpark import RequireGreaterTimestamp, TimestampOutOfBallpark
from parsec.components.events import EventBus
from parsec.components.memory.datamodel import MemoryDatamodel, MemoryRealm, MemoryRealmUserRole
from parsec.components.realm import (
    BaseRealmComponent,
    RealmCreateStoreBadOutcome,
    RealmCreateValidateBadOutcome,
    RealmDumpRealmsGrantedRolesBadOutcome,
    RealmGetCurrentRealmsForUserBadOutcome,
    RealmGetStatsAsUserBadOutcome,
    RealmGetStatsBadOutcome,
    RealmGrantedRole,
    RealmRole,
    RealmShareStoreBadOutcome,
    RealmShareValidateBadOutcome,
    RealmStats,
    RealmUnshareStoreBadOutcome,
    RealmUnshareValidateBadOutcome,
    realm_create_validate,
    realm_share_validate,
    realm_unshare_validate,
)
from parsec.events import EventRealmCertificate


class MemoryRealmComponent(BaseRealmComponent):
    def __init__(self, data: MemoryDatamodel, event_bus: EventBus) -> None:
        self._data = data
        self._event_bus = event_bus

    @override
    async def create(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_role_certificate: bytes,
    ) -> (
        RealmRoleCertificate
        | RealmCreateValidateBadOutcome
        | TimestampOutOfBallpark
        | RealmCreateStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmCreateStoreBadOutcome.ORGANIZATION_NOT_FOUND
        if org.is_expired:
            return RealmCreateStoreBadOutcome.ORGANIZATION_EXPIRED

        try:
            author_device = org.devices[author]
        except KeyError:
            return RealmCreateStoreBadOutcome.AUTHOR_NOT_FOUND
        author_user = org.users[author.user_id]
        if author_user.is_revoked:
            return RealmCreateStoreBadOutcome.AUTHOR_REVOKED

        match realm_create_validate(
            now=now,
            expected_author=author,
            author_verify_key=author_device.cooked.verify_key,
            realm_role_certificate=realm_role_certificate,
        ):
            case RealmRoleCertificate() as certif:
                pass
            case error:
                return error

        if certif.realm_id in org.realms:
            return RealmCreateStoreBadOutcome.REALM_ALREADY_EXISTS

        # Ensure certificate consistency: our certificate must be the newest thing on the server.
        #
        # Strictly speaking there is no consistency requirement here (the new empty realm
        # has no impact on existing data).
        #
        # However we still use the same check that is applied everywhere else in order to be
        # consistent.

        assert (
            org.last_certificate_or_vlob_timestamp is not None
        )  # Bootstrap has created the first certif
        if org.last_certificate_or_vlob_timestamp >= certif.timestamp:
            return RequireGreaterTimestamp(
                strictly_greater_than=org.last_certificate_or_vlob_timestamp
            )

        # All checks are good, now we do the actual insertion

        org.last_certificate_timestamp = certif.timestamp

        org.realms[certif.realm_id] = MemoryRealm(
            realm_id=certif.realm_id,
            created_on=now,
            roles=[
                MemoryRealmUserRole(cooked=certif, realm_role_certificate=realm_role_certificate)
            ],
        )

        await self._event_bus.send(
            EventRealmCertificate(
                organization_id=organization_id,
                timestamp=certif.timestamp,
                realm_id=certif.realm_id,
                user_id=certif.user_id,
                role_removed=certif.role is None,
            )
        )

        return certif

    @override
    async def share(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_role_certificate: bytes,
        recipient_keys_bundle_access: bytes,
    ) -> (
        RealmRoleCertificate
        | RealmShareValidateBadOutcome
        | TimestampOutOfBallpark
        | RealmShareStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmShareStoreBadOutcome.ORGANIZATION_NOT_FOUND
        if org.is_expired:
            return RealmShareStoreBadOutcome.ORGANIZATION_EXPIRED

        try:
            author_device = org.devices[author]
        except KeyError:
            return RealmShareStoreBadOutcome.AUTHOR_NOT_FOUND
        author_user = org.users[author.user_id]
        if author_user.is_revoked:
            return RealmShareStoreBadOutcome.AUTHOR_REVOKED

        match realm_share_validate(
            now=now,
            expected_author=author,
            author_verify_key=author_device.cooked.verify_key,
            realm_role_certificate=realm_role_certificate,
        ):
            case RealmRoleCertificate() as certif:
                pass
            case error:
                return error

        try:
            user = org.users[certif.user_id]
        except KeyError:
            return RealmShareStoreBadOutcome.USER_NOT_FOUND

        if user.is_revoked:
            return RealmShareStoreBadOutcome.USER_REVOKED

        if user.current_profile == UserProfile.OUTSIDER and certif.role in (
            RealmRole.MANAGER,
            RealmRole.OWNER,
        ):
            return RealmShareStoreBadOutcome.ROLE_INCOMPATIBLE_WITH_OUTSIDER

        try:
            realm = org.realms[certif.realm_id]
        except KeyError:
            return RealmShareStoreBadOutcome.REALM_NOT_FOUND

        owner_only = (RealmRole.OWNER,)
        owner_or_manager = (RealmRole.OWNER, RealmRole.MANAGER)
        existing_user_role = realm.get_current_role_for(certif.user_id)
        new_user_role = certif.role
        needed_roles: tuple[RealmRole, ...]
        if existing_user_role in owner_or_manager or new_user_role in owner_or_manager:
            needed_roles = owner_only
        else:
            needed_roles = owner_or_manager

        author_role = realm.get_current_role_for(author.user_id)
        if author_role not in needed_roles:
            return RealmShareStoreBadOutcome.AUTHOR_NOT_ALLOWED

        if existing_user_role == new_user_role:
            return RealmShareStoreBadOutcome.ROLE_ALREADY_GRANTED

        # Ensure certificate consistency: our certificate must be the newest thing on the server.
        #
        # Strictly speaking consistency only requires the certificate to be more recent than
        # the the certificates involving the realm and/or the recipient user; and, similarly,
        # the vlobs created/updated by the recipient.
        #
        # However doing such precise checks is complex and error prone, so we take a simpler
        # approach by considering certificates don't change often so it's no big deal to
        # have a much more coarse approach.

        assert (
            org.last_certificate_or_vlob_timestamp is not None
        )  # Bootstrap has created the first certif
        if org.last_certificate_or_vlob_timestamp >= certif.timestamp:
            return RequireGreaterTimestamp(
                strictly_greater_than=org.last_certificate_or_vlob_timestamp
            )

        # All checks are good, now we do the actual insertion

        org.last_certificate_timestamp = certif.timestamp

        realm.roles.append(
            MemoryRealmUserRole(cooked=certif, realm_role_certificate=realm_role_certificate)
        )

        # TODO: store `recipient_keys_bundle_access` !

        await self._event_bus.send(
            EventRealmCertificate(
                organization_id=organization_id,
                timestamp=certif.timestamp,
                realm_id=certif.realm_id,
                user_id=certif.user_id,
                role_removed=certif.role is None,
            )
        )

        return certif

    @override
    async def unshare(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        author: DeviceID,
        realm_role_certificate: bytes,
    ) -> (
        RealmRoleCertificate
        | RealmUnshareValidateBadOutcome
        | TimestampOutOfBallpark
        | RealmUnshareStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmUnshareStoreBadOutcome.ORGANIZATION_NOT_FOUND
        if org.is_expired:
            return RealmUnshareStoreBadOutcome.ORGANIZATION_EXPIRED

        try:
            author_device = org.devices[author]
        except KeyError:
            return RealmUnshareStoreBadOutcome.AUTHOR_NOT_FOUND
        author_user = org.users[author.user_id]
        if author_user.is_revoked:
            return RealmUnshareStoreBadOutcome.AUTHOR_REVOKED

        match realm_unshare_validate(
            now=now,
            expected_author=author,
            author_verify_key=author_device.cooked.verify_key,
            realm_role_certificate=realm_role_certificate,
        ):
            case RealmRoleCertificate() as certif:
                pass
            case error:
                return error

        if certif.user_id not in org.users:
            return RealmUnshareStoreBadOutcome.USER_NOT_FOUND

        try:
            realm = org.realms[certif.realm_id]
        except KeyError:
            return RealmUnshareStoreBadOutcome.REALM_NOT_FOUND

        owner_only = (RealmRole.OWNER,)
        owner_or_manager = (RealmRole.OWNER, RealmRole.MANAGER)
        existing_user_role = realm.get_current_role_for(certif.user_id)
        new_user_role = certif.role
        needed_roles: tuple[RealmRole, ...]
        if existing_user_role in owner_or_manager or new_user_role in owner_or_manager:
            needed_roles = owner_only
        else:
            needed_roles = owner_or_manager

        author_role = realm.get_current_role_for(author.user_id)
        if author_role not in needed_roles:
            return RealmUnshareStoreBadOutcome.AUTHOR_NOT_ALLOWED

        if existing_user_role == new_user_role:
            return RealmUnshareStoreBadOutcome.USER_ALREADY_UNSHARED

        # Ensure certificate consistency: our certificate must be the newest thing on the server.
        #
        # Strictly speaking consistency only requires the certificate to be more recent than
        # the the certificates involving the realm and/or the recipient user; and, similarly,
        # the vlobs created/updated by the recipient.
        #
        # However doing such precise checks is complex and error prone, so we take a simpler
        # approach by considering certificates don't change often so it's no big deal to
        # have a much more coarse approach.

        assert (
            org.last_certificate_or_vlob_timestamp is not None
        )  # Bootstrap has created the first certif
        if org.last_certificate_or_vlob_timestamp >= certif.timestamp:
            return RequireGreaterTimestamp(
                strictly_greater_than=org.last_certificate_or_vlob_timestamp
            )

        # All checks are good, now we do the actual insertion

        org.last_certificate_timestamp = certif.timestamp

        realm.roles.append(
            MemoryRealmUserRole(cooked=certif, realm_role_certificate=realm_role_certificate)
        )

        await self._event_bus.send(
            EventRealmCertificate(
                organization_id=organization_id,
                timestamp=certif.timestamp,
                realm_id=certif.realm_id,
                user_id=certif.user_id,
                role_removed=certif.role is None,
            )
        )

        return certif

    @override
    async def get_stats_as_user(
        self, organization_id: OrganizationID, author: DeviceID, realm_id: VlobID
    ) -> RealmStats | RealmGetStatsAsUserBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmGetStatsAsUserBadOutcome.ORGANIZATION_NOT_FOUND
        if org.is_expired:
            return RealmGetStatsAsUserBadOutcome.ORGANIZATION_EXPIRED

        if author not in org.devices:
            return RealmGetStatsAsUserBadOutcome.AUTHOR_NOT_FOUND
        author_user = org.users[author.user_id]
        if author_user.is_revoked:
            return RealmGetStatsAsUserBadOutcome.AUTHOR_REVOKED

        try:
            realm = org.realms[realm_id]
        except KeyError:
            return RealmGetStatsAsUserBadOutcome.REALM_NOT_FOUND

        if realm.get_current_role_for(author.user_id) is None:
            return RealmGetStatsAsUserBadOutcome.AUTHOR_NOT_ALLOWED

        block_size = 0
        vlob_size = 0

        for vlob in org.vlobs.values():
            for vlob_atom in vlob:
                vlob_size += len(vlob_atom.blob)

        for block in org.blocks.values():
            if block.realm_id == realm_id:
                block_size += block.block_size

        return RealmStats(
            blocks_size=block_size,
            vlobs_size=vlob_size,
        )

    @override
    async def get_stats(
        self, organization_id: OrganizationID, realm_id: VlobID
    ) -> RealmStats | RealmGetStatsBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmGetStatsBadOutcome.ORGANIZATION_NOT_FOUND

        if realm_id not in org.realms:
            return RealmGetStatsBadOutcome.REALM_NOT_FOUND

        block_size = 0
        vlob_size = 0

        for vlob in org.vlobs.values():
            for vlob_atom in vlob:
                vlob_size += len(vlob_atom.blob)

        for block in org.blocks.values():
            if block.realm_id == realm_id:
                block_size += block.block_size

        return RealmStats(
            blocks_size=block_size,
            vlobs_size=vlob_size,
        )

    @override
    async def get_current_realms_for_user(
        self, organization_id: OrganizationID, user: UserID
    ) -> dict[VlobID, RealmRole] | RealmGetCurrentRealmsForUserBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmGetCurrentRealmsForUserBadOutcome.ORGANIZATION_NOT_FOUND

        if user not in org.users:
            return RealmGetCurrentRealmsForUserBadOutcome.USER_NOT_FOUND

        user_realms = {}
        for realm in org.realms.values():
            role = realm.get_current_role_for(user)
            if role is not None:
                user_realms[realm.realm_id] = role

        return user_realms

    @override
    async def dump_realms_granted_roles(
        self, organization_id: OrganizationID
    ) -> list[RealmGrantedRole] | RealmDumpRealmsGrantedRolesBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return RealmDumpRealmsGrantedRolesBadOutcome.ORGANIZATION_NOT_FOUND

        granted_roles = []
        for realm in org.realms.values():
            for role in realm.roles:
                granted_roles.append(
                    RealmGrantedRole(
                        realm_id=realm.realm_id,
                        certificate=role.realm_role_certificate,
                        user_id=role.cooked.user_id,
                        role=role.cooked.role,
                        granted_by=role.cooked.author,
                        granted_on=role.cooked.timestamp,
                    )
                )

        return granted_roles
