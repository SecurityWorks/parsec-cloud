<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="container">
        <div class="recovery-container">
          <div v-show="state === ExportDevicePageState.Start">
            <ms-informative-text>
              {{ $t('ExportRecoveryDevicePage.subtitles.newPassword') }}
            </ms-informative-text>
            <ms-informative-text>
              {{ $t('ExportRecoveryDevicePage.subtitles.twoFilesToKeep') }}
            </ms-informative-text>

            <div>
              <div class="block">
                {{ $t('ExportRecoveryDevicePage.titles.recoveryFile') }}
              </div>
              <div class="block">
                {{ $t('ExportRecoveryDevicePage.titles.recoveryKey') }}
              </div>
            </div>
            <ion-button
              @click="exportDevice()"
              id="exportDevice"
            >
              {{ $t('ExportRecoveryDevicePage.actions.understand') }}
            </ion-button>
          </div>
          <div v-if="state === ExportDevicePageState.Download">
            <ms-informative-text>
              {{ $t('ExportRecoveryDevicePage.subtitles.keepFilesSeparate') }}
            </ms-informative-text>

            <div>
              <div class="block">
                {{ $t('ExportRecoveryDevicePage.titles.recoveryFile') }}
                <div v-if="!recoveryFileDownloaded">
                  <ion-button
                    @click="downloadRecoveryFile()"
                  >
                    {{ $t('ExportRecoveryDevicePage.actions.download') }}
                  </ion-button>
                </div>
                <div v-else>
                  <ion-icon
                    :icon="checkmarkCircle"
                    class="checked"
                  />
                  {{ $t('ExportRecoveryDevicePage.subtitles.fileDownloaded') }}
                </div>
              </div>
              <div class="block">
                {{ $t('ExportRecoveryDevicePage.titles.recoveryKey') }}
                <div v-if="!recoveryKeyDownloaded">
                  <ion-button
                    @click="downloadRecoveryKey()"
                  >
                    {{ $t('ExportRecoveryDevicePage.actions.download') }}
                  </ion-button>
                </div>
                <div v-else>
                  <ion-icon
                    :icon="checkmarkCircle"
                    class="checked"
                  />
                  {{ $t('ExportRecoveryDevicePage.subtitles.fileDownloaded') }}
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
                  {{ $t('ExportRecoveryDevicePage.actions.backToWorkspaces') }}
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
import { getClientInfo } from '@/parsec/login';
import { NotificationManager, Notification, NotificationKey, NotificationLevel } from '@/services/notificationManager';
import { routerNavigateTo } from '@/router';
import { home, checkmarkCircle } from 'ionicons/icons';

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
  const password = await getPasswordFromUser(t);
  if (!password) {
    return;
  }
  const result = await exportRecoveryDevice(password);
  if (!result.ok) {
    const notificationMsg = result.error.tag === RecoveryDeviceErrorTag.Invalid ?
      t('PasswordInputModal.invalid') :
      t('PasswordInputModal.otherError');
    notificationManager.showToast(
      new Notification({
        message: notificationMsg,
        level: NotificationLevel.Error,
      }),
    );
    return;
  }
  code = result.value.code;
  file = result.value.file;
  state.value = ExportDevicePageState.Download;
}

async function downloadRecoveryKey(): Promise<void> {
  const clientInfo = await getClientInfo();
  fileDownload(code, t('ExportRecoveryDevicePage.filenames.recoveryKey', { org: (clientInfo.ok ? clientInfo.value.organizationId : '') }));
  recoveryKeyDownloaded.value = true;
  notificationManager.showToast(
    new Notification({
      message: t('ExportRecoveryDevicePage.toasts.keyDownloadOk'),
      level: NotificationLevel.Success,
    }),
  );
}

async function downloadRecoveryFile(): Promise<void> {
  const clientInfo = await getClientInfo();
  fileDownload(file, t('ExportRecoveryDevicePage.filenames.recoveryFile', { org: (clientInfo.ok ? clientInfo.value.organizationId : '') }));
  recoveryFileDownloaded.value = true;
  notificationManager.showToast(
    new Notification({
      message: t('ExportRecoveryDevicePage.toasts.fileDownloadOk'),
      level: NotificationLevel.Success,
    }),
  );
}

async function fileDownload(data: string, fileName: string): Promise<void> {
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
