<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ms-modal
    :title="title"
    :subtitle="subtitle"
    :close-button="{ visible: true }"
    :cancel-button="{
      label: $t('PasswordInputModal.cancel'),
      disabled: false,
      onClick: cancel,
    }"
    :confirm-button="{
      label: okButtonText || $t('PasswordInputModal.ok'),
      disabled: password.length === 0,
      onClick: confirm,
    }"
  >
    <ms-password-input
      :label="inputLabel || ''"
      v-model="password"
      @on-enter-keyup="confirm()"
    />
  </ms-modal>
</template>

<script lang="ts">
import MsPasswordInputModal from '@/components/core/ms-modal/MsPasswordInputModal.vue';

export interface GetPasswordOptions {
  title: string;
  subtitle?: string;
  inputLabel?: string;
  okButtonText?: string;
}

export async function getPasswordFromUser(options: GetPasswordOptions): Promise<string | null> {
  const modal = await modalController.create({
    component: MsPasswordInputModal,
    canDismiss: true,
    cssClass: 'text-input-modal',
    componentProps: {
      title: options.title,
      subtitle: options.subtitle,
      inputLabel: options.inputLabel,
      okButtonText: options.okButtonText,
    },
  });
  await modal.present();
  const result = await modal.onWillDismiss();
  await modal.dismiss();
  return result.role === MsModalResult.Confirm ? result.data : null;
}
</script>

<script setup lang="ts">
import { modalController } from '@ionic/vue';
import { ref } from 'vue';
import MsModal from '@/components/core/ms-modal/MsModal.vue';
import MsPasswordInput from '@/components/core/ms-input/MsPasswordInput.vue';
import { MsModalResult } from '@/components/core/ms-types';

defineProps<GetPasswordOptions>();

const password = ref('');

async function confirm(): Promise<boolean> {
  if (password.value.length === 0) {
    return false;
  }
  return await modalController.dismiss(password.value, MsModalResult.Confirm);
}

function cancel(): Promise<boolean> {
  return modalController.dismiss(null, MsModalResult.Cancel);
}
</script>

<style scoped lang="scss">
.password-input-modal {
}
</style>
