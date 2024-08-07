<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <!-- step 1: recovery file -->
  <div
    v-if="state === ImportDevicePageState.Start"
    class="recovery-content"
  >
    <div class="recovery-header">
      <ion-title class="recovery-header__title title-h1">
        {{ $msTranslate('ImportRecoveryDevicePage.titles.forgottenPassword') }}
      </ion-title>
    </div>
    <ion-card class="recovery-card">
      <ion-card-content class="card-container">
        <organization-card
          :device="device"
          :org-name-only="true"
        />
        <ms-report-text
          :theme="MsReportTheme.Warning"
          id="warning-text"
        >
          {{ $msTranslate('ImportRecoveryDevicePage.subtitles.recoveryFilesMustExistWarning') }}
        </ms-report-text>
        <div class="recovery-list">
          <!-- recovery item -->
          <div class="recovery-list-item">
            <div class="recovery-list-item__title subtitles-normal">
              <span class="number subtitles-normal">1</span>
              {{ $msTranslate('ImportRecoveryDevicePage.titles.recoveryFile') }}
            </div>
            <div class="recovery-list-item__button">
              <input
                type="file"
                hidden
                ref="hiddenInput"
              />
              <div
                v-if="!recoveryFile"
                class="body"
              >
                {{ $msTranslate('ImportRecoveryDevicePage.subtitles.noFileSelected') }}
              </div>
              <div
                v-else
                class="body file-added"
                @click="importButtonClick()"
              >
                {{ recoveryFile.name }}
              </div>
              <ion-button
                id="browse-button"
                @click="importButtonClick()"
                fill="outline"
              >
                {{ $msTranslate('ImportRecoveryDevicePage.actions.browse') }}
              </ion-button>
            </div>
          </div>

          <!-- ----- -->
          <div class="recovery-divider" />

          <!-- recovery item -->
          <div
            class="recovery-list-item"
            :class="{ disabled: !recoveryFile }"
          >
            <div class="recovery-list-item__title subtitles-normal">
              <span class="number">2</span>
              {{ $msTranslate('ImportRecoveryDevicePage.titles.recoveryKey') }}
            </div>
            <div class="recovery-list-item__button">
              <ms-input
                class="recovery-list-item__input"
                id="secret-key-input"
                :placeholder="secretKeyPlaceholder"
                v-model="secretKey"
                @change="checkSecretKeyValidity()"
              />
              <ion-icon
                id="checkmark-icon"
                v-show="isSecretKeyValid"
                :icon="checkmarkCircle"
              />
            </div>
          </div>
        </div>
        <div class="next-button">
          <ion-button
            slot="start"
            id="to-password-change-btn"
            @click="goToPasswordChange()"
            :disabled="!isSecretKeyValid || !recoveryFile"
          >
            {{ $msTranslate('ImportRecoveryDevicePage.actions.next') }}
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>
  </div>
  <!-- step 2: new password -->
  <div
    v-else-if="state === ImportDevicePageState.Password"
    class="recovery-content password-input"
  >
    <div class="recovery-header">
      <ion-title class="recovery-header__title title-h1">
        {{ $msTranslate('ImportRecoveryDevicePage.titles.setNewPassword') }}
      </ion-title>
    </div>
    <ion-card class="recovery-card">
      <ms-choose-password-input
        :password-label="'ImportRecoveryDevicePage.titles.setNewPassword'"
        @on-enter-keyup="createNewDevice()"
        ref="choosePasswordInput"
      />
      <ion-button
        id="validate-password-btn"
        class="validate-button"
        :disabled="!changeButtonIsEnabled"
        @click="createNewDevice()"
      >
        {{ $msTranslate('ImportRecoveryDevicePage.actions.validatePassword') }}
      </ion-button>
    </ion-card>
  </div>
  <!-- step 3: done -->
  <div
    v-else-if="state === ImportDevicePageState.Done"
    id="success-step"
    class="recovery-content"
  >
    <ion-card class="recovery-card success-card">
      <ion-card-title class="success-card__title title-h2">
        {{ $msTranslate('ImportRecoveryDevicePage.titles.passwordChanged') }}
      </ion-card-title>
      <ms-informative-text>
        {{ $msTranslate('ImportRecoveryDevicePage.subtitles.passwordModified') }}
      </ms-informative-text>
      <ion-button
        class="success-card__button"
        @click="onLoginClick()"
      >
        {{ $msTranslate('ImportRecoveryDevicePage.actions.goBackToLogin') }}
      </ion-button>
    </ion-card>
  </div>
</template>

<script setup lang="ts">
import { secretKeyValidator } from '@/common/validators';
import { MsChoosePasswordInput, MsInformativeText, MsReportText, MsReportTheme, MsInput, asyncComputed, Validity } from 'megashark-lib';
import OrganizationCard from '@/components/organizations/OrganizationCard.vue';
import { AvailableDevice, DeviceInfo, RecoveryImportErrorTag, SecretKey, deleteDevice, importRecoveryDevice, saveDevice } from '@/parsec';
import { Information, InformationLevel, InformationManager, InformationManagerKey, PresentationMode } from '@/services/informationManager';
import { IonButton, IonCard, IonCardContent, IonCardTitle, IonIcon, IonTitle } from '@ionic/vue';
import { checkmarkCircle } from 'ionicons/icons';
import { Ref, inject, onMounted, ref } from 'vue';

enum ImportDevicePageState {
  Start = 'start',
  Password = 'password',
  Done = 'done',
}

const state = ref(ImportDevicePageState.Start);
const choosePasswordInput: Ref<typeof MsChoosePasswordInput | null> = ref(null);
const hiddenInput = ref();
const secretKey: Ref<SecretKey> = ref('');
// cspell:disable-next-line
const secretKeyPlaceholder = 'FH3H-N3DW-RUOO-A6Q7-...';
const changeButtonIsEnabled = asyncComputed(async (): Promise<boolean> => {
  return choosePasswordInput.value && (await choosePasswordInput.value.areFieldsCorrect());
});
const recoveryFile: Ref<File | null> = ref(null);
const newDeviceInfo: Ref<DeviceInfo | null> = ref(null);
const isSecretKeyValid = ref(false);
const informationManager: InformationManager = inject(InformationManagerKey)!;

const emits = defineEmits<{
  (e: 'organizationSelected', device: AvailableDevice): void;
}>();

const props = defineProps<{
  device: AvailableDevice;
}>();

onMounted(() => {
  hiddenInput.value.addEventListener('change', onInputChange);
});

async function onInputChange(_event: Event): Promise<void> {
  if (hiddenInput.value.files.length === 1) {
    recoveryFile.value = hiddenInput.value.files[0];
  }
}

async function importButtonClick(): Promise<void> {
  hiddenInput.value.click();
}

async function checkSecretKeyValidity(): Promise<void> {
  isSecretKeyValid.value = (await secretKeyValidator(secretKey.value)).validity === Validity.Valid;
}

async function goToPasswordChange(): Promise<void> {
  if (!recoveryFile.value) {
    return;
  }
  const result = await importRecoveryDevice(props.device.deviceLabel, recoveryFile.value, secretKey.value);
  if (result.ok) {
    newDeviceInfo.value = result.value;
    state.value = ImportDevicePageState.Password;
  } else {
    const notificationInfo = { message: '', level: InformationLevel.Error };

    switch (result.error.tag) {
      case RecoveryImportErrorTag.KeyError:
        notificationInfo.message = 'ImportRecoveryDevicePage.errors.keyErrorMessage';
        break;
      case RecoveryImportErrorTag.RecoveryFileError:
        notificationInfo.message = 'ImportRecoveryDevicePage.errors.fileErrorMessage';
        break;
      case RecoveryImportErrorTag.Internal:
        notificationInfo.message = 'ImportRecoveryDevicePage.errors.internalErrorMessage';
        break;
    }
    informationManager.present(new Information(notificationInfo), PresentationMode.Toast);
  }
}

async function createNewDevice(): Promise<void> {
  // Check matching and valid passwords
  if (!choosePasswordInput.value || !(await choosePasswordInput.value.areFieldsCorrect())) {
    informationManager.present(
      new Information({
        message: 'ImportRecoveryDevicePage.errors.passwordErrorMessage',
        level: InformationLevel.Error,
      }),
      PresentationMode.Toast,
    );
    return;
  }
  // Check new device info exists
  if (!newDeviceInfo.value) {
    informationManager.present(
      new Information({
        message: 'ImportRecoveryDevicePage.errors.internalErrorMessage',
        level: InformationLevel.Error,
      }),
      PresentationMode.Toast,
    );
    return;
  }
  // Save new device with password
  if (!(await saveDevice(newDeviceInfo.value, 'newPassword')).ok) {
    informationManager.present(
      new Information({
        message: 'ImportRecoveryDevicePage.errors.saveDeviceErrorMessage',
        level: InformationLevel.Error,
      }),
      PresentationMode.Toast,
    );
    return;
  }
  // Delete previous device
  await deleteDevice(props.device);

  state.value = ImportDevicePageState.Done;
}

async function onLoginClick(): Promise<void> {
  emits('organizationSelected', props.device);
}
</script>

<style lang="scss" scoped>
.recovery-content {
  height: 100%;
  width: 60vw;
  max-width: var(--parsec-max-forgotten-pwd-width);
  display: flex;
  margin: 0 auto;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.recovery-header {
  &__title {
    color: var(--parsec-color-light-secondary-white);
  }
}

.recovery-card {
  height: auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 2rem;
  margin: 0;
  border-radius: var(--parsec-radius-12);
  box-shadow: var(--parsec-shadow-light);
  background: var(--parsec-color-light-secondary-white);
}

.card-container {
  display: flex;
  flex-direction: column;
  padding: 0;
  gap: 2rem;

  .recovery-list {
    display: flex;
    flex-direction: column;
    gap: 2rem;

    &-item {
      border-radius: var(--parsec-radius-8);
      width: 100%;
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;

      &__title {
        color: var(--parsec-color-light-primary-700);
        display: flex;
        align-items: center;
        gap: 0.5rem;

        .number {
          display: flex;
          justify-content: center;
          align-items: center;
          border-radius: var(--parsec-radius-32);
          width: 1.25rem;
          height: 1.25rem;
          color: var(--parsec-color-light-secondary-white);
          background: var(--parsec-color-light-primary-700);
        }
      }

      &__button {
        display: flex;
        align-items: center;
        gap: 1rem;
        color: var(--parsec-color-light-secondary-grey);

        .file-added {
          color: var(--parsec-color-light-secondary-text);

          &:hover {
            cursor: pointer;
            text-decoration: underline;
          }
        }

        ion-button {
          margin: 0;
        }
        ion-icon {
          font-size: 1.25rem;
          color: var(--parsec-color-light-success-500);
        }
      }

      &__input {
        width: 100%;
      }

      &.disabled {
        opacity: 0.3;
        pointer-events: none;
        user-select: none;
      }
    }
  }

  .recovery-divider {
    width: 100%;
    height: 1px;
    background-color: var(--parsec-color-light-secondary-medium);
  }
}

.validate-button,
.next-button {
  display: flex;
  width: fit-content;
  margin-left: auto;
}

.success-card {
  &__title {
    color: var(--parsec-color-light-primary-700);
    margin-bottom: 1.5rem;
  }

  &__button {
    margin-top: 2.5rem;
    display: flex;
    width: fit-content;
    margin-left: auto;
  }
}
</style>
