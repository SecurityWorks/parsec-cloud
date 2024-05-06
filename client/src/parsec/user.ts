// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import { libparsec } from '@/plugins/libparsec';

import { needsMocks } from '@/parsec/environment';
import { getParsecHandle } from '@/parsec/routing';
import { ClientListUsersError, ClientRevokeUserError, Result, UserID, UserInfo, UserProfile } from '@/parsec/types';
import { DateTime } from 'luxon';

function filterUserList(list: Array<UserInfo>, pattern: string): Array<UserInfo> {
  pattern = pattern.toLocaleLowerCase();
  return list.filter((item) => {
    return item.humanHandle.label.toLocaleLowerCase().includes(pattern) || item.humanHandle.email.toLocaleLowerCase().includes(pattern);
  });
}

export async function listUsers(skipRevoked = true, pattern = ''): Promise<Result<Array<UserInfo>, ClientListUsersError>> {
  const handle = getParsecHandle();

  if (handle !== null && !needsMocks()) {
    const result = await libparsec.clientListUsers(handle, skipRevoked);
    if (result.ok) {
      if (pattern.length > 0) {
        // Won't be using dates or `isRevoked` so the cast is fine
        result.value = filterUserList(result.value as Array<UserInfo>, pattern);
      }
      result.value.map((item) => {
        item.createdOn = DateTime.fromSeconds(item.createdOn as any as number);
        if (item.revokedOn) {
          item.revokedOn = DateTime.fromSeconds(item.revokedOn as any as number);
        }
        (item as UserInfo).isRevoked = (): boolean => item.revokedOn !== null;
        return item;
      });
    }
    return result as any as Promise<Result<Array<UserInfo>, ClientListUsersError>>;
  } else {
    let value: Array<UserInfo> = [
      {
        id: 'me',
        humanHandle: {
          email: 'user@host.com',
          label: 'Gordon Freeman',
        },
        currentProfile: UserProfile.Admin,
        createdOn: DateTime.now(),
        createdBy: 'device',
        revokedOn: null,
        revokedBy: null,
        isRevoked: (): boolean => false,
      },
      {
        id: 'id1',
        // cspell:disable-next-line
        humanHandle: { label: 'Cernd', email: 'cernd@gmail.com' },
        currentProfile: UserProfile.Standard,
        createdOn: DateTime.now(),
        createdBy: 'device',
        revokedOn: null,
        revokedBy: null,
        isRevoked: (): boolean => false,
      },
      {
        id: 'id2',
        // cspell:disable-next-line
        humanHandle: { label: 'Jaheira', email: 'jaheira@gmail.com' },
        currentProfile: UserProfile.Admin,
        createdOn: DateTime.now(),
        createdBy: 'device',
        revokedOn: null,
        revokedBy: null,
        isRevoked: (): boolean => false,
      },
      {
        id: 'id3',
        // cspell:disable-next-line
        humanHandle: { label: 'Karl Hungus', email: 'karlhungus@gmail.com' },
        currentProfile: UserProfile.Outsider,
        createdOn: DateTime.utc(1998, 4, 22),
        createdBy: 'device',
        revokedOn: null,
        revokedBy: null,
        isRevoked: (): boolean => false,
      },
      {
        id: 'id4',
        // cspell:disable-next-line
        humanHandle: { label: 'Patches', email: 'patches@yahoo.fr' },
        currentProfile: UserProfile.Standard,
        createdOn: DateTime.utc(2009, 10, 6),
        createdBy: 'device',
        revokedOn: null,
        revokedBy: null,
        isRevoked: (): boolean => false,
      },
    ];
    if (!skipRevoked) {
      value.push(
        {
          id: 'id5',
          // cspell:disable-next-line
          humanHandle: { label: 'Arthas Menethil', email: 'arthasmenethil@gmail.com' },
          currentProfile: UserProfile.Admin,
          createdOn: DateTime.utc(2002, 7, 3),
          createdBy: 'device',
          revokedOn: DateTime.now(),
          revokedBy: 'device',
          isRevoked: (): boolean => true,
        },
        {
          id: 'id6',
          // cspell:disable-next-line
          humanHandle: { label: 'Gaia', email: 'gaia@gmail.com' },
          currentProfile: UserProfile.Outsider,
          createdOn: DateTime.utc(2019, 7, 16),
          createdBy: 'device',
          revokedOn: DateTime.now(),
          revokedBy: 'device',
          isRevoked: (): boolean => true,
        },
        {
          id: 'id7',
          // cspell:disable-next-line
          humanHandle: { label: 'Valygar Corthala', email: 'val@gmail.com' },
          currentProfile: UserProfile.Standard,
          createdOn: DateTime.now(),
          createdBy: 'device',
          revokedOn: DateTime.now(),
          revokedBy: 'device',
          isRevoked: (): boolean => true,
        },
      );
    }
    if (pattern.length > 0) {
      value = filterUserList(value, pattern);
    }
    return { ok: true, value: value };
  }
}

export async function revokeUser(userId: UserID): Promise<Result<null, ClientRevokeUserError>> {
  const handle = getParsecHandle();

  if (handle !== null && !needsMocks()) {
    return await libparsec.clientRevokeUser(handle, userId);
  } else {
    return { ok: true, value: null };
  }
}

export enum UserInfoErrorTag {
  NotFound = 'NotFound',
  Internal = 'Internal',
}

interface UserInfoNotFoundError {
  tag: UserInfoErrorTag.NotFound;
}

interface UserInfoInternalError {
  tag: UserInfoErrorTag.Internal;
}

export type UserInfoError = UserInfoInternalError | UserInfoNotFoundError;

export async function getUserInfo(userId: UserID): Promise<Result<UserInfo, UserInfoError>> {
  const listResult = await listUsers(false);

  if (!listResult.ok) {
    return { ok: false, error: { tag: UserInfoErrorTag.Internal } };
  }

  const userInfo = listResult.value.find((item) => item.id === userId);
  if (!userInfo) {
    return { ok: false, error: { tag: UserInfoErrorTag.NotFound } };
  }
  return { ok: true, value: userInfo };
}
