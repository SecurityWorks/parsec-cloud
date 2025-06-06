<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<!-- This page serve only for test purposes -->

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <ion-header collapse="condense">
        <ion-title size="large"> Test libparsec </ion-title>
      </ion-header>
      <div v-html="logs" />
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import {
  BootstrapOrganizationErrorTag,
  ClientConfig,
  ClientEvent,
  DeviceSaveStrategyTag,
  MountpointMountStrategyTag,
  WorkspaceStorageCacheSizeTag,
  libparsec,
} from '@/plugins/libparsec';
import { IonContent, IonHeader, IonPage, IonTitle } from '@ionic/vue';
import { onMounted, ref } from 'vue';

const logs = ref('');

async function testCase<T>(name: string, cb: () => Promise<T>): Promise<T> {
  console.log(`${name}...`);
  logs.value += `${name}...`;
  let ret;
  try {
    ret = await cb();
  } catch (error) {
    logs.value += ` <span style="color: red; font-weight: bold">☒</span><br>${error}`;
    throw error;
  }
  console.log(`${name}... ok !`);
  logs.value += ' <span style="color: green; font-weight: bold">☑</span><br>';
  return ret;
}

// ARE YOU KIDDING ME JAVASCRIPT ??????
function compareArrays(a: Array<any>, b: Array<any>): boolean {
  return (
    a.length === b.length &&
    a.every((value, index) => {
      b[index] === value;
    })
  );
}

function assert(outcome: boolean, msg: string): void {
  if (!outcome) {
    throw `Error: ${msg}`;
  }
}
// {
//   "keyFilePath": "/parsec/testbed/1/Org20/alice@dev1.key",
//   "organizationId": "Org20",
//   "deviceId": "alice@dev1",
//   "humanHandle": "Alicey McAliceFace <alice@example.com>",
//   "deviceLabel": "My dev1 machine",
//   "ty": {
//     "tag": "Password"
//   }
// }

onMounted(async () => {
  // Tests are ran here

  await testBootstrapOrganization();
});

/*
 * Bootstrap organization
 */

async function testBootstrapOrganization(): Promise<void> {
  const configResult = await testCase('Init empty testbed', async () => {
    return await libparsec.testNewTestbed('empty', import.meta.env.PARSEC_APP_TESTBED_SERVER);
  });

  if (!configResult.ok) {
    throw new Error('Failed to init testbed');
  }

  const configPath = configResult.value;

  const config: ClientConfig = {
    configDir: configPath,
    dataBaseDir: configPath,
    mountpointMountStrategy: { tag: MountpointMountStrategyTag.Disabled },
    workspaceStorageCacheSize: {
      tag: WorkspaceStorageCacheSizeTag.Default,
    },
    withMonitors: false,
    preventSyncPattern: null,
    logLevel: null,
  };

  const bootstrapAddrResult = await libparsec.testGetTestbedBootstrapOrganizationAddr(configPath);
  if (!bootstrapAddrResult.ok || bootstrapAddrResult.value === null) {
    throw new Error("Couldn't retrieve bootstrap organization addr");
  }

  const bootstrapAddr = bootstrapAddrResult.value;

  const humanHandle = { label: 'John', email: 'john@example.com' };
  const availableDevice = await testCase('Bootstrap organization', async () => {
    const outcome = await libparsec.bootstrapOrganization(
      config,
      bootstrapAddr,
      {
        tag: DeviceSaveStrategyTag.Password,
        password: 'P@ssw0rd.',
      },
      humanHandle,
      'PC1',
      null,
    );
    switch (outcome.ok) {
      case true:
        return outcome.value;

      default:
        throw new Error(`Returned error: ${JSON.stringify(outcome, null, 2)}`);
    }
  });
  assert(availableDevice.humanHandle === humanHandle, `Invalid available device: ${JSON.stringify(availableDevice, null, 2)}`);
  assert(availableDevice.deviceLabel === 'PC1', `Invalid available device: ${JSON.stringify(availableDevice, null, 2)}`);

  // Cannot re-bootstrap the organization !
  await testCase('Bootstrap organization bad outcome', async () => {
    const outcome = await libparsec.bootstrapOrganization(
      config,
      bootstrapAddr,
      {
        tag: DeviceSaveStrategyTag.Password,
        password: 'P@ssw0rd.',
      },
      availableDevice.humanHandle,
      availableDevice.deviceLabel,
      null,
    );
    switch (outcome.ok) {
      case true:
        throw new Error(`Returned success but expected error ! ${JSON.stringify(outcome, null, 2)}`);

      case false:
        switch (outcome.error.tag) {
          case BootstrapOrganizationErrorTag.AlreadyUsedToken:
            break;

          default:
            throw new Error(`Returned expected error: ${JSON.stringify(outcome, null, 2)}`);
        }
    }
  });

  await testCase('Teardown testbed', async () => {
    await libparsec.testDropTestbed(configPath);
  });
}
</script>
