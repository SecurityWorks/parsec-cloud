// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import type {
  DeviceLabel,
  VlobID as WorkspaceID,
  AvailableDevice,
  Result,
  Handle,
  ClientEvent,
  DateTime,
  ClientEventPing,
  DeviceAccessStrategyPassword,
  ClientConfig,
  EntryName as WorkspaceName,
  InvitationToken,
  NewUserInvitationError,
  NewDeviceInvitationError,
  InviteListItemUser as UserInvitation,
  UserClaimInProgress1Info,
  UserClaimInProgress2Info,
  UserClaimInProgress3Info,
  UserClaimFinalizeInfo,
  DeviceClaimFinalizeInfo,
  DeviceClaimInProgress1Info,
  DeviceClaimInProgress2Info,
  DeviceClaimInProgress3Info,
  SASCode,
  HumanHandle,
  UserOrDeviceClaimInitialInfoUser,
  UserOrDeviceClaimInitialInfoDevice,
  ParsedBackendAddr,
  ClientStartError,
  ListInvitationsError,
  DeleteInvitationError,
  ClientListWorkspacesError,
  ClientCreateWorkspaceError,
  ClientStopError,
  ClaimerRetrieveInfoError,
  ClaimInProgressError,
  BootstrapOrganizationError,
  ParseBackendAddrError,
  OrganizationID,
  BackendAddr,
  ParsedBackendAddrInvitationUser,
  ClientInfo,
  ClientInfoError,
  ClientStartInvitationGreetError,
  UserGreetInitialInfo,
  UserGreetInProgress1Info,
  GreetInProgressError,
  UserGreetInProgress2Info,
  UserGreetInProgress3Info,
  UserGreetInProgress4Info,
  WorkspaceInfo,
  UserInfo as ParsecUserInfo,
  ClientListUsersError,
  DeviceInfo,
  ClientListUserDevicesError,
  UserID,
} from '@/plugins/libparsec';
// Enums have to be imported separately
import {
  DeviceFileType,
  InvitationEmailSentStatus,
  InvitationStatus,
  UserProfile,
  RealmRole as WorkspaceRole,
} from '@/plugins/libparsec';

interface UserInfo extends ParsecUserInfo {
  isRevoked: () => boolean
}

enum BackendAddrType {
  Invalid = 'InvalidUrl',
  Base = 'Base',
  InvitationUser = 'InvitationUser',
  InvitationDevice = 'InvitationDevice',
  OrganizationBootstrap = 'OrganizationBootstrap',
  OrganizationFileLink = 'OrganizationFileLink',
  PkiEnrollment = 'PkiEnrollment',
}

interface GetWorkspaceNameError {
  tag: 'NotFound'
}

export {
  DeviceLabel,
  UserInvitation,
  WorkspaceID,
  WorkspaceName,
  AvailableDevice,
  ClientConfig,
  Result,
  DeviceAccessStrategyPassword,
  ClientEvent,
  Handle,
  DateTime,
  ClientEventPing,
  InvitationStatus,
  ParsedBackendAddr,
  DeviceFileType,
  HumanHandle,
  SASCode,
  InvitationEmailSentStatus,
  InvitationToken,
  BackendAddr,
  OrganizationID,
  UserClaimInProgress1Info,
  UserClaimInProgress2Info,
  UserClaimInProgress3Info,
  UserClaimFinalizeInfo,
  DeviceClaimFinalizeInfo,
  DeviceClaimInProgress1Info,
  DeviceClaimInProgress2Info,
  DeviceClaimInProgress3Info,
  UserOrDeviceClaimInitialInfoUser,
  UserOrDeviceClaimInitialInfoDevice,
  ParsedBackendAddrInvitationUser,
  BackendAddrType,
  UserInfo,
  UserProfile,
  UserGreetInitialInfo,
  UserGreetInProgress1Info,
  UserGreetInProgress2Info,
  UserGreetInProgress3Info,
  UserGreetInProgress4Info,
  WorkspaceRole,
  WorkspaceInfo,
  ClientInfo,
  DeviceInfo,
  UserID,
};

export {
  ClientStopError,
  ListInvitationsError,
  ClientStartError,
  NewUserInvitationError,
  NewDeviceInvitationError,
  ClaimerRetrieveInfoError,
  ClaimInProgressError,
  BootstrapOrganizationError,
  ParseBackendAddrError,
  DeleteInvitationError,
  ClientListWorkspacesError,
  ClientCreateWorkspaceError,
  ClientInfoError,
  GetWorkspaceNameError,
  ClientStartInvitationGreetError,
  GreetInProgressError,
  ClientListUsersError,
  ClientListUserDevicesError,
};
