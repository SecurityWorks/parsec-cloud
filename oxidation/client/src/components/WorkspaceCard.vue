<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <div
    class="workspace-card"
    @click="$emit('click', $event, workspace)"
  >
    <ion-button
      fill="clear"
      class="button-open-menu"
      @click.stop="$emit('menuClick', $event, workspace)"
    >
      <ion-icon
        :icon="ellipsisHorizontal"
      />
    </ion-button>
    <div
      class="workspace-card-inner"
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

      <ion-item
        class="workspace-label"
      >
        <ion-label>
          {{ workspace.name }}
        </ion-label>
      </ion-item>

      <ion-item
        lines="full"
        class="workspace-time-since"
      >
        <ion-label>
          {{ $t('WorkspacesPage.Workspace.lastUpdate') }}
          <br />
          {{ timeSince(workspace.lastUpdate, '--', 'short') }}
        </ion-label>
      </ion-item>

      <ion-item class="workspace-info">
        <ion-label class="label-file-size">
          {{ fileSize(workspace.size) }}
        </ion-label>
        <avatar-group
          class="shared-group"
          :people="workspace.sharedWith"
          :max-display="2"
          @click.stop="$emit('shareClick', $event, workspace)"
        />
      </ion-item>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  business,
  ellipsisHorizontal,
  cloudDone,
  cloudOffline
} from 'ionicons/icons';
import { IonAvatar, IonIcon, IonButton, IonItem, IonLabel } from '@ionic/vue';
import { inject } from 'vue';
import { formattersKey } from '../main';
import { MockWorkspace } from '@/common/mocks';
import AvatarGroup from '@/components/AvatarGroup.vue';

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
.workspace-card {
  min-height: 15em;
  width: 15em;
  padding: 1em;
  cursor: pointer;
  text-align: center;
  background-color: var(--parsec-color-light-secondary-background);
  user-select: none;

  ion-avatar {
    color: var(--parsec-color-light-primary-900);
    display: flex;
    justify-content: center;
    align-items: center;
    margin: auto;
    width: 100%;
  }
}

.button-open-menu {
  color: var(--parsec-color-light-secondary-grey);
  text-align: right;
  position: relative;
  float: right;
}

.workspace-icon {
  position: relative;
  padding: 5px;

  .main-icon {
    height: 100%;
    width: 100%;
  }

  .cloud-overlay {
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

.workspace-label {
  color: var(--parsec-color-light-primary-900);
  background-color: var(--parsec-color-light-secondary-background);
  font-size: 18px;
  text-align: center;
}

.workspace-time-since {
  font-size: 14px;
  color: var(--parsec-color-light-secondary-grey);
  background-color: var(--parsec-color-light-secondary-background);
  text-align: center;
}

.workspace-info {
  font-size: 14px;
  color: var(--parsec-color-light-secondary-grey);
  background-color: var(--parsec-color-light-secondary-background);
}

/* No idea how to change the color of the ion-item */
.workspace-label::part(native), .workspace-info::part(native), .workspace-time-since::part(native) {
  background-color: var(--parsec-color-light-secondary-background);
}

.label-file-size {
  display: block;
  float: left;
}

.shared-group {
  float: right;
}
</style>
