// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

export {
  BootstrapOrganizationErrorTag,
  CancelledGreetingAttemptReason,
  ClaimInProgressErrorTag,
  ClaimerRetrieveInfoErrorTag,
  ClientCancelInvitationErrorTag,
  ClientChangeAuthenticationErrorTag,
  ClientCreateWorkspaceErrorTag,
  ClientEventTag,
  ClientInfoErrorTag,
  ClientListUserDevicesErrorTag,
  ClientListUsersErrorTag,
  ClientListWorkspaceUsersErrorTag,
  ClientListWorkspacesErrorTag,
  ClientNewDeviceInvitationErrorTag,
  ClientNewUserInvitationErrorTag,
  ClientRenameWorkspaceErrorTag,
  ClientRevokeUserErrorTag,
  ClientShareWorkspaceErrorTag,
  ClientStartErrorTag,
  ClientStartInvitationGreetErrorTag,
  ClientStartWorkspaceErrorTag,
  ClientStopErrorTag,
  DeviceAccessStrategyTag,
  DeviceFileType,
  DeviceSaveStrategyTag,
  EntryStatTag as FileType,
  GreetInProgressErrorTag,
  InvitationEmailSentStatus,
  InvitationStatus,
  ListInvitationsErrorTag,
  MountpointToOsPathErrorTag,
  ParseParsecAddrErrorTag,
  ParsedParsecAddrTag,
  Platform,
  UserOrDeviceClaimInitialInfoTag,
  UserProfile,
  WorkspaceCreateFileErrorTag,
  WorkspaceCreateFolderErrorTag,
  WorkspaceDecryptPathAddrErrorTag,
  WorkspaceFdCloseErrorTag,
  WorkspaceFdReadErrorTag,
  WorkspaceFdWriteErrorTag,
  WorkspaceInfoErrorTag,
  WorkspaceMountErrorTag,
  WorkspaceMoveEntryErrorTag,
  WorkspaceOpenFileErrorTag,
  WorkspaceRemoveEntryErrorTag,
  WorkspaceStatEntryErrorTag,
  WorkspaceStatFolderChildrenErrorTag,
  WorkspaceStopErrorTag,
} from '@/plugins/libparsec';
export type {
  ArchiveDeviceError,
  AvailableDevice,
  BootstrapOrganizationError,
  ClaimInProgressError,
  ClaimerRetrieveInfoError,
  ClientAcceptTosError,
  ClientCancelInvitationError,
  ClientChangeAuthenticationError,
  ClientConfig,
  ClientCreateWorkspaceError,
  ClientEvent,
  ClientEventInvitationChanged,
  ClientEventPing,
  ClientGetTosError,
  ClientInfo,
  ClientInfoError,
  ClientListUserDevicesError,
  ClientListUsersError,
  ClientListWorkspaceUsersError,
  ClientListWorkspacesError,
  ClientNewDeviceInvitationError,
  ClientNewUserInvitationError,
  ClientRenameWorkspaceError,
  ClientRevokeUserError,
  ClientShareWorkspaceError,
  ClientStartError,
  ClientStartInvitationGreetError,
  ClientStartWorkspaceError,
  ClientStopError,
  DeviceAccessStrategy,
  DeviceAccessStrategyPassword,
  DeviceClaimFinalizeInfo,
  DeviceClaimInProgress1Info,
  DeviceClaimInProgress2Info,
  DeviceClaimInProgress3Info,
  DeviceGreetInProgress1Info,
  DeviceGreetInProgress2Info,
  DeviceGreetInProgress3Info,
  DeviceGreetInProgress4Info,
  DeviceGreetInitialInfo,
  DeviceInfo,
  InviteListItemDevice as DeviceInvitation,
  DeviceLabel,
  DeviceSaveStrategy,
  DeviceSaveStrategyKeyring,
  DeviceSaveStrategyPassword,
  EntryName,
  FileDescriptor,
  VlobID as FileID,
  GreetInProgressError,
  InvitationToken,
  ListInvitationsError,
  MountpointToOsPathError,
  NewInvitationInfo,
  ParseParsecAddrError,
  ParsecAddr,
  ParsecWorkspacePathAddr,
  ParsedParsecAddr,
  ParsedParsecAddrInvitationDevice,
  ParsedParsecAddrInvitationUser,
  ParsedParsecAddrOrganization,
  ParsedParsecAddrOrganizationBootstrap,
  ParsedParsecAddrPkiEnrollment,
  ParsedParsecAddrServer,
  ParsedParsecAddrWorkspacePath,
  Result,
  SASCode,
  SizeInt,
  Tos,
  UserClaimFinalizeInfo,
  UserClaimInProgress1Info,
  UserClaimInProgress2Info,
  UserClaimInProgress3Info,
  UserGreetInProgress1Info,
  UserGreetInProgress2Info,
  UserGreetInProgress3Info,
  UserGreetInProgress4Info,
  UserGreetInitialInfo,
  InviteListItemUser as UserInvitation,
  UserOrDeviceClaimInitialInfoDevice,
  UserOrDeviceClaimInitialInfoUser,
  WorkspaceCreateFileError,
  WorkspaceCreateFolderError,
  WorkspaceDecryptPathAddrError,
  WorkspaceFdCloseError,
  WorkspaceFdReadError,
  WorkspaceFdResizeError,
  WorkspaceFdWriteError,
  WorkspaceGeneratePathAddrError,
  VlobID as WorkspaceID,
  WorkspaceInfoError,
  WorkspaceMountError,
  WorkspaceMoveEntryError,
  WorkspaceOpenFileError,
  WorkspaceRemoveEntryError,
  WorkspaceStatEntryError,
  WorkspaceStatFolderChildrenError,
  WorkspaceStopError,
} from '@/plugins/libparsec';

import type {
  DateTime,
  DeviceInfo,
  EntryName,
  FsPath,
  Handle,
  HumanHandle,
  OrganizationID,
  EntryStatFile as ParsecEntryStatFile,
  EntryStatFolder as ParsecEntryStatFolder,
  ParsecOrganizationAddr,
  StartedWorkspaceInfo as ParsecStartedWorkspaceInfo,
  UserInfo as ParsecUserInfo,
  WorkspaceInfo as ParsecWorkspaceInfo,
  Path,
  UserID,
  UserProfile,
  VlobID,
} from '@/plugins/libparsec';

import { RealmRole as WorkspaceRole } from '@/plugins/libparsec';

type WorkspaceHandle = Handle;
type EntryID = VlobID;
type WorkspaceName = EntryName;
type ConnectionHandle = Handle;
type MountpointHandle = Handle;
type SystemPath = Path;

interface UserInfo extends ParsecUserInfo {
  isRevoked: () => boolean;
  isFrozen: () => boolean;
}

interface OwnDeviceInfo extends DeviceInfo {
  isCurrent: boolean;
}

interface EntryStatFolder extends ParsecEntryStatFolder {
  isFile: () => boolean;
  isConfined: () => boolean;
  path: FsPath;
  name: EntryName;
}

interface EntryStatFile extends ParsecEntryStatFile {
  isFile: () => boolean;
  isConfined: () => boolean;
  path: FsPath;
  name: EntryName;
}

interface OpenOptions {
  read?: boolean;
  write?: boolean;
  append?: boolean;
  truncate?: boolean;
  create?: boolean;
  createNew?: boolean;
}

type EntryStat = EntryStatFile | EntryStatFolder;

enum GetWorkspaceNameErrorTag {
  NotFound = 'NotFound',
}

interface GetWorkspaceNameError {
  tag: GetWorkspaceNameErrorTag.NotFound;
}

enum GetAbsolutePathErrorTag {
  NotFound = 'NotFound',
}

interface GetAbsolutePathError {
  tag: GetAbsolutePathErrorTag.NotFound;
}

interface UserTuple {
  id: UserID;
  humanHandle: HumanHandle;
  profile: UserProfile;
}

interface WorkspaceInfo extends ParsecWorkspaceInfo {
  sharing: Array<[UserTuple, WorkspaceRole | null]>;
  size: number;
  lastUpdated: DateTime;
  availableOffline: boolean;
  handle: WorkspaceHandle;
  mountpoints: [MountpointHandle, SystemPath][];
}

interface StartedWorkspaceInfo extends ParsecStartedWorkspaceInfo {
  handle: WorkspaceHandle;
}

enum OrganizationInfoErrorTag {
  Internal = 'Internal',
}

interface OrganizationInfoErrorInternal {
  tag: OrganizationInfoErrorTag.Internal;
}

type OrganizationInfoError = OrganizationInfoErrorInternal;

interface OrganizationInfo {
  users: {
    revoked: number;
    total: number;
    active: number;
    admins: number;
    standards: number;
    outsiders: number;
  };
  size: {
    metadata: number;
    data: number;
  };
  outsidersAllowed: boolean;
  userLimit?: number;
  hasUserLimit: boolean;
  organizationAddr: ParsecOrganizationAddr;
  organizationId: OrganizationID;
}

export {
  ConnectionHandle,
  DateTime,
  EntryID,
  EntryStat,
  EntryStatFile,
  EntryStatFolder,
  FsPath,
  GetAbsolutePathError,
  GetAbsolutePathErrorTag,
  GetWorkspaceNameError,
  GetWorkspaceNameErrorTag,
  HumanHandle,
  MountpointHandle,
  OpenOptions,
  OrganizationID,
  OrganizationInfo,
  OrganizationInfoError,
  OrganizationInfoErrorTag,
  OwnDeviceInfo,
  ParsecOrganizationAddr,
  StartedWorkspaceInfo,
  SystemPath,
  UserID,
  UserInfo,
  UserTuple,
  WorkspaceHandle,
  WorkspaceInfo,
  WorkspaceName,
  WorkspaceRole,
};
