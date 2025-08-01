<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ms-modal
    :title="title"
    :close-button="{ visible: true }"
    :cancel-button="{
      label: 'TextInputModal.cancel',
      disabled: false,
      onClick: cancel,
    }"
    :confirm-button="{
      label: okButtonLabel || 'TextInputModal.moveHere',
      disabled: allowStartingPath ? false : selectedPath === startingPath,
      onClick: confirm,
    }"
  >
    <!-- :disabled="backStack.length === 0" -->
    <div
      class="navigation"
      ref="navigation"
    >
      <div ref="buttons">
        <div
          class="navigation-buttons"
          v-if="isLargeDisplay"
        >
          <ion-button
            fill="clear"
            @click="back()"
            class="navigation-back-button"
            :disabled="backStack.length === 0"
            :class="{ disabled: backStack.length === 0 }"
          >
            <ion-icon :icon="chevronBack" />
          </ion-button>
          <ion-button
            fill="clear"
            @click="forward()"
            :disabled="forwardStack.length === 0"
            :class="{ disabled: forwardStack.length === 0 }"
            class="navigation-forward-button"
          >
            <ion-icon :icon="chevronForward" />
          </ion-button>
        </div>
      </div>
      <header-breadcrumbs
        :path-nodes="headerPath"
        @change="onPathChange"
        class="navigation-breadcrumb"
        :items-before-collapse="1"
        :items-after-collapse="2"
        :available-width="breadcrumbsWidth"
      />
    </div>
    <ion-list class="folder-list">
      <ion-text
        class="current-folder button-medium"
        v-if="headerPath.length > 0 && pathLength > 1"
      >
        <ms-image
          :image="Folder"
          class="current-folder__icon"
        />
        <span class="current-folder__text">{{ `${headerPath[headerPath.length - 1].display}` }}</span>
      </ion-text>

      <ion-text
        class="folder-list__empty body"
        v-if="currentEntries.length === 0"
      >
        {{ $msTranslate('FoldersPage.copyMoveFolderNoElement') }}
      </ion-text>
      <div
        class="folder-container"
        v-if="currentEntries.length > 0"
      >
        <ion-item
          class="file-item"
          v-for="entry in currentEntries"
          :key="entry[0].id"
          :disabled="entry[1]"
          @click="enterFolder(entry[0])"
        >
          <div class="file-item-image">
            <ms-image
              :image="entry[0].isFile() ? getFileIcon(entry[0].name) : Folder"
              class="file-item-image__icon"
            />
          </div>
          <ion-label class="file-item__name cell">
            {{ entry[0].name }}
          </ion-label>
          <!-- last update -->
          <div
            class="file-lastUpdate"
            v-if="isLargeDisplay"
          >
            <ion-label class="label-last-update cell">
              {{ $msTranslate(formatTimeSince(entry[0].updated, '--', 'short')) }}
            </ion-label>
          </div>
        </ion-item>
      </div>
    </ion-list>
    <div
      class="navigation-buttons"
      v-if="isSmallDisplay"
    >
      <ion-button
        fill="clear"
        @click="back()"
        class="navigation-back-button"
        :disabled="backStack.length === 0"
        :class="{ disabled: backStack.length === 0 }"
      >
        <ion-icon :icon="chevronBack" />
      </ion-button>
      <ion-button
        fill="clear"
        @click="forward()"
        :disabled="forwardStack.length === 0"
        :class="{ disabled: forwardStack.length === 0 }"
        class="navigation-forward-button"
      >
        <ion-icon :icon="chevronForward" />
      </ion-button>
    </div>
  </ms-modal>
</template>

<script setup lang="ts">
import { getFileIcon } from '@/common/file';
import { pxToRem } from '@/common/utils';
import { Routes } from '@/router';
import { FolderSelectionOptions } from '@/components/files';
import { Folder, MsImage, MsModalResult, MsModal, formatTimeSince, useWindowSize } from 'megashark-lib';
import HeaderBreadcrumbs, { RouterPathNode } from '@/components/header/HeaderBreadcrumbs.vue';
import { EntryStat, FsPath, Path, StartedWorkspaceInfo, getWorkspaceInfo, statFolderChildren } from '@/parsec';
import { IonButton, IonText, IonIcon, IonItem, IonLabel, IonList, modalController } from '@ionic/vue';
import { chevronBack, chevronForward, home } from 'ionicons/icons';
import { Ref, onMounted, onUnmounted, ref, watch, useTemplateRef } from 'vue';

const props = defineProps<FolderSelectionOptions>();
const selectedPath: Ref<FsPath> = ref(props.startingPath);
const headerPath: Ref<RouterPathNode[]> = ref([]);
const pathLength = ref(0);
const currentEntries: Ref<[EntryStat, boolean][]> = ref([]);
const workspaceInfo: Ref<StartedWorkspaceInfo | null> = ref(null);
const backStack: FsPath[] = [];
const forwardStack: FsPath[] = [];
const breadcrumbsWidth = ref(0);
const navigationRef = useTemplateRef<HTMLDivElement>('navigation');
const buttonsRef = useTemplateRef<HTMLDivElement>('buttons');
const { windowWidth, isSmallDisplay, isLargeDisplay } = useWindowSize();

const topbarWidthWatchCancel = watch([windowWidth, pathLength], () => {
  if (navigationRef.value?.offsetWidth && buttonsRef.value?.offsetWidth) {
    breadcrumbsWidth.value = pxToRem(navigationRef.value.offsetWidth - buttonsRef.value.offsetWidth);
    if (isSmallDisplay.value) {
      breadcrumbsWidth.value += pathLength.value > 1 ? 2 : 1;
    }
  }
});

onMounted(async () => {
  const result = await getWorkspaceInfo(props.workspaceHandle);
  if (result.ok) {
    workspaceInfo.value = result.value;
  }
  await update();
});

onUnmounted(() => topbarWidthWatchCancel());

async function update(): Promise<void> {
  if (!workspaceInfo.value) {
    return;
  }
  const workspaceHandle = workspaceInfo.value.handle;
  const components = await Path.parse(selectedPath.value);

  const result = await statFolderChildren(workspaceHandle, selectedPath.value);
  if (result.ok) {
    const newEntries: [EntryStat, boolean][] = [];
    for (const entry of result.value
      .filter((entry) => !entry.isConfined())
      .sort((item1, item2) => Number(item1.isFile()) - Number(item2.isFile()))) {
      const isDisabled = await isEntryDisabled(entry);
      newEntries.push([entry, isDisabled]);
    }
    currentEntries.value = newEntries;
  }

  let path = '/';
  headerPath.value = [];
  headerPath.value.push({
    id: 0,
    display: workspaceInfo.value ? workspaceInfo.value.currentName : '',
    route: Routes.Documents,
    popoverIcon: home,
    query: { documentPath: path },
  });
  let id = 1;
  for (const comp of components) {
    path = await Path.join(path, comp);
    headerPath.value.push({
      id: id,
      display: comp === '/' ? '' : comp,
      route: Routes.Documents,
      query: { documentPath: path },
    });
    id += 1;
  }
  pathLength.value = headerPath.value.length;
}

async function isEntryDisabled(entry: EntryStat): Promise<boolean> {
  if (entry.isFile()) {
    return true;
  }
  for (const excludePath of props.excludePaths || []) {
    if (entry.path.startsWith(excludePath)) {
      return true;
    }
  }
  return false;
}

async function forward(): Promise<void> {
  const forwardPath = forwardStack.pop();

  if (!forwardPath) {
    return;
  }
  backStack.push(selectedPath.value);
  selectedPath.value = forwardPath;
  await update();
}

async function back(): Promise<void> {
  const backPath = backStack.pop();

  if (!backPath) {
    return;
  }
  forwardStack.push(selectedPath.value);
  selectedPath.value = backPath;
  await update();
}

async function onPathChange(node: RouterPathNode): Promise<void> {
  forwardStack.splice(0, forwardStack.length);
  if (node.query && node.query.documentPath) {
    selectedPath.value = node.query.documentPath;
    await update();
  }
}

async function enterFolder(entry: EntryStat): Promise<void> {
  if (entry.isFile()) {
    return;
  }
  backStack.push(selectedPath.value);
  selectedPath.value = await Path.join(selectedPath.value, entry.name);
  await update();
}

async function confirm(): Promise<boolean> {
  return await modalController.dismiss(selectedPath.value, MsModalResult.Confirm);
}

async function cancel(): Promise<boolean> {
  return modalController.dismiss(null, MsModalResult.Cancel);
}
</script>

<style scoped lang="scss">
.navigation {
  display: flex;
  margin-bottom: 1rem;

  @include ms.responsive-breakpoint('md') {
    border-bottom: none;
    overflow: visible;
  }

  .disabled {
    pointer-events: none;
    color: var(--parsec-color-light-secondary-light);
    opacity: 1;
  }

  &-buttons {
    display: flex;
    align-items: center;
    margin-right: 0.5rem;

    @include ms.responsive-breakpoint('sm') {
      position: absolute;
      bottom: 3.25rem;
      z-index: 10;

      ion-icon {
        font-size: 1.5rem;
      }
    }
  }
}

.folder-list {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: var(--parsec-color-light-secondary-background);
  border: 1px solid var(--parsec-color-light-secondary-premiere);
  height: -webkit-fill-available;
  border-radius: var(--parsec-radius-8);
  height: 100%;
  padding: 0;

  &__empty {
    align-self: center;
    text-align: center;
    color: var(--parsec-color-light-secondary-soft-text);
    display: flex;
    align-items: center;
    height: 100%;
  }

  .current-folder {
    color: var(--parsec-color-light-secondary-text);
    background: var(--parsec-color-light-secondary-white);
    border-bottom: 1px solid var(--parsec-color-light-secondary-medium);
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    overflow: hidden;

    &__text {
      flex-grow: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    &__icon {
      flex-shrink: 0;
      width: 1.25rem;
      height: 1.25rem;
    }
  }
}

.folder-container {
  overflow-y: auto;
  width: 100%;
  padding: 0.5rem;
}

.file-item {
  border-radius: var(--parsec-radius-6);
  --show-full-highlight: 0;
  --background: var(--parsec-color-light-secondary-background);
  --background-hover: var(--parsec-color-light-secondary-white);
  cursor: pointer;
  position: relative;
  overflow: visible;

  &::part(native) {
    --padding-start: 0px;
    padding: 0.125rem 0.75rem;
    border-radius: var(--parsec-radius-6);
  }

  &:not(:last-child):after {
    content: '';
    position: absolute;
    left: 3rem;
    width: calc(100% - 3rem);
    height: 1px;
    z-index: 10;
    background-color: var(--parsec-color-light-secondary-medium);
  }

  &:hover {
    color: var(--parsec-color-light-secondary-text);
    --background: var(--parsec-color-light-secondary-white);
  }

  &:focus,
  &:active {
    --background-focused: var(--parsec-color-light-primary-100);
    --background: var(--parsec-color-light-primary-100);
    --background-focused-opacity: 1;
    --border-width: 0;
  }

  &__name {
    color: var(--parsec-color-light-secondary-text);
    margin-left: 1rem;
  }

  &-image {
    width: 1.75rem;
    height: 1.75rem;
  }
}
</style>
