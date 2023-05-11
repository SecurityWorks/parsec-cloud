<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <ion-content id="workspace-context-menu">
    <ion-list>
      <ion-item-group>
        <ion-item
          class="menu-title"
          lines="none"
          disabled
        >
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.titleOffline') }}</ion-label>
        </ion-item>
        <ion-item
          button
          @click="onClick(WorkspaceAction.MakeAvailableOffline)"
          class="menu-item"
          lines="full"
        >
          <ion-icon :icon="cloudy" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionOffline') }}</ion-label>
        </ion-item>
      </ion-item-group>

      <ion-item-group>
        <ion-item
          class="menu-title"
          lines="none"
          disabled
        >
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.titleManage') }}</ion-label>
        </ion-item>

        <ion-item
          button
          lines="none"
          @click="onClick(WorkspaceAction.Rename)"
          class="menu-item"
        >
          <ion-icon :icon="pencil" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionRename') }}</ion-label>
        </ion-item>

        <ion-item
          button
          lines="none"
          @click="onClick(WorkspaceAction.OpenInExplorer)"
          class="menu-item"
        >
          <ion-icon :icon="open" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionOpenInExplorer') }}</ion-label>
        </ion-item>

        <ion-item
          button
          lines="none"
          @click="onClick(WorkspaceAction.ShowHistory)"
          class="menu-item"
        >
          <ion-icon :icon="time" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionHistory') }}</ion-label>
        </ion-item>

        <ion-item
          button
          lines="none"
          @click="onClick(WorkspaceAction.Manage)"
          class="menu-item"
        >
          <ion-icon :icon="cog" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionManage') }}</ion-label>
        </ion-item>

        <ion-item
          button
          lines="full"
          @click="onClick(WorkspaceAction.ShowDetails)"
          class="menu-item"
        >
          <ion-icon :icon="informationCircle" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionDetails') }}</ion-label>
        </ion-item>
      </ion-item-group>

      <ion-item-group>
        <ion-item
          disabled
          lines="none"
          class="menu-title"
        >
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.titleCollaboration') }}</ion-label>
        </ion-item>
        <ion-item
          button
          lines="none"
          @click="onClick(WorkspaceAction.CopyLink)"
          class="menu-item"
        >
          <ion-icon :icon="link" />
          <ion-label>{{ $t('WorkspacesPage.workspaceContextMenu.actionCopyLink') }}</ion-label>
        </ion-item>
      </ion-item-group>
    </ion-list>
  </ion-content>
</template>

<script lang = "ts">
export enum WorkspaceAction {
  Rename,
  MakeAvailableOffline,
  CopyLink,
  ShowDetails,
  Manage,
  ShowHistory,
  OpenInExplorer
}
</script>

<script setup lang = "ts" >
import { IonContent, IonItem, IonLabel, IonList, popoverController, IonIcon, IonItemGroup } from '@ionic/vue';
import {
  cloudy,
  pencil,
  link,
  informationCircle,
  cog,
  time,
  open
} from 'ionicons/icons';

function onClick(action: WorkspaceAction): Promise<boolean> {
  return popoverController.dismiss({'action': action});
}
</script>

<style lang="scss" scoped>
#workspace-context-menu {
  background-color: var(--parsec-color-light-secondary-inverted-contrast);
}
.menu-title {
  color: var(--parsec-color-light-secondary-light);
  text-transform: uppercase;
}

.menu-item {
  color: var(--parsec-color-light-secondary-grey);
}

.menu-item > ion-icon {
  margin-right: 1em;
}

</style>
