<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="container">
        <div class="recovery-container">
          <div v-show="state === ExportDevicePageState.Start">
            <ms-informative-text>
              {{ 'Le texte que je veux' }}
            </ms-informative-text>
            <ms-informative-text>
              {{ 'Un autre texte' }}
            </ms-informative-text>

            <div>
              <div class="block">
                {{ 'Fichier' }}
              </div>
              <div class="block">
                {{ 'Clef' }}
              </div>
            </div>

            <ion-button
              @click="exportDevice()"
            >
              {{ 'J\'ai compris' }}
            </ion-button>
          </div>
          <div v-if="state === ExportDevicePageState.Download">
            <ms-informative-text>
              {{ 'Encore un autre text' }}
            </ms-informative-text>

            <div>
              <div class="block">
                {{ 'Fichier' }}
                <!-- TODO: Change once clicked -->
                <ion-button
                  @click="downloadFile()"
                >
                  {{ 'Download' }}
                </ion-button>
              </div>
              <div class="block">
                {{ 'Clef' }}

                <!-- TODO: Change once clicked -->
                <ion-button
                  @click="downloadKey()"
                >
                  {{ 'Download' }}
                </ion-button>
              </div>

              <a
                ref="downloadLink"
                v-show="false"
              />

              <!-- TODO: Once both have been clicked, button to get back to workspaces -->
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
import { ref } from 'vue';
import { getPasswordFromUser } from '@/components/core/ms-modal/MsPasswordInputModal.vue';
import { useI18n } from 'vue-i18n';
import { exportRecoveryDevice, RecoveryDeviceErrorTag } from '@/parsec';

const { t } = useI18n();

enum ExportDevicePageState {
  Start = 'start',
  Download = 'download',
}

const state = ref(ExportDevicePageState.Start);
let code = '';
let file = '';
const downloadLink = ref();

async function exportDevice(): Promise<void> {
  // TODO: translations
  const password = await getPasswordFromUser({
    title: t('Title'),
    subtitle: t('Subtitle'),
    inputLabel: t('Password'),
    okButtonText: t('OK'),
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
}

async function downloadFile(): Promise<void> {
  download(file, 'Recovery_device.data');
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
</style>
