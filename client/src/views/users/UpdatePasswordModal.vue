<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page
    class="modal-stepper"
    :class="ChangePasswordStep[pageStep]"
  >
    <!-- close button -->
    <ion-buttons
      slot="end"
      class="closeBtn-container"
    >
      <ion-button
        slot="icon-only"
        @click="cancel()"
        class="closeBtn"
      >
        <ion-icon
          :icon="close"
          size="large"
          class="closeBtn__icon"
        />
      </ion-button>
    </ion-buttons>

    <!-- modal content -->
    <div class="modal">
      <ion-header class="modal-header">
        <ion-title class="modal-header__title title-h2">
          {{ $msTranslate(getTitle()) }}
        </ion-title>
      </ion-header>

      <div class="modal-content inner-content">
        <div
          v-show="pageStep === ChangePasswordStep.OldPassword"
          class="step"
        >
          <ms-password-input
            v-model="oldPassword"
            @change="updateError"
            :label="'Password.currentPassword'"
            @on-enter-keyup="nextStep()"
            :password-is-invalid="passwordIsInvalid"
            :error-message="errorMessage"
            ref="currentPasswordInput"
          />
        </div>
        <div
          v-show="pageStep === ChangePasswordStep.NewPassword"
          class="step"
        >
          <ms-choose-password-input
            :password-label="'Password.newPassword'"
            ref="choosePasswordInput"
          />
        </div>
      </div>

      <ion-footer class="modal-footer">
        <ion-buttons
          slot="primary"
          class="modal-footer-buttons"
        >
          <ion-button
            fill="clear"
            size="default"
            @click="cancel"
          >
            {{ $msTranslate('MyProfilePage.cancelButton') }}
          </ion-button>
          <ion-button
            fill="solid"
            size="default"
            id="next-button"
            @click="nextStep"
            :disabled="!canGoForward"
          >
            {{ $msTranslate(getNextButtonText()) }}
          </ion-button>
        </ion-buttons>
      </ion-footer>
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { MsChoosePasswordInput, MsModalResult, MsPasswordInput, asyncComputed } from 'megashark-lib';
import {
  AccessStrategy,
  AvailableDevice,
  ClientChangeAuthenticationErrorTag,
  SaveStrategy,
  getCurrentAvailableDevice,
  changePassword as parsecChangePassword,
} from '@/parsec';
import { Information, InformationLevel, InformationManager, PresentationMode } from '@/services/informationManager';
import { Translatable } from 'megashark-lib';
import { IonButton, IonButtons, IonFooter, IonHeader, IonIcon, IonPage, IonTitle, modalController } from '@ionic/vue';
import { close } from 'ionicons/icons';
import { Ref, onMounted, ref } from 'vue';

enum ChangePasswordStep {
  OldPassword,
  NewPassword,
}

const props = defineProps<{
  informationManager: InformationManager;
}>();

const currentDevice: Ref<AvailableDevice | null> = ref(null);
const pageStep = ref(ChangePasswordStep.OldPassword);
const choosePasswordInput = ref();
const oldPassword = ref('');
const errorMessage: Ref<Translatable> = ref('');
const passwordIsInvalid = ref(false);
const currentPasswordInput = ref();

onMounted(async () => {
  await currentPasswordInput.value.setFocus();
  const deviceResult = await getCurrentAvailableDevice();
  currentDevice.value = deviceResult.ok ? deviceResult.value : null;

  if (!currentDevice.value) {
    props.informationManager.present(
      new Information({
        message: 'MyProfilePage.errors.cannotChangePassword',
        level: InformationLevel.Error,
      }),
      PresentationMode.Toast,
    );
    await cancel();
  }
});

async function nextStep(): Promise<void> {
  if (pageStep.value === ChangePasswordStep.OldPassword) {
    pageStep.value = ChangePasswordStep.NewPassword;
  } else if (pageStep.value === ChangePasswordStep.NewPassword) {
    await changePassword();
  }
}

const canGoForward = asyncComputed(async () => {
  if (!currentDevice.value) {
    return false;
  }

  if (pageStep.value === ChangePasswordStep.OldPassword && oldPassword.value.length > 0) {
    return true;
  } else if (pageStep.value === ChangePasswordStep.NewPassword && (await choosePasswordInput.value.areFieldsCorrect())) {
    return true;
  }
  return false;
});

async function changePassword(): Promise<void> {
  if (!currentDevice.value || !choosePasswordInput.value) {
    return;
  }
  const result = await parsecChangePassword(
    AccessStrategy.usePassword(currentDevice.value, oldPassword.value),
    SaveStrategy.usePassword(choosePasswordInput.value.password),
  );

  if (result.ok) {
    props.informationManager.present(
      new Information({
        message: 'MyProfilePage.passwordUpdated',
        level: InformationLevel.Success,
      }),
      PresentationMode.Toast,
    );
    await modalController.dismiss();
  } else {
    switch (result.error.tag) {
      case ClientChangeAuthenticationErrorTag.DecryptionFailed: {
        pageStep.value = ChangePasswordStep.OldPassword;
        passwordIsInvalid.value = true;
        errorMessage.value = 'MyProfilePage.errors.wrongPassword';
        break;
      }
      default:
        props.informationManager.present(
          new Information({
            message: 'MyProfilePage.errors.cannotChangePassword',
            level: InformationLevel.Error,
          }),
          PresentationMode.Toast,
        );
    }
  }
}

function updateError(): void {
  passwordIsInvalid.value = false;
  errorMessage.value = '';
}

function getTitle(): string {
  switch (pageStep.value) {
    case ChangePasswordStep.OldPassword:
      return 'MyProfilePage.titleActualPassword';
    case ChangePasswordStep.NewPassword:
      return 'MyProfilePage.titleNewPassword';
    default:
      return '';
  }
}

async function cancel(): Promise<boolean> {
  return modalController.dismiss(null, MsModalResult.Cancel);
}

function getNextButtonText(): string {
  switch (pageStep.value) {
    case ChangePasswordStep.OldPassword:
      return 'MyProfilePage.nextButton';
    case ChangePasswordStep.NewPassword:
      return 'MyProfilePage.changePasswordButton';
    default:
      return '';
  }
}
</script>

<style scoped lang="scss"></style>
