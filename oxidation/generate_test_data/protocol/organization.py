# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS


from parsec._parsec import (
    ActiveUsersLimit,
    ArchivingConfigRepNotFound,
    ArchivingConfigRepOk,
    OrganizationBootstrapRepAlreadyBootstrapped,
    OrganizationBootstrapRepBadTimestamp,
    OrganizationBootstrapRepInvalidCertification,
    OrganizationBootstrapRepInvalidData,
    OrganizationBootstrapRepNotFound,
    OrganizationBootstrapRepOk,
    OrganizationConfigRepNotFound,
    OrganizationConfigRepOk,
    OrganizationStatsRepNotAllowed,
    OrganizationStatsRepNotFound,
    OrganizationStatsRepOk,
    RealmArchivingConfiguration,
    RealmArchivingStatus,
    UsersPerProfileDetailItem,
)
from parsec.api.data import *
from parsec.api.protocol import *

from .utils import *

################### OrganizationStats ##################

serializer = organization_stats_serializer

serialized = serializer.req_dumps({"cmd": "organization_stats"})
serializer.req_loads(serialized)
display("organization_stats_req", serialized, [])

serialized = serializer.rep_dumps(
    OrganizationStatsRepOk(
        data_size=8,
        metadata_size=8,
        realms=1,
        users=1,
        active_users=1,
        users_per_profile_detail=[
            UsersPerProfileDetailItem(profile=UserProfile.ADMIN, active=1, revoked=0)
        ],
    )
)
serializer.rep_loads(serialized)
display("organization_stats_rep", serialized, [])

serialized = serializer.rep_dumps(OrganizationStatsRepNotAllowed(reason="foobar"))
serializer.rep_loads(serialized)
display("organization_stats_rep_not_allowed", serialized, [])

serialized = serializer.rep_dumps(OrganizationStatsRepNotFound())
serializer.rep_loads(serialized)
display("organization_stats_rep_not_found", serialized, [])

################### OrganizationConfig ##################

serializer = organization_config_serializer

serialized = serializer.req_dumps({"cmd": "organization_config"})
serializer.req_loads(serialized)
display("organization_config_req", serialized, [])

serialized = serializer.rep_dumps(
    OrganizationConfigRepOk(
        user_profile_outsider_allowed=False,
        active_users_limit=ActiveUsersLimit.NO_LIMIT,
        sequester_authority_certificate=None,
        sequester_services_certificates=None,
        minimum_archiving_period=2592000,
    )
)
serializer.rep_loads(serialized)
display("organization_config_rep_without", serialized, [])

serialized = serializer.rep_dumps(
    OrganizationConfigRepOk(
        user_profile_outsider_allowed=False,
        active_users_limit=ActiveUsersLimit.LimitedTo(1),
        sequester_authority_certificate=b"foobar",
        sequester_services_certificates=[b"foo", b"bar"],
        minimum_archiving_period=2592000,
    )
)
serializer.rep_loads(serialized)
display("organization_config_rep_full", serialized, [])

serialized = serializer.rep_dumps(OrganizationConfigRepNotFound())
serializer.rep_loads(serialized)
display("organization_config_rep_not_found", serialized, [])


################### ArchivingConfig ##################

serializer = archiving_config_serializer

serialized = serializer.req_dumps({"cmd": "archiving_config"})
serializer.req_loads(serialized)
display("archiving_config_req", serialized, [])

serialized = serializer.rep_dumps(ArchivingConfigRepOk(archiving_config=[]))
serializer.rep_loads(serialized)
display("organization_config_rep_ok_empty", serialized, [])

serialized = serializer.rep_dumps(
    ArchivingConfigRepOk(
        archiving_config=[
            RealmArchivingStatus(
                realm_id=RealmID.from_hex("1d3353157d7d4e95ad2fdea7b3bd19c5"),
                configuration=RealmArchivingConfiguration.available(),
                configured_by=None,
                configured_on=None,
            ),
            RealmArchivingStatus(
                realm_id=RealmID.from_hex("2d3353157d7d4e95ad2fdea7b3bd19c6"),
                configuration=RealmArchivingConfiguration.archived(),
                configured_by=DeviceID("alice@dev1"),
                configured_on=DateTime(2000, 1, 2, 1),
            ),
            RealmArchivingStatus(
                realm_id=RealmID.from_hex("3d3353157d7d4e95ad2fdea7b3bd19c7"),
                configuration=RealmArchivingConfiguration.deletion_planned(DateTime(2000, 1, 2, 3)),
                configured_by=DeviceID("bob@dev1"),
                configured_on=DateTime(2000, 1, 2, 2),
            ),
        ]
    )
)
serializer.rep_loads(serialized)
display("organization_config_rep_ok_populated", serialized, [])

serialized = serializer.rep_dumps(ArchivingConfigRepNotFound())
serializer.rep_loads(serialized)
display("organization_config_rep_not_found", serialized, [])


################### OrganizationBootstrap ##################

serializer = organization_bootstrap_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "organization_bootstrap",
        "bootstrap_token": "0db537dee3ff9a3c2f76e337a4461f41fb3d738f35eb48f3759046dfbedb2e79",
        "root_verify_key": ALICE.root_verify_key,
        "user_certificate": USER_CERTIFICATE,
        "device_certificate": DEVICE_CERTIFICATE,
        "redacted_user_certificate": REDACTED_USER_CERTIFICATE,
        "redacted_device_certificate": REDACTED_DEVICE_CERTIFICATE,
    }
)
serializer.req_loads(serialized)
display("organization_bootstrap_req_absent", serialized, [])

serialized = serializer.req_dumps(
    {
        "cmd": "organization_bootstrap",
        "bootstrap_token": "0db537dee3ff9a3c2f76e337a4461f41fb3d738f35eb48f3759046dfbedb2e79",
        "root_verify_key": ALICE.root_verify_key,
        "user_certificate": USER_CERTIFICATE,
        "device_certificate": DEVICE_CERTIFICATE,
        "redacted_user_certificate": REDACTED_USER_CERTIFICATE,
        "redacted_device_certificate": REDACTED_DEVICE_CERTIFICATE,
        "sequester_authority_certificate": None,
    }
)
serializer.req_loads(serialized)
display("organization_bootstrap_req_none", serialized, [])

serialized = serializer.req_dumps(
    {
        "cmd": "organization_bootstrap",
        "bootstrap_token": "0db537dee3ff9a3c2f76e337a4461f41fb3d738f35eb48f3759046dfbedb2e79",
        "root_verify_key": ALICE.root_verify_key,
        "user_certificate": USER_CERTIFICATE,
        "device_certificate": DEVICE_CERTIFICATE,
        "redacted_user_certificate": REDACTED_USER_CERTIFICATE,
        "redacted_device_certificate": REDACTED_DEVICE_CERTIFICATE,
        "sequester_authority_certificate": b"foo",
    }
)
serializer.req_loads(serialized)
display("organization_bootstrap_req_full", serialized, [])

serialized = serializer.rep_dumps(OrganizationBootstrapRepOk())
serializer.rep_loads(serialized)
display("organization_bootstrap_rep_ok", serialized, [])

serialized = serializer.rep_dumps(OrganizationBootstrapRepInvalidCertification("foobar"))
serializer.rep_loads(serialized)
display("organization_bootstrap_rep_invalid_certification", serialized, [])

serialized = serializer.rep_dumps(OrganizationBootstrapRepInvalidData("foobar"))
serializer.rep_loads(serialized)
display("organization_bootstrap_rep_invalid_data", serialized, [])

serialized = serializer.rep_dumps(
    OrganizationBootstrapRepBadTimestamp(
        reason=None,
        ballpark_client_early_offset=300.0,
        ballpark_client_late_offset=320.0,
        backend_timestamp=NOW,
        client_timestamp=NOW,
    )
)
serializer.rep_loads(serialized)
display("organization_bootstrap_rep_bad_timestamp", serialized, [])

serialized = serializer.rep_dumps(OrganizationBootstrapRepAlreadyBootstrapped())
serializer.rep_loads(serialized)
display("organization_bootstrap_rep_already_bootstrapped", serialized, [])

serialized = serializer.rep_dumps(OrganizationBootstrapRepNotFound())
serializer.rep_loads(serialized)
display("organization_bootstrap_rep_not_found", serialized, [])