<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <ion-item
    button
    class="workspace-list-item"
    lines="full"
    :detail="false"
    :class="{ selected: isSelected, 'no-padding-end': !isSelected }"
    @click="$emit('click', $event, workspace)"
  >
    <ion-avatar class="workspace-icon">
      <ion-icon
        class="main-icon"
        :icon="business"
      />
      <ion-icon
        class="cloud-overlay"
        :class="workspace.availableOffline ? 'cloud-overlay-ok' : 'cloud-overlay-ko'"
        :icon="workspace.availableOffline ? cloudDone : cloudOffline"
      />
    </ion-avatar>
    <ion-label class="label-name">
      {{ workspace.name }}
    </ion-label>
    <ion-label class="label-role">
      <ion-chip color="primary">
        {{ workspace.role }}
      </ion-chip>
    </ion-label>
    <avatar-group
      class="shared-group"
      :people="workspace.sharedWith"
      :max-display="2"
      @click.stop="$emit('shareClick', $event, workspace)"
    />
    <ion-label class="label-last-update">
      {{ timeSince(workspace.lastUpdate, '--', 'short') }}
    </ion-label>
    <ion-label class="label-size">
      {{ fileSize(workspace.size) }}
    </ion-label>
    <ion-button
      v-if="!isSelected"
      fill="clear"
      @click.stop="$emit('menuClick', $event, workspace)"
    >
      <ion-icon
        :icon="ellipsisHorizontal"
        slot="icon-only"
        class="workspace-menu-icon"
      />
    </ion-button>
  </ion-item>
</template>

<script setup lang="ts">
import {
  business,
  ellipsisHorizontal,
  cloudDone,
  cloudOffline
} from 'ionicons/icons';
import { ref, inject } from 'vue';
import { IonIcon, IonButton, IonItem, IonLabel, IonChip, IonAvatar } from '@ionic/vue';
import { formattersKey } from '../main';
import { MockWorkspace } from '@/common/mocks';
import AvatarGroup from '@/components/AvatarGroup.vue';

const isSelected = ref(false);

defineProps<{
  workspace: MockWorkspace
}>();

defineEmits<{
  (e: 'click', event: Event, workspace: MockWorkspace): void,
  (e: 'menuClick', event: Event, workspace: MockWorkspace): void,
  (e: 'shareClick', event: Event, workspace: MockWorkspace): void
}>();

const { timeSince, fileSize } = inject(formattersKey)!;

</script>

<style lang="scss" scoped>
.label-name {
  color: var(--parsec-color-light-secondary-text);
  margin-left: 1em;
}

.label-size, .label-shared-with, .label-last-update {
  color: var(--parsec-color-light-secondary-grey);
}

.workspace-icon {
  position: relative;
  padding: 5px;

  .main-icon {
    height: 100%;
    width: 100%;
    color: var(--parsec-color-light-secondary-text);
    margin-right: 1em;
  }

  .cloud-overlay {
    height: 40%;
    width: 40%;
    position: absolute;
    font-size: 1.5rem;
    bottom: -3px;
    left: 55%;
    padding: 2px;
    background: white;
    border-radius: 50%;
  }

  .cloud-overlay-ok {
    color: var(--parsec-color-light-primary-500);
  }

  .cloud-overlay-ko {
    color: var(--parsec-color-light-secondary-text);
  }
}

.shared-group {
  width: 10em;
}

.workspace-menu-icon {
  color: var(--parsec-color-light-secondary-grey);
}
</style>
