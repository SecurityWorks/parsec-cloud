// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

/*
 * /!\ Auto-generated code (see `bindings/generator`), any modification will be lost ! /!\
 */


export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E }

export enum CancelledGreetingAttemptReason {
    AutomaticallyCancelled = 'CancelledGreetingAttemptReasonAutomaticallyCancelled',
    InconsistentPayload = 'CancelledGreetingAttemptReasonInconsistentPayload',
    InvalidNonceHash = 'CancelledGreetingAttemptReasonInvalidNonceHash',
    InvalidSasCode = 'CancelledGreetingAttemptReasonInvalidSasCode',
    ManuallyCancelled = 'CancelledGreetingAttemptReasonManuallyCancelled',
    UndecipherablePayload = 'CancelledGreetingAttemptReasonUndecipherablePayload',
    UndeserializablePayload = 'CancelledGreetingAttemptReasonUndeserializablePayload',
}

export enum DeviceFileType {
    Keyring = 'DeviceFileTypeKeyring',
    Password = 'DeviceFileTypePassword',
    Recovery = 'DeviceFileTypeRecovery',
    Smartcard = 'DeviceFileTypeSmartcard',
}

export enum GreeterOrClaimer {
    Claimer = 'GreeterOrClaimerClaimer',
    Greeter = 'GreeterOrClaimerGreeter',
}

export enum InvitationEmailSentStatus {
    RecipientRefused = 'InvitationEmailSentStatusRecipientRefused',
    ServerUnavailable = 'InvitationEmailSentStatusServerUnavailable',
    Success = 'InvitationEmailSentStatusSuccess',
}

export enum InvitationStatus {
    Cancelled = 'InvitationStatusCancelled',
    Finished = 'InvitationStatusFinished',
    Idle = 'InvitationStatusIdle',
    Ready = 'InvitationStatusReady',
}

export enum Platform {
    Android = 'PlatformAndroid',
    Linux = 'PlatformLinux',
    MacOS = 'PlatformMacOS',
    Web = 'PlatformWeb',
    Windows = 'PlatformWindows',
}

export enum RealmRole {
    Contributor = 'RealmRoleContributor',
    Manager = 'RealmRoleManager',
    Owner = 'RealmRoleOwner',
    Reader = 'RealmRoleReader',
}

export enum UserProfile {
    Admin = 'UserProfileAdmin',
    Outsider = 'UserProfileOutsider',
    Standard = 'UserProfileStandard',
}


export interface AvailableDevice {
    keyFilePath: string
    createdOn: number
    protectedOn: number
    serverUrl: string
    organizationId: string
    userId: string
    deviceId: string
    humanHandle: HumanHandle
    deviceLabel: string
    ty: DeviceFileType
}


export interface ClientConfig {
    configDir: string
    dataBaseDir: string
    mountpointMountStrategy: MountpointMountStrategy
    workspaceStorageCacheSize: WorkspaceStorageCacheSize
    withMonitors: boolean
    preventSyncPattern: string | null
}


export interface ClientInfo {
    organizationAddr: string
    organizationId: string
    deviceId: string
    userId: string
    deviceLabel: string
    humanHandle: HumanHandle
    currentProfile: UserProfile
    serverConfig: ServerConfig
}


export interface DeviceClaimFinalizeInfo {
    handle: number
}


export interface DeviceClaimInProgress1Info {
    handle: number
    greeterSas: string
    greeterSasChoices: Array<string>
}


export interface DeviceClaimInProgress2Info {
    handle: number
    claimerSas: string
}


export interface DeviceClaimInProgress3Info {
    handle: number
}


export interface DeviceGreetInProgress1Info {
    handle: number
    greeterSas: string
}


export interface DeviceGreetInProgress2Info {
    handle: number
    claimerSas: string
    claimerSasChoices: Array<string>
}


export interface DeviceGreetInProgress3Info {
    handle: number
}


export interface DeviceGreetInProgress4Info {
    handle: number
    requestedDeviceLabel: string
}


export interface DeviceGreetInitialInfo {
    handle: number
}


export interface DeviceInfo {
    id: string
    deviceLabel: string
    createdOn: number
    createdBy: string | null
}


export interface FileStat {
    id: string
    created: number
    updated: number
    baseVersion: number
    isPlaceholder: boolean
    needSync: boolean
    size: number
}


export interface HumanHandle {
    email: string
    label: string
}


export interface NewInvitationInfo {
    addr: string
    token: string
    emailSentStatus: InvitationEmailSentStatus
}


export interface OpenOptions {
    read: boolean
    write: boolean
    truncate: boolean
    create: boolean
    createNew: boolean
}


export interface ServerConfig {
    userProfileOutsiderAllowed: boolean
    activeUsersLimit: ActiveUsersLimit
}


export interface StartedWorkspaceInfo {
    client: number
    id: string
    currentName: string
    currentSelfRole: RealmRole
    mountpoints: Array<[number, string]>
}


export interface Tos {
    perLocaleUrls: Map<string, string>
    updatedOn: number
}


export interface UserClaimFinalizeInfo {
    handle: number
}


export interface UserClaimInProgress1Info {
    handle: number
    greeterSas: string
    greeterSasChoices: Array<string>
}


export interface UserClaimInProgress2Info {
    handle: number
    claimerSas: string
}


export interface UserClaimInProgress3Info {
    handle: number
}


export interface UserGreetInProgress1Info {
    handle: number
    greeterSas: string
}


export interface UserGreetInProgress2Info {
    handle: number
    claimerSas: string
    claimerSasChoices: Array<string>
}


export interface UserGreetInProgress3Info {
    handle: number
}


export interface UserGreetInProgress4Info {
    handle: number
    requestedHumanHandle: HumanHandle
    requestedDeviceLabel: string
}


export interface UserGreetInitialInfo {
    handle: number
}


export interface UserInfo {
    id: string
    humanHandle: HumanHandle
    currentProfile: UserProfile
    createdOn: number
    createdBy: string | null
    revokedOn: number | null
    revokedBy: string | null
}


export interface WorkspaceInfo {
    id: string
    currentName: string
    currentSelfRole: RealmRole
    isStarted: boolean
    isBootstrapped: boolean
}


export interface WorkspaceUserAccessInfo {
    userId: string
    humanHandle: HumanHandle
    currentProfile: UserProfile
    currentRole: RealmRole
}


// ActiveUsersLimit
export interface ActiveUsersLimitLimitedTo {
    tag: "LimitedTo"
    x1: number
}
export interface ActiveUsersLimitNoLimit {
    tag: "NoLimit"
}
export type ActiveUsersLimit =
  | ActiveUsersLimitLimitedTo
  | ActiveUsersLimitNoLimit


// ArchiveDeviceError
export interface ArchiveDeviceErrorInternal {
    tag: "Internal"
    error: string
}
export type ArchiveDeviceError =
  | ArchiveDeviceErrorInternal


// BootstrapOrganizationError
export interface BootstrapOrganizationErrorAlreadyUsedToken {
    tag: "AlreadyUsedToken"
    error: string
}
export interface BootstrapOrganizationErrorInternal {
    tag: "Internal"
    error: string
}
export interface BootstrapOrganizationErrorInvalidToken {
    tag: "InvalidToken"
    error: string
}
export interface BootstrapOrganizationErrorOffline {
    tag: "Offline"
    error: string
}
export interface BootstrapOrganizationErrorOrganizationExpired {
    tag: "OrganizationExpired"
    error: string
}
export interface BootstrapOrganizationErrorSaveDeviceError {
    tag: "SaveDeviceError"
    error: string
}
export interface BootstrapOrganizationErrorTimestampOutOfBallpark {
    tag: "TimestampOutOfBallpark"
    error: string
    server_timestamp: number
    client_timestamp: number
    ballpark_client_early_offset: number
    ballpark_client_late_offset: number
}
export type BootstrapOrganizationError =
  | BootstrapOrganizationErrorAlreadyUsedToken
  | BootstrapOrganizationErrorInternal
  | BootstrapOrganizationErrorInvalidToken
  | BootstrapOrganizationErrorOffline
  | BootstrapOrganizationErrorOrganizationExpired
  | BootstrapOrganizationErrorSaveDeviceError
  | BootstrapOrganizationErrorTimestampOutOfBallpark


// CancelError
export interface CancelErrorInternal {
    tag: "Internal"
    error: string
}
export interface CancelErrorNotBound {
    tag: "NotBound"
    error: string
}
export type CancelError =
  | CancelErrorInternal
  | CancelErrorNotBound


// ClaimInProgressError
export interface ClaimInProgressErrorActiveUsersLimitReached {
    tag: "ActiveUsersLimitReached"
    error: string
}
export interface ClaimInProgressErrorAlreadyUsed {
    tag: "AlreadyUsed"
    error: string
}
export interface ClaimInProgressErrorCancelled {
    tag: "Cancelled"
    error: string
}
export interface ClaimInProgressErrorCorruptedConfirmation {
    tag: "CorruptedConfirmation"
    error: string
}
export interface ClaimInProgressErrorGreeterNotAllowed {
    tag: "GreeterNotAllowed"
    error: string
}
export interface ClaimInProgressErrorGreetingAttemptCancelled {
    tag: "GreetingAttemptCancelled"
    error: string
    origin: GreeterOrClaimer
    reason: CancelledGreetingAttemptReason
    timestamp: number
}
export interface ClaimInProgressErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClaimInProgressErrorNotFound {
    tag: "NotFound"
    error: string
}
export interface ClaimInProgressErrorOffline {
    tag: "Offline"
    error: string
}
export interface ClaimInProgressErrorOrganizationExpired {
    tag: "OrganizationExpired"
    error: string
}
export interface ClaimInProgressErrorPeerReset {
    tag: "PeerReset"
    error: string
}
export type ClaimInProgressError =
  | ClaimInProgressErrorActiveUsersLimitReached
  | ClaimInProgressErrorAlreadyUsed
  | ClaimInProgressErrorCancelled
  | ClaimInProgressErrorCorruptedConfirmation
  | ClaimInProgressErrorGreeterNotAllowed
  | ClaimInProgressErrorGreetingAttemptCancelled
  | ClaimInProgressErrorInternal
  | ClaimInProgressErrorNotFound
  | ClaimInProgressErrorOffline
  | ClaimInProgressErrorOrganizationExpired
  | ClaimInProgressErrorPeerReset


// ClaimerGreeterAbortOperationError
export interface ClaimerGreeterAbortOperationErrorInternal {
    tag: "Internal"
    error: string
}
export type ClaimerGreeterAbortOperationError =
  | ClaimerGreeterAbortOperationErrorInternal


// ClaimerRetrieveInfoError
export interface ClaimerRetrieveInfoErrorAlreadyUsed {
    tag: "AlreadyUsed"
    error: string
}
export interface ClaimerRetrieveInfoErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClaimerRetrieveInfoErrorNotFound {
    tag: "NotFound"
    error: string
}
export interface ClaimerRetrieveInfoErrorOffline {
    tag: "Offline"
    error: string
}
export type ClaimerRetrieveInfoError =
  | ClaimerRetrieveInfoErrorAlreadyUsed
  | ClaimerRetrieveInfoErrorInternal
  | ClaimerRetrieveInfoErrorNotFound
  | ClaimerRetrieveInfoErrorOffline


// ClientAcceptTosError
export interface ClientAcceptTosErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientAcceptTosErrorNoTos {
    tag: "NoTos"
    error: string
}
export interface ClientAcceptTosErrorOffline {
    tag: "Offline"
    error: string
}
export interface ClientAcceptTosErrorTosMismatch {
    tag: "TosMismatch"
    error: string
}
export type ClientAcceptTosError =
  | ClientAcceptTosErrorInternal
  | ClientAcceptTosErrorNoTos
  | ClientAcceptTosErrorOffline
  | ClientAcceptTosErrorTosMismatch


// ClientCancelInvitationError
export interface ClientCancelInvitationErrorAlreadyDeleted {
    tag: "AlreadyDeleted"
    error: string
}
export interface ClientCancelInvitationErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientCancelInvitationErrorNotFound {
    tag: "NotFound"
    error: string
}
export interface ClientCancelInvitationErrorOffline {
    tag: "Offline"
    error: string
}
export type ClientCancelInvitationError =
  | ClientCancelInvitationErrorAlreadyDeleted
  | ClientCancelInvitationErrorInternal
  | ClientCancelInvitationErrorNotFound
  | ClientCancelInvitationErrorOffline


// ClientChangeAuthenticationError
export interface ClientChangeAuthenticationErrorDecryptionFailed {
    tag: "DecryptionFailed"
    error: string
}
export interface ClientChangeAuthenticationErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientChangeAuthenticationErrorInvalidData {
    tag: "InvalidData"
    error: string
}
export interface ClientChangeAuthenticationErrorInvalidPath {
    tag: "InvalidPath"
    error: string
}
export type ClientChangeAuthenticationError =
  | ClientChangeAuthenticationErrorDecryptionFailed
  | ClientChangeAuthenticationErrorInternal
  | ClientChangeAuthenticationErrorInvalidData
  | ClientChangeAuthenticationErrorInvalidPath


// ClientCreateWorkspaceError
export interface ClientCreateWorkspaceErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientCreateWorkspaceErrorStopped {
    tag: "Stopped"
    error: string
}
export type ClientCreateWorkspaceError =
  | ClientCreateWorkspaceErrorInternal
  | ClientCreateWorkspaceErrorStopped


// ClientEvent
export interface ClientEventExpiredOrganization {
    tag: "ExpiredOrganization"
}
export interface ClientEventIncompatibleServer {
    tag: "IncompatibleServer"
    detail: string
}
export interface ClientEventInvitationChanged {
    tag: "InvitationChanged"
    token: string
    status: InvitationStatus
}
export interface ClientEventMustAcceptTos {
    tag: "MustAcceptTos"
}
export interface ClientEventOffline {
    tag: "Offline"
}
export interface ClientEventOnline {
    tag: "Online"
}
export interface ClientEventPing {
    tag: "Ping"
    ping: string
}
export interface ClientEventRevokedSelfUser {
    tag: "RevokedSelfUser"
}
export interface ClientEventServerConfigChanged {
    tag: "ServerConfigChanged"
}
export interface ClientEventTooMuchDriftWithServerClock {
    tag: "TooMuchDriftWithServerClock"
    server_timestamp: number
    client_timestamp: number
    ballpark_client_early_offset: number
    ballpark_client_late_offset: number
}
export interface ClientEventWorkspaceLocallyCreated {
    tag: "WorkspaceLocallyCreated"
}
export interface ClientEventWorkspaceOpsInboundSyncDone {
    tag: "WorkspaceOpsInboundSyncDone"
    realm_id: string
    entry_id: string
}
export interface ClientEventWorkspaceOpsOutboundSyncAborted {
    tag: "WorkspaceOpsOutboundSyncAborted"
    realm_id: string
    entry_id: string
}
export interface ClientEventWorkspaceOpsOutboundSyncDone {
    tag: "WorkspaceOpsOutboundSyncDone"
    realm_id: string
    entry_id: string
}
export interface ClientEventWorkspaceOpsOutboundSyncProgress {
    tag: "WorkspaceOpsOutboundSyncProgress"
    realm_id: string
    entry_id: string
    blocks: number
    block_index: number
    blocksize: number
}
export interface ClientEventWorkspaceOpsOutboundSyncStarted {
    tag: "WorkspaceOpsOutboundSyncStarted"
    realm_id: string
    entry_id: string
}
export interface ClientEventWorkspaceWatchedEntryChanged {
    tag: "WorkspaceWatchedEntryChanged"
    realm_id: string
    entry_id: string
}
export interface ClientEventWorkspacesSelfListChanged {
    tag: "WorkspacesSelfListChanged"
}
export type ClientEvent =
  | ClientEventExpiredOrganization
  | ClientEventIncompatibleServer
  | ClientEventInvitationChanged
  | ClientEventMustAcceptTos
  | ClientEventOffline
  | ClientEventOnline
  | ClientEventPing
  | ClientEventRevokedSelfUser
  | ClientEventServerConfigChanged
  | ClientEventTooMuchDriftWithServerClock
  | ClientEventWorkspaceLocallyCreated
  | ClientEventWorkspaceOpsInboundSyncDone
  | ClientEventWorkspaceOpsOutboundSyncAborted
  | ClientEventWorkspaceOpsOutboundSyncDone
  | ClientEventWorkspaceOpsOutboundSyncProgress
  | ClientEventWorkspaceOpsOutboundSyncStarted
  | ClientEventWorkspaceWatchedEntryChanged
  | ClientEventWorkspacesSelfListChanged


// ClientGetTosError
export interface ClientGetTosErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientGetTosErrorNoTos {
    tag: "NoTos"
    error: string
}
export interface ClientGetTosErrorOffline {
    tag: "Offline"
    error: string
}
export type ClientGetTosError =
  | ClientGetTosErrorInternal
  | ClientGetTosErrorNoTos
  | ClientGetTosErrorOffline


// ClientGetUserDeviceError
export interface ClientGetUserDeviceErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientGetUserDeviceErrorNonExisting {
    tag: "NonExisting"
    error: string
}
export interface ClientGetUserDeviceErrorStopped {
    tag: "Stopped"
    error: string
}
export type ClientGetUserDeviceError =
  | ClientGetUserDeviceErrorInternal
  | ClientGetUserDeviceErrorNonExisting
  | ClientGetUserDeviceErrorStopped


// ClientInfoError
export interface ClientInfoErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientInfoErrorStopped {
    tag: "Stopped"
    error: string
}
export type ClientInfoError =
  | ClientInfoErrorInternal
  | ClientInfoErrorStopped


// ClientListUserDevicesError
export interface ClientListUserDevicesErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientListUserDevicesErrorStopped {
    tag: "Stopped"
    error: string
}
export type ClientListUserDevicesError =
  | ClientListUserDevicesErrorInternal
  | ClientListUserDevicesErrorStopped


// ClientListUsersError
export interface ClientListUsersErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientListUsersErrorStopped {
    tag: "Stopped"
    error: string
}
export type ClientListUsersError =
  | ClientListUsersErrorInternal
  | ClientListUsersErrorStopped


// ClientListWorkspaceUsersError
export interface ClientListWorkspaceUsersErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientListWorkspaceUsersErrorStopped {
    tag: "Stopped"
    error: string
}
export type ClientListWorkspaceUsersError =
  | ClientListWorkspaceUsersErrorInternal
  | ClientListWorkspaceUsersErrorStopped


// ClientListWorkspacesError
export interface ClientListWorkspacesErrorInternal {
    tag: "Internal"
    error: string
}
export type ClientListWorkspacesError =
  | ClientListWorkspacesErrorInternal


// ClientNewDeviceInvitationError
export interface ClientNewDeviceInvitationErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientNewDeviceInvitationErrorOffline {
    tag: "Offline"
    error: string
}
export type ClientNewDeviceInvitationError =
  | ClientNewDeviceInvitationErrorInternal
  | ClientNewDeviceInvitationErrorOffline


// ClientNewUserInvitationError
export interface ClientNewUserInvitationErrorAlreadyMember {
    tag: "AlreadyMember"
    error: string
}
export interface ClientNewUserInvitationErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientNewUserInvitationErrorNotAllowed {
    tag: "NotAllowed"
    error: string
}
export interface ClientNewUserInvitationErrorOffline {
    tag: "Offline"
    error: string
}
export type ClientNewUserInvitationError =
  | ClientNewUserInvitationErrorAlreadyMember
  | ClientNewUserInvitationErrorInternal
  | ClientNewUserInvitationErrorNotAllowed
  | ClientNewUserInvitationErrorOffline


// ClientRenameWorkspaceError
export interface ClientRenameWorkspaceErrorAuthorNotAllowed {
    tag: "AuthorNotAllowed"
    error: string
}
export interface ClientRenameWorkspaceErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientRenameWorkspaceErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface ClientRenameWorkspaceErrorInvalidEncryptedRealmName {
    tag: "InvalidEncryptedRealmName"
    error: string
}
export interface ClientRenameWorkspaceErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface ClientRenameWorkspaceErrorNoKey {
    tag: "NoKey"
    error: string
}
export interface ClientRenameWorkspaceErrorOffline {
    tag: "Offline"
    error: string
}
export interface ClientRenameWorkspaceErrorStopped {
    tag: "Stopped"
    error: string
}
export interface ClientRenameWorkspaceErrorTimestampOutOfBallpark {
    tag: "TimestampOutOfBallpark"
    error: string
    server_timestamp: number
    client_timestamp: number
    ballpark_client_early_offset: number
    ballpark_client_late_offset: number
}
export interface ClientRenameWorkspaceErrorWorkspaceNotFound {
    tag: "WorkspaceNotFound"
    error: string
}
export type ClientRenameWorkspaceError =
  | ClientRenameWorkspaceErrorAuthorNotAllowed
  | ClientRenameWorkspaceErrorInternal
  | ClientRenameWorkspaceErrorInvalidCertificate
  | ClientRenameWorkspaceErrorInvalidEncryptedRealmName
  | ClientRenameWorkspaceErrorInvalidKeysBundle
  | ClientRenameWorkspaceErrorNoKey
  | ClientRenameWorkspaceErrorOffline
  | ClientRenameWorkspaceErrorStopped
  | ClientRenameWorkspaceErrorTimestampOutOfBallpark
  | ClientRenameWorkspaceErrorWorkspaceNotFound


// ClientRevokeUserError
export interface ClientRevokeUserErrorAuthorNotAllowed {
    tag: "AuthorNotAllowed"
    error: string
}
export interface ClientRevokeUserErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientRevokeUserErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface ClientRevokeUserErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface ClientRevokeUserErrorNoKey {
    tag: "NoKey"
    error: string
}
export interface ClientRevokeUserErrorOffline {
    tag: "Offline"
    error: string
}
export interface ClientRevokeUserErrorStopped {
    tag: "Stopped"
    error: string
}
export interface ClientRevokeUserErrorTimestampOutOfBallpark {
    tag: "TimestampOutOfBallpark"
    error: string
}
export interface ClientRevokeUserErrorUserIsSelf {
    tag: "UserIsSelf"
    error: string
}
export interface ClientRevokeUserErrorUserNotFound {
    tag: "UserNotFound"
    error: string
}
export type ClientRevokeUserError =
  | ClientRevokeUserErrorAuthorNotAllowed
  | ClientRevokeUserErrorInternal
  | ClientRevokeUserErrorInvalidCertificate
  | ClientRevokeUserErrorInvalidKeysBundle
  | ClientRevokeUserErrorNoKey
  | ClientRevokeUserErrorOffline
  | ClientRevokeUserErrorStopped
  | ClientRevokeUserErrorTimestampOutOfBallpark
  | ClientRevokeUserErrorUserIsSelf
  | ClientRevokeUserErrorUserNotFound


// ClientShareWorkspaceError
export interface ClientShareWorkspaceErrorAuthorNotAllowed {
    tag: "AuthorNotAllowed"
    error: string
}
export interface ClientShareWorkspaceErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientShareWorkspaceErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface ClientShareWorkspaceErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface ClientShareWorkspaceErrorOffline {
    tag: "Offline"
    error: string
}
export interface ClientShareWorkspaceErrorRecipientIsSelf {
    tag: "RecipientIsSelf"
    error: string
}
export interface ClientShareWorkspaceErrorRecipientNotFound {
    tag: "RecipientNotFound"
    error: string
}
export interface ClientShareWorkspaceErrorRecipientRevoked {
    tag: "RecipientRevoked"
    error: string
}
export interface ClientShareWorkspaceErrorRoleIncompatibleWithOutsider {
    tag: "RoleIncompatibleWithOutsider"
    error: string
}
export interface ClientShareWorkspaceErrorStopped {
    tag: "Stopped"
    error: string
}
export interface ClientShareWorkspaceErrorTimestampOutOfBallpark {
    tag: "TimestampOutOfBallpark"
    error: string
    server_timestamp: number
    client_timestamp: number
    ballpark_client_early_offset: number
    ballpark_client_late_offset: number
}
export interface ClientShareWorkspaceErrorWorkspaceNotFound {
    tag: "WorkspaceNotFound"
    error: string
}
export type ClientShareWorkspaceError =
  | ClientShareWorkspaceErrorAuthorNotAllowed
  | ClientShareWorkspaceErrorInternal
  | ClientShareWorkspaceErrorInvalidCertificate
  | ClientShareWorkspaceErrorInvalidKeysBundle
  | ClientShareWorkspaceErrorOffline
  | ClientShareWorkspaceErrorRecipientIsSelf
  | ClientShareWorkspaceErrorRecipientNotFound
  | ClientShareWorkspaceErrorRecipientRevoked
  | ClientShareWorkspaceErrorRoleIncompatibleWithOutsider
  | ClientShareWorkspaceErrorStopped
  | ClientShareWorkspaceErrorTimestampOutOfBallpark
  | ClientShareWorkspaceErrorWorkspaceNotFound


// ClientStartError
export interface ClientStartErrorDeviceUsedByAnotherProcess {
    tag: "DeviceUsedByAnotherProcess"
    error: string
}
export interface ClientStartErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientStartErrorLoadDeviceDecryptionFailed {
    tag: "LoadDeviceDecryptionFailed"
    error: string
}
export interface ClientStartErrorLoadDeviceInvalidData {
    tag: "LoadDeviceInvalidData"
    error: string
}
export interface ClientStartErrorLoadDeviceInvalidPath {
    tag: "LoadDeviceInvalidPath"
    error: string
}
export type ClientStartError =
  | ClientStartErrorDeviceUsedByAnotherProcess
  | ClientStartErrorInternal
  | ClientStartErrorLoadDeviceDecryptionFailed
  | ClientStartErrorLoadDeviceInvalidData
  | ClientStartErrorLoadDeviceInvalidPath


// ClientStartInvitationGreetError
export interface ClientStartInvitationGreetErrorInternal {
    tag: "Internal"
    error: string
}
export type ClientStartInvitationGreetError =
  | ClientStartInvitationGreetErrorInternal


// ClientStartWorkspaceError
export interface ClientStartWorkspaceErrorInternal {
    tag: "Internal"
    error: string
}
export interface ClientStartWorkspaceErrorWorkspaceNotFound {
    tag: "WorkspaceNotFound"
    error: string
}
export type ClientStartWorkspaceError =
  | ClientStartWorkspaceErrorInternal
  | ClientStartWorkspaceErrorWorkspaceNotFound


// ClientStopError
export interface ClientStopErrorInternal {
    tag: "Internal"
    error: string
}
export type ClientStopError =
  | ClientStopErrorInternal


// DeviceAccessStrategy
export interface DeviceAccessStrategyKeyring {
    tag: "Keyring"
    key_file: string
}
export interface DeviceAccessStrategyPassword {
    tag: "Password"
    password: string
    key_file: string
}
export interface DeviceAccessStrategySmartcard {
    tag: "Smartcard"
    key_file: string
}
export type DeviceAccessStrategy =
  | DeviceAccessStrategyKeyring
  | DeviceAccessStrategyPassword
  | DeviceAccessStrategySmartcard


// DeviceSaveStrategy
export interface DeviceSaveStrategyKeyring {
    tag: "Keyring"
}
export interface DeviceSaveStrategyPassword {
    tag: "Password"
    password: string
}
export interface DeviceSaveStrategySmartcard {
    tag: "Smartcard"
}
export type DeviceSaveStrategy =
  | DeviceSaveStrategyKeyring
  | DeviceSaveStrategyPassword
  | DeviceSaveStrategySmartcard


// EntryStat
export interface EntryStatFile {
    tag: "File"
    confinement_point: string | null
    id: string
    parent: string
    created: number
    updated: number
    base_version: number
    is_placeholder: boolean
    need_sync: boolean
    size: number
}
export interface EntryStatFolder {
    tag: "Folder"
    confinement_point: string | null
    id: string
    parent: string
    created: number
    updated: number
    base_version: number
    is_placeholder: boolean
    need_sync: boolean
}
export type EntryStat =
  | EntryStatFile
  | EntryStatFolder


// GreetInProgressError
export interface GreetInProgressErrorActiveUsersLimitReached {
    tag: "ActiveUsersLimitReached"
    error: string
}
export interface GreetInProgressErrorAlreadyDeleted {
    tag: "AlreadyDeleted"
    error: string
}
export interface GreetInProgressErrorCancelled {
    tag: "Cancelled"
    error: string
}
export interface GreetInProgressErrorCorruptedInviteUserData {
    tag: "CorruptedInviteUserData"
    error: string
}
export interface GreetInProgressErrorDeviceAlreadyExists {
    tag: "DeviceAlreadyExists"
    error: string
}
export interface GreetInProgressErrorGreeterNotAllowed {
    tag: "GreeterNotAllowed"
    error: string
}
export interface GreetInProgressErrorGreetingAttemptCancelled {
    tag: "GreetingAttemptCancelled"
    error: string
    origin: GreeterOrClaimer
    reason: CancelledGreetingAttemptReason
    timestamp: number
}
export interface GreetInProgressErrorHumanHandleAlreadyTaken {
    tag: "HumanHandleAlreadyTaken"
    error: string
}
export interface GreetInProgressErrorInternal {
    tag: "Internal"
    error: string
}
export interface GreetInProgressErrorNonceMismatch {
    tag: "NonceMismatch"
    error: string
}
export interface GreetInProgressErrorNotFound {
    tag: "NotFound"
    error: string
}
export interface GreetInProgressErrorOffline {
    tag: "Offline"
    error: string
}
export interface GreetInProgressErrorPeerReset {
    tag: "PeerReset"
    error: string
}
export interface GreetInProgressErrorTimestampOutOfBallpark {
    tag: "TimestampOutOfBallpark"
    error: string
    server_timestamp: number
    client_timestamp: number
    ballpark_client_early_offset: number
    ballpark_client_late_offset: number
}
export interface GreetInProgressErrorUserAlreadyExists {
    tag: "UserAlreadyExists"
    error: string
}
export interface GreetInProgressErrorUserCreateNotAllowed {
    tag: "UserCreateNotAllowed"
    error: string
}
export type GreetInProgressError =
  | GreetInProgressErrorActiveUsersLimitReached
  | GreetInProgressErrorAlreadyDeleted
  | GreetInProgressErrorCancelled
  | GreetInProgressErrorCorruptedInviteUserData
  | GreetInProgressErrorDeviceAlreadyExists
  | GreetInProgressErrorGreeterNotAllowed
  | GreetInProgressErrorGreetingAttemptCancelled
  | GreetInProgressErrorHumanHandleAlreadyTaken
  | GreetInProgressErrorInternal
  | GreetInProgressErrorNonceMismatch
  | GreetInProgressErrorNotFound
  | GreetInProgressErrorOffline
  | GreetInProgressErrorPeerReset
  | GreetInProgressErrorTimestampOutOfBallpark
  | GreetInProgressErrorUserAlreadyExists
  | GreetInProgressErrorUserCreateNotAllowed


// InviteListItem
export interface InviteListItemDevice {
    tag: "Device"
    addr: string
    token: string
    created_on: number
    status: InvitationStatus
}
export interface InviteListItemUser {
    tag: "User"
    addr: string
    token: string
    created_on: number
    claimer_email: string
    status: InvitationStatus
}
export type InviteListItem =
  | InviteListItemDevice
  | InviteListItemUser


// ListInvitationsError
export interface ListInvitationsErrorInternal {
    tag: "Internal"
    error: string
}
export interface ListInvitationsErrorOffline {
    tag: "Offline"
    error: string
}
export type ListInvitationsError =
  | ListInvitationsErrorInternal
  | ListInvitationsErrorOffline


// MountpointMountStrategy
export interface MountpointMountStrategyDirectory {
    tag: "Directory"
    base_dir: string
}
export interface MountpointMountStrategyDisabled {
    tag: "Disabled"
}
export interface MountpointMountStrategyDriveLetter {
    tag: "DriveLetter"
}
export type MountpointMountStrategy =
  | MountpointMountStrategyDirectory
  | MountpointMountStrategyDisabled
  | MountpointMountStrategyDriveLetter


// MountpointToOsPathError
export interface MountpointToOsPathErrorInternal {
    tag: "Internal"
    error: string
}
export type MountpointToOsPathError =
  | MountpointToOsPathErrorInternal


// MountpointUnmountError
export interface MountpointUnmountErrorInternal {
    tag: "Internal"
    error: string
}
export type MountpointUnmountError =
  | MountpointUnmountErrorInternal


// MoveEntryMode
export interface MoveEntryModeCanReplace {
    tag: "CanReplace"
}
export interface MoveEntryModeExchange {
    tag: "Exchange"
}
export interface MoveEntryModeNoReplace {
    tag: "NoReplace"
}
export type MoveEntryMode =
  | MoveEntryModeCanReplace
  | MoveEntryModeExchange
  | MoveEntryModeNoReplace


// ParseParsecAddrError
export interface ParseParsecAddrErrorInvalidUrl {
    tag: "InvalidUrl"
    error: string
}
export type ParseParsecAddrError =
  | ParseParsecAddrErrorInvalidUrl


// ParsedParsecAddr
export interface ParsedParsecAddrInvitationDevice {
    tag: "InvitationDevice"
    hostname: string
    port: number
    use_ssl: boolean
    organization_id: string
    token: string
}
export interface ParsedParsecAddrInvitationUser {
    tag: "InvitationUser"
    hostname: string
    port: number
    use_ssl: boolean
    organization_id: string
    token: string
}
export interface ParsedParsecAddrOrganization {
    tag: "Organization"
    hostname: string
    port: number
    use_ssl: boolean
    organization_id: string
}
export interface ParsedParsecAddrOrganizationBootstrap {
    tag: "OrganizationBootstrap"
    hostname: string
    port: number
    use_ssl: boolean
    organization_id: string
    token: string | null
}
export interface ParsedParsecAddrPkiEnrollment {
    tag: "PkiEnrollment"
    hostname: string
    port: number
    use_ssl: boolean
    organization_id: string
}
export interface ParsedParsecAddrServer {
    tag: "Server"
    hostname: string
    port: number
    use_ssl: boolean
}
export interface ParsedParsecAddrWorkspacePath {
    tag: "WorkspacePath"
    hostname: string
    port: number
    use_ssl: boolean
    organization_id: string
    workspace_id: string
    key_index: number
    encrypted_path: Uint8Array
}
export type ParsedParsecAddr =
  | ParsedParsecAddrInvitationDevice
  | ParsedParsecAddrInvitationUser
  | ParsedParsecAddrOrganization
  | ParsedParsecAddrOrganizationBootstrap
  | ParsedParsecAddrPkiEnrollment
  | ParsedParsecAddrServer
  | ParsedParsecAddrWorkspacePath


// TestbedError
export interface TestbedErrorDisabled {
    tag: "Disabled"
    error: string
}
export interface TestbedErrorInternal {
    tag: "Internal"
    error: string
}
export type TestbedError =
  | TestbedErrorDisabled
  | TestbedErrorInternal


// UserOrDeviceClaimInitialInfo
export interface UserOrDeviceClaimInitialInfoDevice {
    tag: "Device"
    handle: number
    greeter_user_id: string
    greeter_human_handle: HumanHandle
}
export interface UserOrDeviceClaimInitialInfoUser {
    tag: "User"
    handle: number
    claimer_email: string
    greeter_user_id: string
    greeter_human_handle: HumanHandle
}
export type UserOrDeviceClaimInitialInfo =
  | UserOrDeviceClaimInitialInfoDevice
  | UserOrDeviceClaimInitialInfoUser


// WaitForDeviceAvailableError
export interface WaitForDeviceAvailableErrorInternal {
    tag: "Internal"
    error: string
}
export type WaitForDeviceAvailableError =
  | WaitForDeviceAvailableErrorInternal


// WorkspaceCreateFileError
export interface WorkspaceCreateFileErrorEntryExists {
    tag: "EntryExists"
    error: string
}
export interface WorkspaceCreateFileErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceCreateFileErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceCreateFileErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceCreateFileErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceCreateFileErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceCreateFileErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceCreateFileErrorParentNotAFolder {
    tag: "ParentNotAFolder"
    error: string
}
export interface WorkspaceCreateFileErrorParentNotFound {
    tag: "ParentNotFound"
    error: string
}
export interface WorkspaceCreateFileErrorReadOnlyRealm {
    tag: "ReadOnlyRealm"
    error: string
}
export interface WorkspaceCreateFileErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceCreateFileError =
  | WorkspaceCreateFileErrorEntryExists
  | WorkspaceCreateFileErrorInternal
  | WorkspaceCreateFileErrorInvalidCertificate
  | WorkspaceCreateFileErrorInvalidKeysBundle
  | WorkspaceCreateFileErrorInvalidManifest
  | WorkspaceCreateFileErrorNoRealmAccess
  | WorkspaceCreateFileErrorOffline
  | WorkspaceCreateFileErrorParentNotAFolder
  | WorkspaceCreateFileErrorParentNotFound
  | WorkspaceCreateFileErrorReadOnlyRealm
  | WorkspaceCreateFileErrorStopped


// WorkspaceCreateFolderError
export interface WorkspaceCreateFolderErrorEntryExists {
    tag: "EntryExists"
    error: string
}
export interface WorkspaceCreateFolderErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceCreateFolderErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceCreateFolderErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceCreateFolderErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceCreateFolderErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceCreateFolderErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceCreateFolderErrorParentNotAFolder {
    tag: "ParentNotAFolder"
    error: string
}
export interface WorkspaceCreateFolderErrorParentNotFound {
    tag: "ParentNotFound"
    error: string
}
export interface WorkspaceCreateFolderErrorReadOnlyRealm {
    tag: "ReadOnlyRealm"
    error: string
}
export interface WorkspaceCreateFolderErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceCreateFolderError =
  | WorkspaceCreateFolderErrorEntryExists
  | WorkspaceCreateFolderErrorInternal
  | WorkspaceCreateFolderErrorInvalidCertificate
  | WorkspaceCreateFolderErrorInvalidKeysBundle
  | WorkspaceCreateFolderErrorInvalidManifest
  | WorkspaceCreateFolderErrorNoRealmAccess
  | WorkspaceCreateFolderErrorOffline
  | WorkspaceCreateFolderErrorParentNotAFolder
  | WorkspaceCreateFolderErrorParentNotFound
  | WorkspaceCreateFolderErrorReadOnlyRealm
  | WorkspaceCreateFolderErrorStopped


// WorkspaceDecryptPathAddrError
export interface WorkspaceDecryptPathAddrErrorCorruptedData {
    tag: "CorruptedData"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorCorruptedKey {
    tag: "CorruptedKey"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorKeyNotFound {
    tag: "KeyNotFound"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorNotAllowed {
    tag: "NotAllowed"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceDecryptPathAddrErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceDecryptPathAddrError =
  | WorkspaceDecryptPathAddrErrorCorruptedData
  | WorkspaceDecryptPathAddrErrorCorruptedKey
  | WorkspaceDecryptPathAddrErrorInternal
  | WorkspaceDecryptPathAddrErrorInvalidCertificate
  | WorkspaceDecryptPathAddrErrorInvalidKeysBundle
  | WorkspaceDecryptPathAddrErrorKeyNotFound
  | WorkspaceDecryptPathAddrErrorNotAllowed
  | WorkspaceDecryptPathAddrErrorOffline
  | WorkspaceDecryptPathAddrErrorStopped


// WorkspaceFdCloseError
export interface WorkspaceFdCloseErrorBadFileDescriptor {
    tag: "BadFileDescriptor"
    error: string
}
export interface WorkspaceFdCloseErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceFdCloseErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceFdCloseError =
  | WorkspaceFdCloseErrorBadFileDescriptor
  | WorkspaceFdCloseErrorInternal
  | WorkspaceFdCloseErrorStopped


// WorkspaceFdFlushError
export interface WorkspaceFdFlushErrorBadFileDescriptor {
    tag: "BadFileDescriptor"
    error: string
}
export interface WorkspaceFdFlushErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceFdFlushErrorNotInWriteMode {
    tag: "NotInWriteMode"
    error: string
}
export interface WorkspaceFdFlushErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceFdFlushError =
  | WorkspaceFdFlushErrorBadFileDescriptor
  | WorkspaceFdFlushErrorInternal
  | WorkspaceFdFlushErrorNotInWriteMode
  | WorkspaceFdFlushErrorStopped


// WorkspaceFdReadError
export interface WorkspaceFdReadErrorBadFileDescriptor {
    tag: "BadFileDescriptor"
    error: string
}
export interface WorkspaceFdReadErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceFdReadErrorInvalidBlockAccess {
    tag: "InvalidBlockAccess"
    error: string
}
export interface WorkspaceFdReadErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceFdReadErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceFdReadErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceFdReadErrorNotInReadMode {
    tag: "NotInReadMode"
    error: string
}
export interface WorkspaceFdReadErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceFdReadErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceFdReadError =
  | WorkspaceFdReadErrorBadFileDescriptor
  | WorkspaceFdReadErrorInternal
  | WorkspaceFdReadErrorInvalidBlockAccess
  | WorkspaceFdReadErrorInvalidCertificate
  | WorkspaceFdReadErrorInvalidKeysBundle
  | WorkspaceFdReadErrorNoRealmAccess
  | WorkspaceFdReadErrorNotInReadMode
  | WorkspaceFdReadErrorOffline
  | WorkspaceFdReadErrorStopped


// WorkspaceFdResizeError
export interface WorkspaceFdResizeErrorBadFileDescriptor {
    tag: "BadFileDescriptor"
    error: string
}
export interface WorkspaceFdResizeErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceFdResizeErrorNotInWriteMode {
    tag: "NotInWriteMode"
    error: string
}
export type WorkspaceFdResizeError =
  | WorkspaceFdResizeErrorBadFileDescriptor
  | WorkspaceFdResizeErrorInternal
  | WorkspaceFdResizeErrorNotInWriteMode


// WorkspaceFdStatError
export interface WorkspaceFdStatErrorBadFileDescriptor {
    tag: "BadFileDescriptor"
    error: string
}
export interface WorkspaceFdStatErrorInternal {
    tag: "Internal"
    error: string
}
export type WorkspaceFdStatError =
  | WorkspaceFdStatErrorBadFileDescriptor
  | WorkspaceFdStatErrorInternal


// WorkspaceFdWriteError
export interface WorkspaceFdWriteErrorBadFileDescriptor {
    tag: "BadFileDescriptor"
    error: string
}
export interface WorkspaceFdWriteErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceFdWriteErrorNotInWriteMode {
    tag: "NotInWriteMode"
    error: string
}
export type WorkspaceFdWriteError =
  | WorkspaceFdWriteErrorBadFileDescriptor
  | WorkspaceFdWriteErrorInternal
  | WorkspaceFdWriteErrorNotInWriteMode


// WorkspaceGeneratePathAddrError
export interface WorkspaceGeneratePathAddrErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceGeneratePathAddrErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceGeneratePathAddrErrorNoKey {
    tag: "NoKey"
    error: string
}
export interface WorkspaceGeneratePathAddrErrorNotAllowed {
    tag: "NotAllowed"
    error: string
}
export interface WorkspaceGeneratePathAddrErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceGeneratePathAddrErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceGeneratePathAddrError =
  | WorkspaceGeneratePathAddrErrorInternal
  | WorkspaceGeneratePathAddrErrorInvalidKeysBundle
  | WorkspaceGeneratePathAddrErrorNoKey
  | WorkspaceGeneratePathAddrErrorNotAllowed
  | WorkspaceGeneratePathAddrErrorOffline
  | WorkspaceGeneratePathAddrErrorStopped


// WorkspaceInfoError
export interface WorkspaceInfoErrorInternal {
    tag: "Internal"
    error: string
}
export type WorkspaceInfoError =
  | WorkspaceInfoErrorInternal


// WorkspaceMountError
export interface WorkspaceMountErrorDisabled {
    tag: "Disabled"
    error: string
}
export interface WorkspaceMountErrorInternal {
    tag: "Internal"
    error: string
}
export type WorkspaceMountError =
  | WorkspaceMountErrorDisabled
  | WorkspaceMountErrorInternal


// WorkspaceMoveEntryError
export interface WorkspaceMoveEntryErrorCannotMoveRoot {
    tag: "CannotMoveRoot"
    error: string
}
export interface WorkspaceMoveEntryErrorDestinationExists {
    tag: "DestinationExists"
    error: string
}
export interface WorkspaceMoveEntryErrorDestinationNotFound {
    tag: "DestinationNotFound"
    error: string
}
export interface WorkspaceMoveEntryErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceMoveEntryErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceMoveEntryErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceMoveEntryErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceMoveEntryErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceMoveEntryErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceMoveEntryErrorReadOnlyRealm {
    tag: "ReadOnlyRealm"
    error: string
}
export interface WorkspaceMoveEntryErrorSourceNotFound {
    tag: "SourceNotFound"
    error: string
}
export interface WorkspaceMoveEntryErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceMoveEntryError =
  | WorkspaceMoveEntryErrorCannotMoveRoot
  | WorkspaceMoveEntryErrorDestinationExists
  | WorkspaceMoveEntryErrorDestinationNotFound
  | WorkspaceMoveEntryErrorInternal
  | WorkspaceMoveEntryErrorInvalidCertificate
  | WorkspaceMoveEntryErrorInvalidKeysBundle
  | WorkspaceMoveEntryErrorInvalidManifest
  | WorkspaceMoveEntryErrorNoRealmAccess
  | WorkspaceMoveEntryErrorOffline
  | WorkspaceMoveEntryErrorReadOnlyRealm
  | WorkspaceMoveEntryErrorSourceNotFound
  | WorkspaceMoveEntryErrorStopped


// WorkspaceOpenFileError
export interface WorkspaceOpenFileErrorEntryExistsInCreateNewMode {
    tag: "EntryExistsInCreateNewMode"
    error: string
}
export interface WorkspaceOpenFileErrorEntryNotAFile {
    tag: "EntryNotAFile"
    error: string
}
export interface WorkspaceOpenFileErrorEntryNotFound {
    tag: "EntryNotFound"
    error: string
}
export interface WorkspaceOpenFileErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceOpenFileErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceOpenFileErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceOpenFileErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceOpenFileErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceOpenFileErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceOpenFileErrorReadOnlyRealm {
    tag: "ReadOnlyRealm"
    error: string
}
export interface WorkspaceOpenFileErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceOpenFileError =
  | WorkspaceOpenFileErrorEntryExistsInCreateNewMode
  | WorkspaceOpenFileErrorEntryNotAFile
  | WorkspaceOpenFileErrorEntryNotFound
  | WorkspaceOpenFileErrorInternal
  | WorkspaceOpenFileErrorInvalidCertificate
  | WorkspaceOpenFileErrorInvalidKeysBundle
  | WorkspaceOpenFileErrorInvalidManifest
  | WorkspaceOpenFileErrorNoRealmAccess
  | WorkspaceOpenFileErrorOffline
  | WorkspaceOpenFileErrorReadOnlyRealm
  | WorkspaceOpenFileErrorStopped


// WorkspaceRemoveEntryError
export interface WorkspaceRemoveEntryErrorCannotRemoveRoot {
    tag: "CannotRemoveRoot"
    error: string
}
export interface WorkspaceRemoveEntryErrorEntryIsFile {
    tag: "EntryIsFile"
    error: string
}
export interface WorkspaceRemoveEntryErrorEntryIsFolder {
    tag: "EntryIsFolder"
    error: string
}
export interface WorkspaceRemoveEntryErrorEntryIsNonEmptyFolder {
    tag: "EntryIsNonEmptyFolder"
    error: string
}
export interface WorkspaceRemoveEntryErrorEntryNotFound {
    tag: "EntryNotFound"
    error: string
}
export interface WorkspaceRemoveEntryErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceRemoveEntryErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceRemoveEntryErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceRemoveEntryErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceRemoveEntryErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceRemoveEntryErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceRemoveEntryErrorReadOnlyRealm {
    tag: "ReadOnlyRealm"
    error: string
}
export interface WorkspaceRemoveEntryErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceRemoveEntryError =
  | WorkspaceRemoveEntryErrorCannotRemoveRoot
  | WorkspaceRemoveEntryErrorEntryIsFile
  | WorkspaceRemoveEntryErrorEntryIsFolder
  | WorkspaceRemoveEntryErrorEntryIsNonEmptyFolder
  | WorkspaceRemoveEntryErrorEntryNotFound
  | WorkspaceRemoveEntryErrorInternal
  | WorkspaceRemoveEntryErrorInvalidCertificate
  | WorkspaceRemoveEntryErrorInvalidKeysBundle
  | WorkspaceRemoveEntryErrorInvalidManifest
  | WorkspaceRemoveEntryErrorNoRealmAccess
  | WorkspaceRemoveEntryErrorOffline
  | WorkspaceRemoveEntryErrorReadOnlyRealm
  | WorkspaceRemoveEntryErrorStopped


// WorkspaceStatEntryError
export interface WorkspaceStatEntryErrorEntryNotFound {
    tag: "EntryNotFound"
    error: string
}
export interface WorkspaceStatEntryErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceStatEntryErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceStatEntryErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceStatEntryErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceStatEntryErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceStatEntryErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceStatEntryErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceStatEntryError =
  | WorkspaceStatEntryErrorEntryNotFound
  | WorkspaceStatEntryErrorInternal
  | WorkspaceStatEntryErrorInvalidCertificate
  | WorkspaceStatEntryErrorInvalidKeysBundle
  | WorkspaceStatEntryErrorInvalidManifest
  | WorkspaceStatEntryErrorNoRealmAccess
  | WorkspaceStatEntryErrorOffline
  | WorkspaceStatEntryErrorStopped


// WorkspaceStatFolderChildrenError
export interface WorkspaceStatFolderChildrenErrorEntryIsFile {
    tag: "EntryIsFile"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorEntryNotFound {
    tag: "EntryNotFound"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceStatFolderChildrenErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceStatFolderChildrenError =
  | WorkspaceStatFolderChildrenErrorEntryIsFile
  | WorkspaceStatFolderChildrenErrorEntryNotFound
  | WorkspaceStatFolderChildrenErrorInternal
  | WorkspaceStatFolderChildrenErrorInvalidCertificate
  | WorkspaceStatFolderChildrenErrorInvalidKeysBundle
  | WorkspaceStatFolderChildrenErrorInvalidManifest
  | WorkspaceStatFolderChildrenErrorNoRealmAccess
  | WorkspaceStatFolderChildrenErrorOffline
  | WorkspaceStatFolderChildrenErrorStopped


// WorkspaceStopError
export interface WorkspaceStopErrorInternal {
    tag: "Internal"
    error: string
}
export type WorkspaceStopError =
  | WorkspaceStopErrorInternal


// WorkspaceStorageCacheSize
export interface WorkspaceStorageCacheSizeCustom {
    tag: "Custom"
    size: number
}
export interface WorkspaceStorageCacheSizeDefault {
    tag: "Default"
}
export type WorkspaceStorageCacheSize =
  | WorkspaceStorageCacheSizeCustom
  | WorkspaceStorageCacheSizeDefault


// WorkspaceWatchError
export interface WorkspaceWatchErrorEntryNotFound {
    tag: "EntryNotFound"
    error: string
}
export interface WorkspaceWatchErrorInternal {
    tag: "Internal"
    error: string
}
export interface WorkspaceWatchErrorInvalidCertificate {
    tag: "InvalidCertificate"
    error: string
}
export interface WorkspaceWatchErrorInvalidKeysBundle {
    tag: "InvalidKeysBundle"
    error: string
}
export interface WorkspaceWatchErrorInvalidManifest {
    tag: "InvalidManifest"
    error: string
}
export interface WorkspaceWatchErrorNoRealmAccess {
    tag: "NoRealmAccess"
    error: string
}
export interface WorkspaceWatchErrorOffline {
    tag: "Offline"
    error: string
}
export interface WorkspaceWatchErrorStopped {
    tag: "Stopped"
    error: string
}
export type WorkspaceWatchError =
  | WorkspaceWatchErrorEntryNotFound
  | WorkspaceWatchErrorInternal
  | WorkspaceWatchErrorInvalidCertificate
  | WorkspaceWatchErrorInvalidKeysBundle
  | WorkspaceWatchErrorInvalidManifest
  | WorkspaceWatchErrorNoRealmAccess
  | WorkspaceWatchErrorOffline
  | WorkspaceWatchErrorStopped


export function archiveDevice(
    device_path: string
): Promise<Result<null, ArchiveDeviceError>>
export function bootstrapOrganization(
    config: ClientConfig,
    on_event_callback: (handle: number, event: ClientEvent) => void,
    bootstrap_organization_addr: string,
    save_strategy: DeviceSaveStrategy,
    human_handle: HumanHandle,
    device_label: string,
    sequester_authority_verify_key: Uint8Array | null
): Promise<Result<AvailableDevice, BootstrapOrganizationError>>
export function buildParsecOrganizationBootstrapAddr(
    addr: string,
    organization_id: string
): Promise<string>
export function cancel(
    canceller: number
): Promise<Result<null, CancelError>>
export function claimerDeviceFinalizeSaveLocalDevice(
    handle: number,
    save_strategy: DeviceSaveStrategy
): Promise<Result<AvailableDevice, ClaimInProgressError>>
export function claimerDeviceInProgress1DoDenyTrust(
    canceller: number,
    handle: number
): Promise<Result<null, ClaimInProgressError>>
export function claimerDeviceInProgress1DoSignifyTrust(
    canceller: number,
    handle: number
): Promise<Result<DeviceClaimInProgress2Info, ClaimInProgressError>>
export function claimerDeviceInProgress2DoWaitPeerTrust(
    canceller: number,
    handle: number
): Promise<Result<DeviceClaimInProgress3Info, ClaimInProgressError>>
export function claimerDeviceInProgress3DoClaim(
    canceller: number,
    handle: number,
    requested_device_label: string
): Promise<Result<DeviceClaimFinalizeInfo, ClaimInProgressError>>
export function claimerDeviceInitialDoWaitPeer(
    canceller: number,
    handle: number
): Promise<Result<DeviceClaimInProgress1Info, ClaimInProgressError>>
export function claimerGreeterAbortOperation(
    handle: number
): Promise<Result<null, ClaimerGreeterAbortOperationError>>
export function claimerRetrieveInfo(
    config: ClientConfig,
    on_event_callback: (handle: number, event: ClientEvent) => void,
    addr: string
): Promise<Result<UserOrDeviceClaimInitialInfo, ClaimerRetrieveInfoError>>
export function claimerUserFinalizeSaveLocalDevice(
    handle: number,
    save_strategy: DeviceSaveStrategy
): Promise<Result<AvailableDevice, ClaimInProgressError>>
export function claimerUserInProgress1DoDenyTrust(
    canceller: number,
    handle: number
): Promise<Result<null, ClaimInProgressError>>
export function claimerUserInProgress1DoSignifyTrust(
    canceller: number,
    handle: number
): Promise<Result<UserClaimInProgress2Info, ClaimInProgressError>>
export function claimerUserInProgress2DoWaitPeerTrust(
    canceller: number,
    handle: number
): Promise<Result<UserClaimInProgress3Info, ClaimInProgressError>>
export function claimerUserInProgress3DoClaim(
    canceller: number,
    handle: number,
    requested_device_label: string,
    requested_human_handle: HumanHandle
): Promise<Result<UserClaimFinalizeInfo, ClaimInProgressError>>
export function claimerUserInitialDoWaitPeer(
    canceller: number,
    handle: number
): Promise<Result<UserClaimInProgress1Info, ClaimInProgressError>>
export function clientAcceptTos(
    client: number,
    tos_updated_on: number
): Promise<Result<null, ClientAcceptTosError>>
export function clientCancelInvitation(
    client: number,
    token: string
): Promise<Result<null, ClientCancelInvitationError>>
export function clientChangeAuthentication(
    client_config: ClientConfig,
    current_auth: DeviceAccessStrategy,
    new_auth: DeviceSaveStrategy
): Promise<Result<null, ClientChangeAuthenticationError>>
export function clientCreateWorkspace(
    client: number,
    name: string
): Promise<Result<string, ClientCreateWorkspaceError>>
export function clientGetTos(
    client: number
): Promise<Result<Tos, ClientGetTosError>>
export function clientGetUserDevice(
    client: number,
    device: string
): Promise<Result<[UserInfo, DeviceInfo], ClientGetUserDeviceError>>
export function clientInfo(
    client: number
): Promise<Result<ClientInfo, ClientInfoError>>
export function clientListInvitations(
    client: number
): Promise<Result<Array<InviteListItem>, ListInvitationsError>>
export function clientListUserDevices(
    client: number,
    user: string
): Promise<Result<Array<DeviceInfo>, ClientListUserDevicesError>>
export function clientListUsers(
    client: number,
    skip_revoked: boolean
): Promise<Result<Array<UserInfo>, ClientListUsersError>>
export function clientListWorkspaceUsers(
    client: number,
    realm_id: string
): Promise<Result<Array<WorkspaceUserAccessInfo>, ClientListWorkspaceUsersError>>
export function clientListWorkspaces(
    client: number
): Promise<Result<Array<WorkspaceInfo>, ClientListWorkspacesError>>
export function clientNewDeviceInvitation(
    client: number,
    send_email: boolean
): Promise<Result<NewInvitationInfo, ClientNewDeviceInvitationError>>
export function clientNewUserInvitation(
    client: number,
    claimer_email: string,
    send_email: boolean
): Promise<Result<NewInvitationInfo, ClientNewUserInvitationError>>
export function clientRenameWorkspace(
    client: number,
    realm_id: string,
    new_name: string
): Promise<Result<null, ClientRenameWorkspaceError>>
export function clientRevokeUser(
    client: number,
    user: string
): Promise<Result<null, ClientRevokeUserError>>
export function clientShareWorkspace(
    client: number,
    realm_id: string,
    recipient: string,
    role: RealmRole | null
): Promise<Result<null, ClientShareWorkspaceError>>
export function clientStart(
    config: ClientConfig,
    on_event_callback: (handle: number, event: ClientEvent) => void,
    access: DeviceAccessStrategy
): Promise<Result<number, ClientStartError>>
export function clientStartDeviceInvitationGreet(
    client: number,
    token: string
): Promise<Result<DeviceGreetInitialInfo, ClientStartInvitationGreetError>>
export function clientStartUserInvitationGreet(
    client: number,
    token: string
): Promise<Result<UserGreetInitialInfo, ClientStartInvitationGreetError>>
export function clientStartWorkspace(
    client: number,
    realm_id: string
): Promise<Result<number, ClientStartWorkspaceError>>
export function clientStop(
    client: number
): Promise<Result<null, ClientStopError>>
export function getDefaultConfigDir(
): Promise<string>
export function getDefaultDataBaseDir(
): Promise<string>
export function getDefaultMountpointBaseDir(
): Promise<string>
export function getPlatform(
): Promise<Platform>
export function greeterDeviceInProgress1DoWaitPeerTrust(
    canceller: number,
    handle: number
): Promise<Result<DeviceGreetInProgress2Info, GreetInProgressError>>
export function greeterDeviceInProgress2DoDenyTrust(
    canceller: number,
    handle: number
): Promise<Result<null, GreetInProgressError>>
export function greeterDeviceInProgress2DoSignifyTrust(
    canceller: number,
    handle: number
): Promise<Result<DeviceGreetInProgress3Info, GreetInProgressError>>
export function greeterDeviceInProgress3DoGetClaimRequests(
    canceller: number,
    handle: number
): Promise<Result<DeviceGreetInProgress4Info, GreetInProgressError>>
export function greeterDeviceInProgress4DoCreate(
    canceller: number,
    handle: number,
    device_label: string
): Promise<Result<null, GreetInProgressError>>
export function greeterDeviceInitialDoWaitPeer(
    canceller: number,
    handle: number
): Promise<Result<DeviceGreetInProgress1Info, GreetInProgressError>>
export function greeterUserInProgress1DoWaitPeerTrust(
    canceller: number,
    handle: number
): Promise<Result<UserGreetInProgress2Info, GreetInProgressError>>
export function greeterUserInProgress2DoDenyTrust(
    canceller: number,
    handle: number
): Promise<Result<null, GreetInProgressError>>
export function greeterUserInProgress2DoSignifyTrust(
    canceller: number,
    handle: number
): Promise<Result<UserGreetInProgress3Info, GreetInProgressError>>
export function greeterUserInProgress3DoGetClaimRequests(
    canceller: number,
    handle: number
): Promise<Result<UserGreetInProgress4Info, GreetInProgressError>>
export function greeterUserInProgress4DoCreate(
    canceller: number,
    handle: number,
    human_handle: HumanHandle,
    device_label: string,
    profile: UserProfile
): Promise<Result<null, GreetInProgressError>>
export function greeterUserInitialDoWaitPeer(
    canceller: number,
    handle: number
): Promise<Result<UserGreetInProgress1Info, GreetInProgressError>>
export function isKeyringAvailable(
): Promise<boolean>
export function listAvailableDevices(
    path: string
): Promise<Array<AvailableDevice>>
export function mountpointToOsPath(
    mountpoint: number,
    parsec_path: string
): Promise<Result<string, MountpointToOsPathError>>
export function mountpointUnmount(
    mountpoint: number
): Promise<Result<null, MountpointUnmountError>>
export function newCanceller(
): Promise<number>
export function parseParsecAddr(
    url: string
): Promise<Result<ParsedParsecAddr, ParseParsecAddrError>>
export function pathFilename(
    path: string
): Promise<string | null>
export function pathJoin(
    parent: string,
    child: string
): Promise<string>
export function pathNormalize(
    path: string
): Promise<string>
export function pathParent(
    path: string
): Promise<string>
export function pathSplit(
    path: string
): Promise<Array<string>>
export function testDropTestbed(
    path: string
): Promise<Result<null, TestbedError>>
export function testGetTestbedBootstrapOrganizationAddr(
    discriminant_dir: string
): Promise<Result<string | null, TestbedError>>
export function testGetTestbedOrganizationId(
    discriminant_dir: string
): Promise<Result<string | null, TestbedError>>
export function testNewTestbed(
    template: string,
    test_server: string | null
): Promise<Result<string, TestbedError>>
export function validateDeviceLabel(
    raw: string
): Promise<boolean>
export function validateEmail(
    raw: string
): Promise<boolean>
export function validateEntryName(
    raw: string
): Promise<boolean>
export function validateHumanHandleLabel(
    raw: string
): Promise<boolean>
export function validateInvitationToken(
    raw: string
): Promise<boolean>
export function validateOrganizationId(
    raw: string
): Promise<boolean>
export function validatePath(
    raw: string
): Promise<boolean>
export function waitForDeviceAvailable(
    config_dir: string,
    device_id: string
): Promise<Result<null, WaitForDeviceAvailableError>>
export function workspaceCreateFile(
    workspace: number,
    path: string
): Promise<Result<string, WorkspaceCreateFileError>>
export function workspaceCreateFolder(
    workspace: number,
    path: string
): Promise<Result<string, WorkspaceCreateFolderError>>
export function workspaceCreateFolderAll(
    workspace: number,
    path: string
): Promise<Result<string, WorkspaceCreateFolderError>>
export function workspaceDecryptPathAddr(
    workspace: number,
    link: string
): Promise<Result<string, WorkspaceDecryptPathAddrError>>
export function workspaceFdClose(
    workspace: number,
    fd: number
): Promise<Result<null, WorkspaceFdCloseError>>
export function workspaceFdFlush(
    workspace: number,
    fd: number
): Promise<Result<null, WorkspaceFdFlushError>>
export function workspaceFdRead(
    workspace: number,
    fd: number,
    offset: number,
    size: number
): Promise<Result<Uint8Array, WorkspaceFdReadError>>
export function workspaceFdResize(
    workspace: number,
    fd: number,
    length: number,
    truncate_only: boolean
): Promise<Result<null, WorkspaceFdResizeError>>
export function workspaceFdStat(
    workspace: number,
    fd: number
): Promise<Result<FileStat, WorkspaceFdStatError>>
export function workspaceFdWrite(
    workspace: number,
    fd: number,
    offset: number,
    data: Uint8Array
): Promise<Result<number, WorkspaceFdWriteError>>
export function workspaceFdWriteConstrainedIo(
    workspace: number,
    fd: number,
    offset: number,
    data: Uint8Array
): Promise<Result<number, WorkspaceFdWriteError>>
export function workspaceFdWriteStartEof(
    workspace: number,
    fd: number,
    data: Uint8Array
): Promise<Result<number, WorkspaceFdWriteError>>
export function workspaceGeneratePathAddr(
    workspace: number,
    path: string
): Promise<Result<string, WorkspaceGeneratePathAddrError>>
export function workspaceInfo(
    workspace: number
): Promise<Result<StartedWorkspaceInfo, WorkspaceInfoError>>
export function workspaceMount(
    workspace: number
): Promise<Result<[number, string], WorkspaceMountError>>
export function workspaceMoveEntry(
    workspace: number,
    src: string,
    dst: string,
    mode: MoveEntryMode
): Promise<Result<null, WorkspaceMoveEntryError>>
export function workspaceOpenFile(
    workspace: number,
    path: string,
    mode: OpenOptions
): Promise<Result<number, WorkspaceOpenFileError>>
export function workspaceOpenFileAndGetId(
    workspace: number,
    path: string,
    mode: OpenOptions
): Promise<Result<[number, string], WorkspaceOpenFileError>>
export function workspaceOpenFileById(
    workspace: number,
    entry_id: string,
    mode: OpenOptions
): Promise<Result<number, WorkspaceOpenFileError>>
export function workspaceRemoveEntry(
    workspace: number,
    path: string
): Promise<Result<null, WorkspaceRemoveEntryError>>
export function workspaceRemoveFile(
    workspace: number,
    path: string
): Promise<Result<null, WorkspaceRemoveEntryError>>
export function workspaceRemoveFolder(
    workspace: number,
    path: string
): Promise<Result<null, WorkspaceRemoveEntryError>>
export function workspaceRemoveFolderAll(
    workspace: number,
    path: string
): Promise<Result<null, WorkspaceRemoveEntryError>>
export function workspaceRenameEntryById(
    workspace: number,
    src_parent_id: string,
    src_name: string,
    dst_name: string,
    mode: MoveEntryMode
): Promise<Result<null, WorkspaceMoveEntryError>>
export function workspaceStatEntry(
    workspace: number,
    path: string
): Promise<Result<EntryStat, WorkspaceStatEntryError>>
export function workspaceStatEntryById(
    workspace: number,
    entry_id: string
): Promise<Result<EntryStat, WorkspaceStatEntryError>>
export function workspaceStatEntryByIdIgnoreConfinementPoint(
    workspace: number,
    entry_id: string
): Promise<Result<EntryStat, WorkspaceStatEntryError>>
export function workspaceStatFolderChildren(
    workspace: number,
    path: string
): Promise<Result<Array<[string, EntryStat]>, WorkspaceStatFolderChildrenError>>
export function workspaceStatFolderChildrenById(
    workspace: number,
    entry_id: string
): Promise<Result<Array<[string, EntryStat]>, WorkspaceStatFolderChildrenError>>
export function workspaceStop(
    workspace: number
): Promise<Result<null, WorkspaceStopError>>
export function workspaceWatchEntryOneshot(
    workspace: number,
    path: string
): Promise<Result<string, WorkspaceWatchError>>
