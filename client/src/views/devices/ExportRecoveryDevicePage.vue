<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="container">
        <div class="recovery-container">
          <div v-show="state === ExportDevicePageState.Start">
            <ms-informative-text>
              {{ $t('RecoveryDevicePage.subtitles.newPassword') }}
            </ms-informative-text>
            <ms-informative-text>
              {{ $t('RecoveryDevicePage.subtitles.twoFilesToKeep') }}
            </ms-informative-text>

            <div>
              <div class="block">
                {{ $t('RecoveryDevicePage.titles.recoveryFile') }}
              </div>
              <div class="block">
                {{ $t('RecoveryDevicePage.titles.secretKey') }}
              </div>
            </div>
            <ion-button
              @click="exportDevice()"
            >
              {{ $t('RecoveryDevicePage.actions.understand') }}
            </ion-button>
          </div>
          <div v-if="state === ExportDevicePageState.Download">
            <ms-informative-text>
              {{ $t('RecoveryDevicePage.subtitles.keepFilesSeparate') }}
            </ms-informative-text>

            <div>
              <div class="block">
                {{ $t('RecoveryDevicePage.titles.recoveryFile') }}
                <div v-if="!recoveryFileDownloaded">
                  <ion-button
                    @click="downloadFile()"
                  >
                    {{ $t('RecoveryDevicePage.actions.download') }}
                  </ion-button>
                </div>
                <div v-else>
                  <ion-icon
                    :icon="checkmarkCircle"
                    class="checked"
                  />
                  {{ $t('RecoveryDevicePage.subtitles.fileDownloaded') }}
                </div>
              </div>
              <div class="block">
                {{ $t('RecoveryDevicePage.titles.recoveryKey') }}
                <div v-if="!recoveryKeyDownloaded">
                  <ion-button
                    @click="downloadKey()"
                  >
                    {{ $t('RecoveryDevicePage.actions.download') }}
                  </ion-button>
                </div>
                <div v-else>
                  <ion-icon
                    :icon="checkmarkCircle"
                    class="checked"
                  />
                  {{ $t('RecoveryDevicePage.subtitles.fileDownloaded') }}
                </div>
              </div>
              <a
                ref="downloadLink"
                v-show="false"
              />
              <div v-if="recoveryKeyDownloaded && recoveryFileDownloaded">
                <ion-button
                  class="return-btn button-outline"
                  @click="routerNavigateTo('workspaces')"
                >
                  <ion-icon
                    :icon="home"
                    class="icon"
                  />
                  {{ $t('RecoveryDevicePage.actions.backToWorkspaces') }}
                </ion-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import {
  IonPage,
  IonContent,
  IonButton,
} from '@ionic/vue';
import MsInformativeText from '@/components/core/ms-text/MsInformativeText.vue';
import { ref, inject } from 'vue';
import { getPasswordFromUser } from '@/components/core/ms-modal/MsPasswordInputModal.vue';
import { useI18n } from 'vue-i18n';
import { exportRecoveryDevice, RecoveryDeviceErrorTag } from '@/parsec';
import { NotificationManager, Notification, NotificationKey, NotificationLevel } from '@/services/notificationManager';
import { routerNavigateTo } from '@/router';
import { home, checkmarkCircle, fingerPrint } from 'ionicons/icons';

const { t } = useI18n();

enum ExportDevicePageState {
  Start = 'start',
  Download = 'download',
}

const state = ref(ExportDevicePageState.Start);
let code = '';
let file = '';
const downloadLink = ref();
const recoveryKeyDownloaded = ref(false);
const recoveryFileDownloaded = ref(false);
const notificationManager: NotificationManager = inject(NotificationKey)!;

async function exportDevice(): Promise<void> {
  const password = await getPasswordFromUser({
    title: t('PasswordInputModal.passwordNeeded'),
    subtitle: t('PasswordInputModal.enterPassword'),
    inputLabel: t('PasswordInputModal.password'),
    okButtonText: t('PasswordInputModal.validate'),
  });
  if (!password) {
    return;
  }
  const result = await exportRecoveryDevice(password);
  if (!result.ok) {
    // TODO: showToast();
    // result.error.tag === RecoveryDeviceErrorTag.WrongPassword
    console.log('ERROR !');
    return;
  }
  code = result.value.code;
  file = result.value.file;
  state.value = ExportDevicePageState.Download;
}

async function downloadKey(): Promise<void> {
  download(code, 'Recovery_code.txt');
  recoveryKeyDownloaded.value = true;
  notificationManager.showToast(
    new Notification({
      message: t('RecoveryDevicePage.toasts.keyDownloadOk'),
      level: NotificationLevel.Success,
    }),
  );
}

async function downloadFile(): Promise<void> {
  download(file, 'Recovery_device.data');
  recoveryFileDownloaded.value = true;
  notificationManager.showToast(
    new Notification({
      message: t('RecoveryDevicePage.toasts.fileDownloadOk'),
      level: NotificationLevel.Success,
    }),
  );
}

async function download(data: string, fileName: string): Promise<void> {
  downloadLink.value.setAttribute('href', `data:text/plain;charset=utf-8, ${encodeURIComponent(data)}`);
  downloadLink.value.setAttribute('download', fileName);
  downloadLink.value.click();
}
</script>

<style scoped lang="scss">
.container {
  display: flex;
  max-width: 70rem;
}

.recovery-container {
  margin: 2.5em 2rem 0;
}

.block {
  background-color: green;
  color: khaki;
  width: 15rem;
  height: 8rem;
  border: 3px solid magenta;
  float: left;
  margin: 1rem;
}

.return-btn {
  &::part(native) {
    background: none;
  }
}

.checked {
    color: lightgreen;
}
</style>
