<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <div class="container">
    <ion-avatar
      class="avatar person-avatar"
      v-for="person in people.slice(0, maxDisplay)"
      :key="person"
    >
      {{ person.substring(0, 2) }}
    </ion-avatar>
    <ion-avatar
      class="avatar extra-avatar"
      v-if="people.length > maxDisplay"
    >
      + {{ people.length - maxDisplay }}
    </ion-avatar>
  </div>
</template>

<script setup lang="ts">
import { IonAvatar } from '@ionic/vue';

defineProps<{
  people: string[],
  maxDisplay: number
}>();
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  flex-wrap: nowrap;
}

.avatar {
  text-align: center;
  padding-top: 0.6em;
  font-size: 1.1em;
  font-weight: bold;
  text-transform: uppercase;
  margin-left: -0.6em;
  height: 2.5em;
  width: 2.5em;
  border: 1px solid #FEFEFE;
}

.person-avatar {
  background-color: #E8E5FF;
  color: #9747FF;
}

.extra-avatar {
  background-color: var(--parsec-color-light-secondary-background);
  color: var(--parsec-color-light-secondary-grey);
}
</style>
