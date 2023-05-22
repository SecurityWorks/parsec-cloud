<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS -->

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <!-- contextual menu -->
      <ion-item-divider class="workspace-toolbar ion-margin-bottom secondary">
        <button-option
          :button-label="$t('WorkspacesPage.createWorkspace')"
          :icon="addCircle"
          @click="openCreateWorkspaceModal()"
        />
        <div class="button-view">
          <ms-select
            id="filter-select"
            :options="msSelectOptions"
            default-option="name"
            @change="onMsSelectChange($event)"
          />
          <!-- grid -->
          <ion-button
            fill="clear"
            id="grid-view"
            :disabled="!listView"
            @click="listView = !listView"
          >
            <ion-icon
              :icon="grid"
            />
            <span v-if="!listView">
              {{ $t('WorkspacesPage.viewDisplay.grid') }}
            </span>
          </ion-button>
          <!-- list -->
          <ion-button
            fill="clear"
            id="list-view"
            :disabled="listView"
            @click="listView = !listView"
          >
            <ion-icon
              :icon="list"
            />
            <span v-if="listView">
              {{ $t('WorkspacesPage.viewDisplay.list') }}
            </span>
          </ion-button>
        </div>
      </ion-item-divider>
      <!-- workspaces -->
      <div class="workspaces-container">
        <div v-if="listView">
          <ion-list>
            <ion-list-header
              class="workspace-list-header"
              lines="full"
            >
              <ion-label>{{ $t('WorkspacesPage.listDisplayTitles.name') }}</ion-label>
              <ion-label>{{ $t('WorkspacesPage.listDisplayTitles.role') }}</ion-label>
              <ion-label>{{ $t('WorkspacesPage.listDisplayTitles.sharedWith') }}</ion-label>
              <ion-label>{{ $t('WorkspacesPage.listDisplayTitles.lastUpdate') }}</ion-label>
              <ion-label>{{ $t('WorkspacesPage.listDisplayTitles.size') }}</ion-label>
            </ion-list-header>
            <workspace-list-item
              v-for="workspace in filteredWorkspaces"
              :key="workspace.id"
              :workspace="workspace"
              @click="onWorkspaceClick"
              @menu-click="openWorkspaceContextMenu"
              @share-click="onWorkspaceShareClick"
            />
          </ion-list>
        </div>
        <div
          v-else
          class="workspaces-grid-container"
        >
          <ion-item
            class="workspaces-list-grid"
            v-for="workspace in filteredWorkspaces"
            :key="workspace.id"
          >
            <workspace-card
              :workspace="workspace"
              @click="onWorkspaceClick"
              @menu-click="openWorkspaceContextMenu"
              @share-click="onWorkspaceShareClick"
            />
          </ion-item>
        </div>
      </div>
      <div class="workspaces-footer">
        {{ $t('WorkspacesPage.itemCount', { count: workspaceList.length }, workspaceList.length) }}
      </div>
      <ion-fab
        v-if="isPlatform('mobile')"
        vertical="bottom"
        horizontal="end"
        slot="fixed"
      >
        <ion-fab-button @click="openCreateWorkspaceModal()">
          <ion-icon :icon="addCircle" />
        </ion-fab-button>
      </ion-fab>
    </ion-content>
  </ion-page>
</template>

<script setup lang = "ts" >
import {
  IonLabel,
  IonButton,
  IonIcon,
  IonPage,
  IonItemDivider,
  IonContent,
  popoverController,
  isPlatform,
  IonFab,
  IonFabButton,
  IonGrid,
  IonCol,
  IonRow,
  modalController,
  IonList,
  IonListHeader,
  IonItem
} from '@ionic/vue';

import {
  addCircle, grid, list
} from 'ionicons/icons';
import WorkspaceCard from '@/components/WorkspaceCard.vue';
import WorkspaceListItem from '@/components/WorkspaceListItem.vue';
import { MockWorkspace, getMockWorkspaces } from '@/common/mocks';
import WorkspaceContextMenu from '@/components/WorkspaceContextMenu.vue';
import { WorkspaceAction } from '@/components/WorkspaceContextMenu.vue';
import CreateWorkspaceModal from '@/components/CreateWorkspaceModal.vue';
import WorkspaceShareModal from '@/components/WorkspaceShareModal.vue';
import MsSelect from '@/components/MsSelect.vue';
import ButtonOption from '@/components/ButtonOption.vue';
import { MsSelectChangeEvent, MsSelectOption } from '@/components/MsSelectOption';
import { useI18n } from 'vue-i18n';
import { ref, Ref, onMounted, computed } from 'vue';

const { t } = useI18n();
const listView = ref(false);
const sortBy = ref('name');
const workspaceList: Ref<MockWorkspace[]> = ref([]);

onMounted(async (): Promise<void> => {
  workspaceList.value = await getMockWorkspaces();
});

const filteredWorkspaces = computed(() => {
  // Copy to avoid updating the workspaceList itself
  return Array.from(workspaceList.value).sort((a: MockWorkspace, b: MockWorkspace) => {
    if (sortBy.value === 'name') {
      return a.name.localeCompare(b.name);
    } else if (sortBy.value === 'size') {
      return a.size - b.size;
    } else if (sortBy.value === 'lastUpdated') {
      return b.lastUpdate.diff(a.lastUpdate).milliseconds;
    }
    return 0;
  });
});

const msSelectOptions: MsSelectOption[] = [
  { label: t('WorkspacesPage.sort.sortByName'), key: 'name' },
  { label: t('WorkspacesPage.sort.sortBySize'), key: 'size' },
  { label: t('WorkspacesPage.sort.sortByLastUpdated'), key: 'lastUpdated' }
];

function onMsSelectChange(event: MsSelectChangeEvent): void {
  sortBy.value = event.option.key;
}

async function openCreateWorkspaceModal(): Promise<void> {
  const modal = await modalController.create({
    component: CreateWorkspaceModal,
    cssClass: 'one-line-modal'
  });
  modal.present();

  const { data, role } = await modal.onWillDismiss();

  if (role === 'confirm') {
    console.log(data);
  }
}

function onWorkspaceClick(_: Event, workspace: MockWorkspace): void {
  console.log('Workspace Clicked!', workspace.name);
}

function onWorkspaceShareClick(_: Event, workspace: MockWorkspace): void {
  console.log('Share workspace Clicked!', workspace.name);
}

async function openWorkspaceContextMenu(event: Event, workspace: MockWorkspace): Promise<void> {
  const popover = await popoverController
    .create({
      component: WorkspaceContextMenu,
      event: event,
      translucent: true,
      showBackdrop: false,
      dismissOnSelect: true,
      reference: 'event'
    });
  await popover.present();

  const { data } = await popover.onDidDismiss();
  if (data !== undefined) {
    console.log(data.action);
    /*
    Keeping the comment here just to show how to check
    what action was selected.

    if (data.action === WorkspaceAction.Rename) {
      console.log('Rename!');
    }
    */
  }
}

async function openWorkspaceShareModal(): Promise<void> {
  const modal = await modalController.create({
    component: WorkspaceShareModal
  });
  modal.present();

  const { data, role } = await modal.onWillDismiss();

  if (role === 'confirm') {
    console.log(data);
  }
}
</script>

<style lang="scss" scoped>

.workspaces-container {
  margin: 2em;
  background-color: white;
}

.workspace-list-header {
  color: var(--parsec-color-light-secondary-grey);
  font-weight: 600;
}

.workspaces-footer {
  width: 100%;
  left: 0;
  position: fixed;
  bottom: 0;
  text-align: center;
  font-weight: 600;
  color: var(--parsec-color-light-secondary-text);
  margin-bottom: 2em;
}
.workspaces-grid-container {
  // grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  display: flex;
  flex-wrap: wrap;
  gap: 1.5em;
  overflow-y: auto;
}

.workspace-toolbar {
  padding: 1em 2em;
  height: 6em;
  background-color: var(--parsec-color-light-secondary-background);
  border-top: 1px solid var(--parsec-color-light-secondary-light);
}

.button-view {
  margin-left: auto;
}

.add-workspace-button {
  color: var(--parsec-color-light-secondary-grey);
}

</style>
