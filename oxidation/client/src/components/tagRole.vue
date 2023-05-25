<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <ion-label class="label-role">
    <ion-chip
      class="caption-caption tag"
      :class="role"
    >
      {{ $t( "HomePage.WorkspacesPage.role" ) }}
    </ion-chip>
  </ion-label>
</template>

<script setup lang="ts">
import { IonChip, IonLabel } from '@ionic/vue';
import { defineProps } from 'vue';

defineProps<{
  role: string
}>();
</script>

<style scoped lang="scss">
.tag {
  padding: .25rem .5rem;
  height: auto;
}

.owner {
  background-color: var(--parsec-color-light-primary-50);
  color: var(--parsec-color-light-primary-700);
}

.manager {
  background-color: var(--parsec-color-tags-indigo100);
  color: var(--parsec-color-tags-indigo500);
}

.contributor {
  background-color: var(--parsec-color-tags-green100);
  color: var(--parsec-color-tags-green500);
}

.reader {
  background-color: var(--parsec-color-tags-orange100);
  color: var(--parsec-color-tags-orange500);
}
</style>
