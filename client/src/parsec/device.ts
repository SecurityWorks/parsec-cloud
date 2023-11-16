// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import { Result } from '@/parsec/types';
import { getParsecHandle } from '@/parsec/routing';
import { needsMocks } from '@/parsec/environment';

export interface RecoveryDeviceData {
  code: string,
  file: string,
}

export enum RecoveryDeviceErrorTag {
  Internal = 'internal'
}

export interface RecoveryDeviceError {
  tag: RecoveryDeviceErrorTag.Internal
}

export async function exportRecoveryDevice(_password: string): Promise<Result<RecoveryDeviceData, RecoveryDeviceError>> {
  const handle = getParsecHandle();

  if (handle !== null && !needsMocks()) {
    return {
      ok: true,
      value: {
        code: 'ABCDEF',
        file: 'Q2lnYXJlQU1vdXN0YWNoZQ==',
      },
    };
  } else {
    return {
      ok: true,
      value: {
        code: 'ABCDEF',
        file: 'Q2lnYXJlQU1vdXN0YWNoZQ==',
      },
    };
  }
}
