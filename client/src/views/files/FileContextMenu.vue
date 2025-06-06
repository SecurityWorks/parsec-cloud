<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-content id="file-context-menu">
    <ion-list class="menu-list">
      <ion-item-group class="list-group">
        <ion-item class="list-group-title button-small">
          <ion-label class="list-group-title__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.titleManage') }}
          </ion-label>
        </ion-item>
        <ion-item
          button
          v-if="!multipleFiles && role !== WorkspaceRole.Reader"
          @click="onClick(FileAction.Rename)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="pencil" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionRename') }}
          </ion-label>
        </ion-item>
        <ion-item
          button
          v-if="role !== WorkspaceRole.Reader"
          @click="onClick(FileAction.MoveTo)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="arrowRedo" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionMoveTo') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          v-if="role !== WorkspaceRole.Reader"
          @click="onClick(FileAction.MakeACopy)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="copy" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionMakeACopy') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          v-if="role !== WorkspaceRole.Reader"
          @click="onClick(FileAction.Delete)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="trashBin" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionDelete') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          v-show="!multipleFiles && isFile && isDesktop()"
          @click="onClick(FileAction.Open)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="open" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionOpen') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          v-if="!multipleFiles && isDesktop()"
          @click="onClick(FileAction.SeeInExplorer)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="open" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionSeeInExplorer') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          @click="onClick(FileAction.ShowHistory)"
          class="ion-no-padding list-group-item"
          v-show="!multipleFiles && role !== WorkspaceRole.Reader"
        >
          <ion-icon :icon="time" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionHistory') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          v-if="!isDesktop() && isFile"
          @click="onClick(FileAction.Download)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="download" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionDownload') }}
          </ion-label>
        </ion-item>

        <ion-item
          button
          v-if="!multipleFiles"
          @click="onClick(FileAction.ShowDetails)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="informationCircle" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionDetails') }}
          </ion-label>
        </ion-item>
      </ion-item-group>
      <ion-item-group
        class="list-group"
        v-if="!multipleFiles"
      >
        <ion-item class="list-group-title button-small">
          <ion-label class="list-group-title__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.titleCollaboration') }}
          </ion-label>
        </ion-item>
        <ion-item
          button
          v-if="!multipleFiles"
          @click="onClick(FileAction.CopyLink)"
          class="ion-no-padding list-group-item"
        >
          <ion-icon :icon="link" />
          <ion-label class="body list-group-item__label">
            {{ $msTranslate('FoldersPage.fileContextMenu.actionCopyLink') }}
          </ion-label>
        </ion-item>
      </ion-item-group>
    </ion-list>
  </ion-content>
</template>

<script setup lang="ts">
import { isDesktop, WorkspaceRole } from '@/parsec';
import { IonContent, IonIcon, IonItem, IonItemGroup, IonLabel, IonList, popoverController } from '@ionic/vue';
import { arrowRedo, copy, download, informationCircle, link, open, pencil, time, trashBin } from 'ionicons/icons';
import { FileAction } from '@/views/files/types';

defineProps<{
  role: WorkspaceRole;
  multipleFiles?: boolean;
  isFile: boolean;
}>();

async function onClick(action: FileAction): Promise<boolean> {
  return await popoverController.dismiss({ action: action });
}
</script>

<style lang="scss" scoped></style>
