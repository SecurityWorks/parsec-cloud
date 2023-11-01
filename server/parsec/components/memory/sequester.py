# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from typing import assert_never, override

from parsec._parsec import (
    DateTime,
    OrganizationID,
    SequesterServiceCertificate,
    SequesterServiceID,
    VlobID,
)
from parsec.ballpark import RequireGreaterTimestamp
from parsec.components.events import EventBus
from parsec.components.memory.datamodel import (
    MemoryDatamodel,
    MemorySequesterService,
)
from parsec.components.sequester import (
    BaseSequesterComponent,
    BaseSequesterService,
    SequesterCreateServiceStoreBadOutcome,
    SequesterCreateServiceValidateBadOutcome,
    SequesterDisableServiceBadOutcome,
    SequesterDumpRealmBadOutcome,
    SequesterEnableServiceBadOutcome,
    SequesterGetOrganizationServicesBadOutcome,
    SequesterGetServiceBadOutcome,
    SequesterServiceType,
    StorageSequesterService,
    WebhookSequesterService,
    sequester_create_service_validate,
)
from parsec.events import EventSequesterCertificate


def _cook_service(service: MemorySequesterService) -> BaseSequesterService:
    match service.service_type:
        case SequesterServiceType.STORAGE:
            return StorageSequesterService(
                service_id=service.cooked.service_id,
                service_label=service.cooked.service_label,
                service_certificate=service.sequester_service_certificate,
                created_on=service.cooked.timestamp,
                disabled_on=service.disabled_on,
            )
        case SequesterServiceType.WEBHOOK:
            assert service.webhook_url is not None
            return WebhookSequesterService(
                service_id=service.cooked.service_id,
                service_label=service.cooked.service_label,
                service_certificate=service.sequester_service_certificate,
                created_on=service.cooked.timestamp,
                disabled_on=service.disabled_on,
                webhook_url=service.webhook_url,
            )
        case unknown:
            assert_never(unknown)


class MemorySequesterComponent(BaseSequesterComponent):
    def __init__(self, data: MemoryDatamodel, event_bus: EventBus) -> None:
        self._data = data
        self._event_bus = event_bus

    @override
    async def create_storage_service(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        service_certificate: bytes,
    ) -> (
        SequesterServiceCertificate
        | SequesterCreateServiceValidateBadOutcome
        | SequesterCreateServiceStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        return await self._create_service(
            now=now,
            organization_id=organization_id,
            service_certificate=service_certificate,
            service_type=SequesterServiceType.STORAGE,
            webhook_url=None,
        )

    @override
    async def create_webhook_service(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        service_certificate: bytes,
        webhook_url: str,
    ) -> (
        SequesterServiceCertificate
        | SequesterCreateServiceValidateBadOutcome
        | SequesterCreateServiceStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        return await self._create_service(
            now=now,
            organization_id=organization_id,
            service_certificate=service_certificate,
            service_type=SequesterServiceType.WEBHOOK,
            webhook_url=webhook_url,
        )

    async def _create_service(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        service_certificate: bytes,
        service_type: SequesterServiceType,
        webhook_url: str | None,
    ) -> (
        SequesterServiceCertificate
        | SequesterCreateServiceValidateBadOutcome
        | SequesterCreateServiceStoreBadOutcome
        | RequireGreaterTimestamp
    ):
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return SequesterCreateServiceStoreBadOutcome.ORGANIZATION_NOT_FOUND

        if org.sequester_services is None:
            return SequesterCreateServiceStoreBadOutcome.SEQUESTER_DISABLED

        assert org.cooked_sequester_authority is not None
        match sequester_create_service_validate(
            now, org.cooked_sequester_authority.verify_key_der, service_certificate
        ):
            case SequesterServiceCertificate() as certif:
                pass
            case error:
                return error

        if certif.service_id in org.sequester_services:
            return SequesterCreateServiceStoreBadOutcome.SEQUESTER_SERVICE_ALREADY_EXISTS

        # Ensure certificate consistency: our certificate must be the very last among
        # the existing sequester (authority & service) certificates.

        max_sequester_timestamp = max(
            org.cooked_sequester_authority.timestamp,
            max(s.cooked.timestamp for s in org.sequester_services.values()),
        )
        if max_sequester_timestamp >= certif.timestamp:
            return RequireGreaterTimestamp(strictly_greater_than=max_sequester_timestamp)

        # All checks are good, now we do the actual insertion

        org.sequester_services[certif.service_id] = MemorySequesterService(
            cooked=certif,
            sequester_service_certificate=service_certificate,
            service_type=service_type,
            webhook_url=webhook_url,
        )

        await self._event_bus.send(
            EventSequesterCertificate(organization_id=organization_id, timestamp=certif.timestamp)
        )

        return certif

    @override
    async def disable_service(
        self,
        now: DateTime,
        organization_id: OrganizationID,
        service_id: SequesterServiceID,
    ) -> None | SequesterDisableServiceBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return SequesterDisableServiceBadOutcome.ORGANIZATION_NOT_FOUND

        if org.sequester_services is None:
            return SequesterDisableServiceBadOutcome.SEQUESTER_DISABLED

        try:
            service = org.sequester_services[service_id]
        except KeyError:
            return SequesterDisableServiceBadOutcome.SEQUESTER_SERVICE_NOT_FOUND

        if service.disabled_on is not None:
            return SequesterDisableServiceBadOutcome.SEQUESTER_SERVICE_ALREADY_DISABLED

        service.disabled_on = now

    @override
    async def enable_service(
        self, organization_id: OrganizationID, service_id: SequesterServiceID
    ) -> None | SequesterEnableServiceBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return SequesterEnableServiceBadOutcome.ORGANIZATION_NOT_FOUND

        if org.sequester_services is None:
            return SequesterEnableServiceBadOutcome.SEQUESTER_DISABLED

        try:
            service = org.sequester_services[service_id]
        except KeyError:
            return SequesterEnableServiceBadOutcome.SEQUESTER_SERVICE_NOT_FOUND

        if service.disabled_on is None:
            return SequesterEnableServiceBadOutcome.SEQUESTER_SERVICE_ALREADY_ENABLED

        service.disabled_on = None

    @override
    async def get_service(
        self, organization_id: OrganizationID, service_id: SequesterServiceID
    ) -> BaseSequesterService | SequesterGetServiceBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return SequesterGetServiceBadOutcome.ORGANIZATION_NOT_FOUND

        if org.sequester_services is None:
            return SequesterGetServiceBadOutcome.SEQUESTER_DISABLED

        try:
            service = org.sequester_services[service_id]
        except KeyError:
            return SequesterGetServiceBadOutcome.SEQUESTER_SERVICE_NOT_FOUND

        return _cook_service(service)

    @override
    async def get_organization_services(
        self, organization_id: OrganizationID
    ) -> list[BaseSequesterService] | SequesterGetOrganizationServicesBadOutcome:
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return SequesterGetOrganizationServicesBadOutcome.ORGANIZATION_NOT_FOUND

        if org.sequester_services is None:
            return SequesterGetOrganizationServicesBadOutcome.SEQUESTER_DISABLED

        return [_cook_service(service) for service in org.sequester_services.values()]

    @override
    async def dump_realm(
        self,
        organization_id: OrganizationID,
        service_id: SequesterServiceID,
        realm_id: VlobID,
    ) -> list[tuple[VlobID, int, bytes]] | SequesterDumpRealmBadOutcome:
        """
        Dump all vlobs in a given realm.
        This should only be used in tests given it doesn't scale at all !
        """
        try:
            org = self._data.organizations[organization_id]
        except KeyError:
            return SequesterDumpRealmBadOutcome.ORGANIZATION_NOT_FOUND

        if org.sequester_services is None:
            return SequesterDumpRealmBadOutcome.SEQUESTER_DISABLED
        try:
            service = org.sequester_services[service_id]
        except KeyError:
            return SequesterDumpRealmBadOutcome.SEQUESTER_SERVICE_NOT_FOUND

        if service.service_type != SequesterServiceType.STORAGE:
            return SequesterDumpRealmBadOutcome.SEQUESTER_SERVICE_NOT_STORAGE

        dump: list[tuple[VlobID, int, bytes]] = []
        for vlob_atoms in org.vlobs.values():
            if vlob_atoms[0].realm_id != realm_id:
                continue
            for vlob_atom in vlob_atoms:
                assert vlob_atom.blob_for_storage_sequester_services is not None
                sequestered = vlob_atom.blob_for_storage_sequester_services.get(service_id)
                if not sequestered:
                    continue
                dump.append((vlob_atom.vlob_id, vlob_atom.version, sequestered))

        return dump
