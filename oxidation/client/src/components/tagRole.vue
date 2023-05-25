<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <ion-label class="label-role">
    <!-- if class role = owner add class : owner -->
    <ion-chip
      class="caption-caption tag"
      :class="role"
    >
      {{ role }}
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

.Owner {
  background-color: var(--parsec-color-light-primary-50);
  color: var(--parsec-color-light-primary-700);
}

.Manager {
  background-color: var(--parsec-color-tags-indigo100);
  color: var(--parsec-color-tags-indigo500);
}

.Contributor {
  background-color: var(--parsec-color-tags-green100);
  color: var(--parsec-color-tags-green500);
}

.Reader {
  background-color: var(--parsec-color-tags-orange100);
  color: var(--parsec-color-tags-orange500);
}
</style>
