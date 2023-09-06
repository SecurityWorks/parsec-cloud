# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

from parsec._parsec import (
    DateTime,
    HashDigest,
    InvitationDeletedReason,
    InvitationType,
    Invite1ClaimerWaitPeerRepInvalidState,
    Invite1ClaimerWaitPeerRepNotFound,
    Invite1ClaimerWaitPeerRepOk,
    Invite1GreeterWaitPeerRepAlreadyDeleted,
    Invite1GreeterWaitPeerRepInvalidState,
    Invite1GreeterWaitPeerRepNotFound,
    Invite1GreeterWaitPeerRepOk,
    Invite2aClaimerSendHashedNonceRepAlreadyDeleted,
    Invite2aClaimerSendHashedNonceRepInvalidState,
    Invite2aClaimerSendHashedNonceRepNotFound,
    Invite2aClaimerSendHashedNonceRepOk,
    Invite2aGreeterGetHashedNonceRepAlreadyDeleted,
    Invite2aGreeterGetHashedNonceRepInvalidState,
    Invite2aGreeterGetHashedNonceRepNotFound,
    Invite2aGreeterGetHashedNonceRepOk,
    Invite2bClaimerSendNonceRepInvalidState,
    Invite2bClaimerSendNonceRepNotFound,
    Invite2bClaimerSendNonceRepOk,
    Invite2bGreeterSendNonceRepAlreadyDeleted,
    Invite2bGreeterSendNonceRepInvalidState,
    Invite2bGreeterSendNonceRepNotFound,
    Invite2bGreeterSendNonceRepOk,
    Invite3aClaimerSignifyTrustRepInvalidState,
    Invite3aClaimerSignifyTrustRepNotFound,
    Invite3aClaimerSignifyTrustRepOk,
    Invite3aGreeterWaitPeerTrustRepAlreadyDeleted,
    Invite3aGreeterWaitPeerTrustRepInvalidState,
    Invite3aGreeterWaitPeerTrustRepNotFound,
    Invite3aGreeterWaitPeerTrustRepOk,
    Invite3bClaimerWaitPeerTrustRepInvalidState,
    Invite3bClaimerWaitPeerTrustRepNotFound,
    Invite3bClaimerWaitPeerTrustRepOk,
    Invite3bGreeterSignifyTrustRepAlreadyDeleted,
    Invite3bGreeterSignifyTrustRepInvalidState,
    Invite3bGreeterSignifyTrustRepNotFound,
    Invite3bGreeterSignifyTrustRepOk,
    Invite4ClaimerCommunicateRepInvalidState,
    Invite4ClaimerCommunicateRepNotFound,
    Invite4ClaimerCommunicateRepOk,
    Invite4GreeterCommunicateRepAlreadyDeleted,
    Invite4GreeterCommunicateRepInvalidState,
    Invite4GreeterCommunicateRepNotFound,
    Invite4GreeterCommunicateRepOk,
    InviteDeleteRepAlreadyDeleted,
    InviteDeleteRepNotFound,
    InviteDeleteRepOk,
    InviteInfoRepOk,
    InviteListItem,
    InviteListRepOk,
    InviteNewRepAlreadyMember,
    InviteNewRepNotAllowed,
    InviteNewRepOk,
    InviteNewRepShamirRecoveryNotSetup,
    PublicKey,
    ShamirRecoveryRecipient,
)
from parsec.api.data import *
from parsec.api.protocol import *

from .utils import *

################### InviteNew ##################

serializer = invite_new_serializer

serialized = serializer.req_dumps(
    {
        "type": InvitationType.USER,
        "cmd": "invite_new",
        "claimer_email": "alice@example.com",
        "send_email": True,
    }
)
serializer.req_loads(serialized)
display("invite_new_req_user", serialized, [])

serialized = serializer.req_dumps(
    {
        "type": InvitationType.DEVICE,
        "cmd": "invite_new",
        "send_email": True,
    }
)
serializer.req_loads(serialized)
display("invite_new_req_device", serialized, [])

serialized = serializer.req_dumps(
    {
        "type": InvitationType.SHAMIR_RECOVERY,
        "cmd": "invite_new",
        "send_email": True,
        "claimer_user_id": ALICE.user_id,
    }
)
serializer.req_loads(serialized)
display("invite_new_req_shamir_recovery_device", serialized, [])

serialized = serializer.rep_dumps(
    InviteNewRepOk(
        token=InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
        email_sent=InvitationEmailSentStatus.SUCCESS,
    )
)
serializer.rep_loads(serialized)
display("invite_new_rep_full", serialized, [])

serialized = serializer.rep_dumps(InviteNewRepNotAllowed())
serializer.rep_loads(serialized)
display("invite_new_rep_not_allowed", serialized, [])

serialized = serializer.rep_dumps(InviteNewRepAlreadyMember())
serializer.rep_loads(serialized)
display("invite_new_rep_already_member", serialized, [])

serialized = serializer.rep_dumps(InviteNewRepShamirRecoveryNotSetup())
serializer.rep_loads(serialized)
display("invite_new_rep_not_available", serialized, [])

################### InviteDelete ##################

serializer = invite_delete_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_delete",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
        "reason": InvitationDeletedReason.FINISHED,
    }
)
serializer.req_loads(serialized)
display("invite_delete_req", serialized, [])

serialized = serializer.rep_dumps(InviteDeleteRepOk())
serializer.rep_loads(serialized)
display("invite_delete_rep", serialized, [])

serialized = serializer.rep_dumps(InviteDeleteRepNotFound())
serializer.rep_loads(serialized)
display("invite_delete_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(InviteDeleteRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_delete_rep_already_deleted", serialized, [])

################### InviteList ##################

serializer = invite_list_serializer

serialized = serializer.req_dumps({"cmd": "invite_list"})
serializer.req_loads(serialized)
display("invite_list_req", serialized, [])

serialized = serializer.rep_dumps(
    InviteListRepOk(
        invitations=[
            InviteListItem.User(
                token=InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
                created_on=DateTime(2000, 1, 2, 1),
                claimer_email="alice@example.com",
                status=InvitationStatus.IDLE,
            ),
            InviteListItem.Device(
                token=InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
                created_on=DateTime(2000, 1, 2, 1),
                status=InvitationStatus.IDLE,
            ),
            InviteListItem.ShamirRecovery(
                token=InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
                created_on=DateTime(2000, 1, 2, 1),
                claimer_user_id=UserID("109b68ba5cdf428ea0017fc6bcc04d4a"),
                status=InvitationStatus.IDLE,
            ),
        ]
    )
)
serializer.rep_loads(serialized)
display("invite_list_rep", serialized, [])

################### InviteInfo ##################

serializer = invite_info_serializer

serialized = serializer.req_dumps({"cmd": "invite_info"})
serializer.req_loads(serialized)
display("invite_info_req", serialized, [])

serialized = serializer.rep_dumps(
    InviteInfoRepOk(
        type=InvitationType.USER,
        claimer_email="alice@example.com",
        greeter_user_id=UserID("109b68ba5cdf428ea0017fc6bcc04d4a"),
        greeter_human_handle=HumanHandle("bob@example.com", "bob"),
    )
)
serializer.rep_loads(serialized)
display("invite_info_rep_user", serialized, [])

serialized = serializer.rep_dumps(
    InviteInfoRepOk(
        type=InvitationType.DEVICE,
        greeter_user_id=UserID("109b68ba5cdf428ea0017fc6bcc04d4a"),
        greeter_human_handle=HumanHandle("bob@example.com", "bob"),
        claimer_email=None,
    )
)
serializer.rep_loads(serialized)
display("invite_info_rep_device", serialized, [])

serialized = serializer.rep_dumps(
    InviteInfoRepOk(
        type=InvitationType.USER,
        claimer_email="alice@example.com",
        greeter_user_id=UserID("109b68ba5cdf428ea0017fc6bcc04d4a"),
        greeter_human_handle=None,
    )
)
serializer.rep_loads(serialized)
display("invite_info_rep_user no handle", serialized, [])

serialized = serializer.rep_dumps(
    InviteInfoRepOk(
        type=InvitationType.DEVICE,
        greeter_user_id=UserID("109b68ba5cdf428ea0017fc6bcc04d4a"),
        greeter_human_handle=None,
        claimer_email=None,
    )
)
serializer.rep_loads(serialized)
display("invite_info_rep_device no handle", serialized, [])

serialized = serializer.rep_dumps(
    InviteInfoRepOk(
        type=InvitationType.SHAMIR_RECOVERY,
        threshold=1,
        recipients=[],
    )
)
serializer.rep_loads(serialized)
display("invite_info_rep_shamir_recovery without recipients", serialized, [])

serialized = serializer.rep_dumps(
    InviteInfoRepOk(
        type=InvitationType.SHAMIR_RECOVERY,
        threshold=1,
        recipients=[ShamirRecoveryRecipient(ALICE.user_id, ALICE.human_handle, 1)],
    )
)
serializer.rep_loads(serialized)
display("invite_info_rep_shamir_recovery with recipients", serialized, [])

################### Invite1ClaimerWaitPeer ##################

serializer = invite_1_claimer_wait_peer_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_1_claimer_wait_peer",
        "greeter_user_id": ALICE.user_id,
        "claimer_public_key": PublicKey(
            unhexlify("6507907d33bae6b5980b32fa03f3ebac56141b126e44f352ea46c5f22cd5ac57")
        ),
    }
)
serializer.req_loads(serialized)
display("invite_1_claimer_wait_peer_req", serialized, [])

serialized = serializer.rep_dumps(
    Invite1ClaimerWaitPeerRepOk(
        greeter_public_key=PublicKey(
            unhexlify("6507907d33bae6b5980b32fa03f3ebac56141b126e44f352ea46c5f22cd5ac57")
        )
    )
)
serializer.rep_loads(serialized)
display("invite_1_claimer_wait_peer_rep", serialized, [])

serialized = serializer.rep_dumps(Invite1ClaimerWaitPeerRepNotFound())
serializer.rep_loads(serialized)
display("invite_1_claimer_wait_peer_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite1ClaimerWaitPeerRepInvalidState())
serializer.rep_loads(serialized)
display("invite_1_claimer_wait_peer_rep_invalid_state", serialized, [])

################### Invite1GreeterWaitPeer ##################

serializer = invite_1_greeter_wait_peer_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_1_greeter_wait_peer",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
        "greeter_public_key": PublicKey(
            unhexlify("6507907d33bae6b5980b32fa03f3ebac56141b126e44f352ea46c5f22cd5ac57")
        ),
    }
)
serializer.req_loads(serialized)
display("invite_1_greeter_wait_peer_req", serialized, [])

serialized = serializer.rep_dumps(
    Invite1GreeterWaitPeerRepOk(
        claimer_public_key=PublicKey(
            unhexlify("6507907d33bae6b5980b32fa03f3ebac56141b126e44f352ea46c5f22cd5ac57")
        )
    )
)
serializer.rep_loads(serialized)
display("invite_1_greeter_wait_peer_rep", serialized, [])

serialized = serializer.rep_dumps(Invite1GreeterWaitPeerRepNotFound())
serializer.rep_loads(serialized)
display("invite_1_greeter_wait_peer_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite1GreeterWaitPeerRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_1_greeter_wait_peer_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite1GreeterWaitPeerRepInvalidState())
serializer.rep_loads(serialized)
display("invite_1_greeter_wait_peer_rep_invalid_state", serialized, [])

################### Invite2aClaimerSendHashedNonce ##################

serializer = invite_2a_claimer_send_hashed_nonce_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_2a_claimer_send_hashed_nonce",
        "greeter_user_id": ALICE.user_id,
        "claimer_hashed_nonce": HashDigest(
            unhexlify("e37ce3b00a1f15b3de62029972345420b76313a885c6ccc6e3b5547857b3ecc6")
        ),
    }
)
serializer.req_loads(serialized)
display("invite_2a_claimer_send_hashed_nonce_req", serialized, [])

serialized = serializer.rep_dumps(Invite2aClaimerSendHashedNonceRepOk(greeter_nonce=b"foobar"))
serializer.rep_loads(serialized)
display("invite_2a_claimer_send_hashed_nonce_rep", serialized, [])

serialized = serializer.rep_dumps(Invite2aClaimerSendHashedNonceRepNotFound())
serializer.rep_loads(serialized)
display("invite_2a_claimer_send_hashed_nonce_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite2aClaimerSendHashedNonceRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_2a_claimer_send_hashed_nonce_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite2aClaimerSendHashedNonceRepInvalidState())
serializer.rep_loads(serialized)
display("invite_2a_claimer_send_hashed_nonce_rep_invalid_state", serialized, [])

################### Invite2aGreeterGetHashedNonce ##################

serializer = invite_2a_greeter_get_hashed_nonce_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_2a_greeter_get_hashed_nonce",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
    }
)
serializer.req_loads(serialized)
display("invite_2a_greeter_get_hashed_nonce_req", serialized, [])

serialized = serializer.rep_dumps(
    Invite2aGreeterGetHashedNonceRepOk(
        claimer_hashed_nonce=HashDigest(
            unhexlify("e37ce3b00a1f15b3de62029972345420b76313a885c6ccc6e3b5547857b3ecc6")
        )
    )
)
serializer.rep_loads(serialized)
display("invite_2a_greeter_get_hashed_nonce_rep", serialized, [])

serialized = serializer.rep_dumps(Invite2aGreeterGetHashedNonceRepNotFound())
serializer.rep_loads(serialized)
display("invite_2a_greeter_get_hashed_nonce_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite2aGreeterGetHashedNonceRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_2a_greeter_get_hashed_nonce_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite2aGreeterGetHashedNonceRepInvalidState())
serializer.rep_loads(serialized)
display("invite_2a_greeter_get_hashed_nonce_rep_invalid_state", serialized, [])

################### Invite2bGreeterSendNonce ##################

serializer = invite_2b_greeter_send_nonce_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_2b_greeter_send_nonce",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
        "greeter_nonce": b"foobar",
    }
)
serializer.req_loads(serialized)
display("invite_2b_greeter_send_nonce_req", serialized, [])

serialized = serializer.rep_dumps(Invite2bGreeterSendNonceRepOk(claimer_nonce=b"foobar"))
serializer.rep_loads(serialized)
display("invite_2b_greeter_send_nonce_rep", serialized, [])

serialized = serializer.rep_dumps(Invite2bGreeterSendNonceRepNotFound())
serializer.rep_loads(serialized)
display("invite_2b_greeter_send_nonce_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite2bGreeterSendNonceRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_2b_greeter_send_nonce_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite2bGreeterSendNonceRepInvalidState())
serializer.rep_loads(serialized)
display("invite_2b_greeter_send_nonce_rep_invalid_state", serialized, [])

################## Invite2bClaimerSendNonce ##################

serializer = invite_2b_claimer_send_nonce_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_2b_claimer_send_nonce",
        "greeter_user_id": ALICE.user_id,
        "claimer_nonce": b"foobar",
    }
)
serializer.req_loads(serialized)
display("invite_2b_claimer_send_nonce_req", serialized, [])

serialized = serializer.rep_dumps(Invite2bClaimerSendNonceRepOk())
serializer.rep_loads(serialized)
display("invite_2b_claimer_send_nonce_rep", serialized, [])

serialized = serializer.rep_dumps(Invite2bClaimerSendNonceRepNotFound())
serializer.rep_loads(serialized)
display("invite_2b_claimer_send_nonce_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite2bClaimerSendNonceRepInvalidState())
serializer.rep_loads(serialized)
display("invite_2b_claimer_send_nonce_rep_invalid_state", serialized, [])

################### Invite3aGreeterWaitPeerTrust ##################

serializer = invite_3a_greeter_wait_peer_trust_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_3a_greeter_wait_peer_trust",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
    }
)
serializer.req_loads(serialized)
display("invite_3a_greeter_wait_peer_trust_req", serialized, [])

serialized = serializer.rep_dumps(Invite3aGreeterWaitPeerTrustRepOk())
serializer.rep_loads(serialized)
display("invite_3a_greeter_wait_peer_trust_rep", serialized, [])

serialized = serializer.rep_dumps(Invite3aGreeterWaitPeerTrustRepNotFound())
serializer.rep_loads(serialized)
display("invite_3a_greeter_wait_peer_trust_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite3aGreeterWaitPeerTrustRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_3a_greeter_wait_peer_trust_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite3aGreeterWaitPeerTrustRepInvalidState())
serializer.rep_loads(serialized)
display("invite_3a_greeter_wait_peer_trust_rep_invalid_state", serialized, [])

################### Invite3bClaimerWaitPeerTrust ##################

serializer = invite_3b_claimer_wait_peer_trust_serializer

serialized = serializer.req_dumps(
    {"cmd": "invite_3b_claimer_wait_peer_trust", "greeter_user_id": ALICE.user_id}
)
serializer.req_loads(serialized)
display("invite_3b_claimer_wait_peer_trust_req", serialized, [])

serialized = serializer.rep_dumps(Invite3bClaimerWaitPeerTrustRepOk())
serializer.rep_loads(serialized)
display("invite_3b_claimer_wait_peer_trust_rep", serialized, [])

serialized = serializer.rep_dumps(Invite3bClaimerWaitPeerTrustRepNotFound())
serializer.rep_loads(serialized)
display("invite_3b_claimer_wait_peer_trust_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite3bClaimerWaitPeerTrustRepInvalidState())
serializer.rep_loads(serialized)
display("invite_3b_claimer_wait_peer_trust_rep_invalid_state", serialized, [])

################### Invite3bGreeterSignifyTrust ##################

serializer = invite_3b_greeter_signify_trust_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_3b_greeter_signify_trust",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
    }
)
serializer.req_loads(serialized)
display("invite_3b_greeter_signify_trust_req", serialized, [])

serialized = serializer.rep_dumps(Invite3bGreeterSignifyTrustRepOk())
serializer.rep_loads(serialized)
display("invite_3b_greeter_signify_trust_rep", serialized, [])

serialized = serializer.rep_dumps(Invite3bGreeterSignifyTrustRepNotFound())
serializer.rep_loads(serialized)
display("invite_3b_greeter_signify_trust_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite3bGreeterSignifyTrustRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_3b_greeter_signify_trust_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite3bGreeterSignifyTrustRepInvalidState())
serializer.rep_loads(serialized)
display("invite_3b_greeter_signify_trust_rep_invalid_state", serialized, [])

################### Invite3aClaimerSignifyTrust ##################

serializer = invite_3a_claimer_signify_trust_serializer

serialized = serializer.req_dumps(
    {"cmd": "invite_3a_claimer_signify_trust", "greeter_user_id": ALICE.user_id}
)
serializer.req_loads(serialized)
display("invite_3a_claimer_signify_trust_req", serialized, [])

serialized = serializer.rep_dumps(Invite3aClaimerSignifyTrustRepOk())
serializer.rep_loads(serialized)
display("invite_3a_claimer_signify_trust_rep", serialized, [])

serialized = serializer.rep_dumps(Invite3aClaimerSignifyTrustRepNotFound())
serializer.rep_loads(serialized)
display("invite_3a_claimer_signify_trust_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite3aClaimerSignifyTrustRepInvalidState())
serializer.rep_loads(serialized)
display("invite_3a_claimer_signify_trust_rep_invalid_state", serialized, [])

################### Invite4GreeterCommunicate ##################

serializer = invite_4_greeter_communicate_serializer

serialized = serializer.req_dumps(
    {
        "cmd": "invite_4_greeter_communicate",
        "token": InvitationToken.from_hex("d864b93ded264aae9ae583fd3d40c45a"),
        "payload": b"foobar",
    }
)
serializer.req_loads(serialized)
display("invite_4_greeter_communicate_req", serialized, [])

serialized = serializer.rep_dumps(Invite4GreeterCommunicateRepOk(payload=b"foobar"))
serializer.rep_loads(serialized)
display("invite_4_greeter_communicate_rep", serialized, [])

serialized = serializer.rep_dumps(Invite4GreeterCommunicateRepNotFound())
serializer.rep_loads(serialized)
display("invite_4_greeter_communicate_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite4GreeterCommunicateRepAlreadyDeleted())
serializer.rep_loads(serialized)
display("invite_4_greeter_communicate_rep_already_deleted", serialized, [])

serialized = serializer.rep_dumps(Invite4GreeterCommunicateRepInvalidState())
serializer.rep_loads(serialized)
display("invite_4_greeter_communicate_rep_invalid_state", serialized, [])

################### Invite4ClaimerCommunicate ##################

serializer = invite_4_claimer_communicate_serializer

serialized = serializer.req_dumps(
    {"cmd": "invite_4_claimer_communicate", "greeter_user_id": ALICE.user_id, "payload": b"foobar"}
)
serializer.req_loads(serialized)
display("invite_4_claimer_communicate_req", serialized, [])

serialized = serializer.rep_dumps(Invite4ClaimerCommunicateRepOk(payload=b"foobar"))
serializer.rep_loads(serialized)
display("invite_4_claimer_communicate_rep", serialized, [])

serialized = serializer.rep_dumps(Invite4ClaimerCommunicateRepNotFound())
serializer.rep_loads(serialized)
display("invite_4_claimer_communicate_rep_not_found", serialized, [])

serialized = serializer.rep_dumps(Invite4ClaimerCommunicateRepInvalidState())
serializer.rep_loads(serialized)
display("invite_4_claimer_communicate_rep_invalid_state", serialized, [])