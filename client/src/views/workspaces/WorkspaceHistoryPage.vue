<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page>
    <ion-content
      class="global-content"
      :scroll-y="false"
    >
      <div class="history-container">
        <div class="head-content">
          <ion-text
            v-if="workspaceInfo && isLargeDisplay"
            class="title-h3 head-content__title"
          >
            <span class="body-lg">{{ $msTranslate('workspaceHistory.workspace') }}</span>
            {{ workspaceInfo.currentName }}
            <div v-show="querying">
              <ms-spinner />
            </div>
          </ion-text>
          <div class="date-selector">
            <ion-text
              class="date-selector__label body-sm"
              v-if="isLargeDisplay"
            >
              {{ $msTranslate('workspaceHistory.date') }}
            </ion-text>
            <ms-datetime-picker
              v-model="selectedDateTime"
              @update:model-value="onDateTimeChange"
              :min-date="minDate"
              :max-date="maxDate"
              :locale="I18n.getLocale()"
            />
          </div>
        </div>

        <div
          class="folder-container"
          ref="folderContainer"
          :class="{ 'folder-container--small': isSmallDisplay }"
        >
          <div class="folder-header">
            <div
              class="folder-header__navigation"
              v-if="!resultFromSearch"
            >
              <div ref="headerButtons">
                <ion-button
                  fill="clear"
                  @click="back()"
                  class="navigation-button"
                  id="navigation-back-button"
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
                  class="navigation-button"
                  id="navigation-forward-button"
                >
                  <ion-icon :icon="chevronForward" />
                </ion-button>
              </div>
              <header-breadcrumbs
                v-if="isLargeDisplay"
                :path-nodes="headerPath"
                @change="onPathChange"
                class="navigation-breadcrumb"
                :items-before-collapse="1"
                :items-after-collapse="1"
                :max-shown="2"
                :available-width="breadcrumbsWidth"
              />
            </div>
            <div
              class="folder-header__actions"
              ref="topbarRight"
            >
              <ion-button
                class="select-button body"
                @click="entries.selectAll(!allSelected)"
                v-if="isLargeDisplay && entries.entriesCount() > 0"
              >
                <span v-if="!allSelected">{{ $msTranslate('workspaceHistory.actions.selectAll') }}</span>
                <span v-else>{{ $msTranslate('workspaceHistory.actions.deselectAll') }}</span>
              </ion-button>
              <ms-search-input
                v-show="false"
                @change="onSearchChanged"
                :debounce="1000"
                :disabled="querying"
              />
              <ion-button
                id="restore-button"
                :disabled="!someSelected || querying"
                @click="onRestoreClicked"
              >
                {{ $msTranslate('workspaceHistory.actions.restore') }}
              </ion-button>
            </div>
          </div>
          <div
            class="current-folder button-medium"
            v-if="headerPath.length > 0 && isSmallDisplay"
          >
            <ms-image
              v-show="pathLength > 1"
              :image="Folder"
              class="current-folder__icon"
            />
            <ion-text class="current-folder__text">{{ `${headerPath[headerPath.length - 1].display}` }}</ion-text>
            <header-breadcrumbs
              v-if="pathLength > 1"
              :path-nodes="headerPath"
              @change="onPathChange"
              class="navigation-breadcrumb"
              :items-before-collapse="0"
              :items-after-collapse="0"
              :max-shown="0"
              :available-width="breadcrumbsWidth"
              :show-parent-node="false"
            />
            <ion-button
              class="select-button body"
              @click="entries.selectAll(!allSelected)"
            >
              <span v-if="!allSelected">{{ $msTranslate('workspaceHistory.actions.selectAll') }}</span>
              <span v-else>{{ $msTranslate('workspaceHistory.actions.deselectAll') }}</span>
            </ion-button>
          </div>
          <div class="folder-content">
            <div
              v-show="querying"
              class="folder-content__loading"
            >
              <ion-text class="subtitles-sm">{{ $msTranslate('workspaceHistory.loading') }}</ion-text>
            </div>
            <div
              v-show="!querying && entries.entriesCount() === 0 && !error"
              class="body-lg folder-content__empty"
            >
              {{ $msTranslate('workspaceHistory.empty') }}
            </div>
            <div
              class="body-lg folder-content__empty"
              v-show="!querying && error"
            >
              <ion-icon :icon="warning" />
              {{ $msTranslate(error) }}
            </div>
            <div
              v-show="!querying && entries.entriesCount() > 0"
              class="folder-list"
            >
              <ion-list class="folder-list-main ion-no-padding">
                <history-file-list-item
                  v-for="entry in entries.getEntries()"
                  :key="entry.id"
                  :entry="entry"
                  :show-checkbox="true"
                  @click="onEntryClicked(entry)"
                />
              </ion-list>
            </div>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { pxToRem } from '@/common/utils';
import { IonPage, IonList, IonIcon, IonButton, IonContent, IonText } from '@ionic/vue';
import { computed, onBeforeUnmount, onMounted, ref, Ref, inject, onUnmounted, watch, useTemplateRef } from 'vue';
import { FsPath, Path, getWorkspaceInfo, StartedWorkspaceInfo, WorkspaceHistory, EntryName } from '@/parsec';
import { MsSpinner, MsSearchInput, askQuestion, Answer, MsDatetimePicker, I18n, useWindowSize, MsImage, Folder } from 'megashark-lib';
import { DateTime } from 'luxon';
import { RouterPathNode } from '@/components/header/HeaderBreadcrumbs.vue';
import HeaderBreadcrumbs from '@/components/header/HeaderBreadcrumbs.vue';
import { WorkspaceHistoryEntryCollection, WorkspaceHistoryEntryModel, HistoryFileListItem } from '@/components/files';
import { chevronBack, chevronForward, home, warning } from 'ionicons/icons';
import { currentRouteIs, getCurrentRouteQuery, getDocumentPath, getWorkspaceHandle, Routes, watchRoute } from '@/router';
import { FileOperationManager, FileOperationManagerKey } from '@/services/fileOperationManager';
import { SortProperty } from '@/components/users';
import { InformationManager, InformationManagerKey } from '@/services/informationManager';
import { openPath } from '@/services/fileOpener';

const fileOperationManager: FileOperationManager = inject(FileOperationManagerKey)!;
const informationManager: InformationManager = inject(InformationManagerKey)!;
const workspaceInfo: Ref<StartedWorkspaceInfo | null> = ref(null);
const selectedDateTime = ref(DateTime.now().toJSDate());
const backStack: FsPath[] = [];
const forwardStack: FsPath[] = [];
const currentPath: Ref<FsPath> = ref('/');
const headerPath: Ref<RouterPathNode[]> = ref([]);
const pathLength = ref(0);
const breadcrumbsWidth = ref(0);
const folderContainerRef = useTemplateRef<HTMLDivElement>('folderContainer');
const headerButtonsRef = useTemplateRef<HTMLDivElement>('headerButtons');
const topbarRightRef = useTemplateRef<HTMLDivElement>('topbarRight');
const { windowWidth, isLargeDisplay, isSmallDisplay } = useWindowSize();

const entries: Ref<WorkspaceHistoryEntryCollection<WorkspaceHistoryEntryModel>> = ref(
  new WorkspaceHistoryEntryCollection<WorkspaceHistoryEntryModel>(),
);
const querying = ref(false);
let timeoutId: number | null = null;
const resultFromSearch = ref(false);
const error = ref('');
const selectEntry: Ref<EntryName> = ref('');
const minDate = ref(DateTime.now().toJSDate());
const maxDate = ref(DateTime.now().toJSDate());

const allSelected = computed(() => {
  return entries.value.selectedCount() === entries.value.entriesCount();
});

const someSelected = computed(() => {
  return entries.value.selectedCount() > 0;
});

const topbarWidthWatchCancel = watch([windowWidth, pathLength], () => {
  if (folderContainerRef.value?.clientWidth && headerButtonsRef.value?.offsetWidth && topbarRightRef.value?.offsetWidth) {
    breadcrumbsWidth.value =
      pxToRem(folderContainerRef.value?.clientWidth - headerButtonsRef.value?.offsetWidth - topbarRightRef.value?.offsetWidth) - 2;
  }
});

const cancelRouteWatch = watchRoute(async () => {
  if (!currentRouteIs(Routes.History)) {
    return;
  }
  await loadHistory();
});

async function loadHistory(): Promise<void> {
  const workspaceHandle = getWorkspaceHandle();
  if (workspaceHandle) {
    const infoResult = await getWorkspaceInfo(workspaceHandle);
    if (infoResult.ok) {
      workspaceInfo.value = infoResult.value;
    } else {
      console.error('Failed to retrieve workspace info');
    }
  } else {
    return;
  }
  currentPath.value = getDocumentPath() ?? '/';
  const query = getCurrentRouteQuery();
  if (query.selectFile) {
    selectEntry.value = query.selectFile;
  }

  await listCurrentPath();
}

onMounted(async () => {
  await loadHistory();
});

onBeforeUnmount(async () => {
  if (timeoutId !== null) {
    window.clearTimeout(timeoutId);
    timeoutId = null;
  }
});

onUnmounted(async () => {
  cancelRouteWatch();
  topbarWidthWatchCancel();
});

async function onDateTimeChange(): Promise<void> {
  await listCurrentPath();
}

async function listCurrentPath(): Promise<void> {
  if (!currentRouteIs(Routes.History)) {
    return;
  }
  if (!workspaceInfo.value) {
    return;
  }
  const history = new WorkspaceHistory(workspaceInfo.value.id);
  try {
    querying.value = true;
    const startResult = await history.start(DateTime.fromJSDate(selectedDateTime.value));
    if (!startResult.ok) {
      error.value = 'workspaceHistory.error';
      entries.value.clear();
      return;
    }
    minDate.value = history.getLowerBound().toJSDate();
    maxDate.value = history.getUpperBound().toJSDate();
    selectedDateTime.value = history.getCurrentTime().toJSDate();

    const statsResult = await history.entryStat(currentPath.value);

    if (!statsResult.ok) {
      error.value = 'workspaceHistory.error';
      entries.value.clear();
      return;
    }
    error.value = '';

    if (statsResult.value.isFile()) {
      // If the current path is set to a file, we instead set it to the parent dir
      currentPath.value = await Path.parent(currentPath.value);
    }

    const breadcrumbs = await Path.parse(currentPath.value);

    const result = await history.statFolderChildren(currentPath.value);
    if (result.ok) {
      const newEntries: WorkspaceHistoryEntryModel[] = [];
      for (const entry of result.value) {
        (entry as WorkspaceHistoryEntryModel).isSelected = Boolean(selectEntry.value && selectEntry.value === entry.name);
        newEntries.push(entry as WorkspaceHistoryEntryModel);
      }
      entries.value.replace(newEntries);
      entries.value.sort(SortProperty.Name as any, true);
    }

    let path = '/';
    headerPath.value = [];
    headerPath.value.push({
      id: 0,
      display: workspaceInfo.value.currentName,
      route: Routes.History,
      popoverIcon: home,
      query: { documentPath: path },
    });
    let id = 1;
    for (const breadcrumb of breadcrumbs) {
      path = await Path.join(path, breadcrumb);
      headerPath.value.push({
        id: id,
        display: breadcrumb === '/' ? '' : breadcrumb,
        route: Routes.History,
        query: { documentPath: path },
      });
      id += 1;
    }
    pathLength.value = headerPath.value.length;
  } finally {
    querying.value = false;
    if (history.isStarted()) {
      await history.stop();
    }
  }
}

async function forward(): Promise<void> {
  const forwardPath = forwardStack.pop();

  if (!forwardPath) {
    return;
  }
  backStack.push(currentPath.value);
  currentPath.value = forwardPath;
  selectEntry.value = '';
  await listCurrentPath();
}

async function back(): Promise<void> {
  const backPath = backStack.pop();

  if (!backPath) {
    return;
  }
  forwardStack.push(currentPath.value);
  currentPath.value = backPath;
  selectEntry.value = '';
  await listCurrentPath();
}

async function onPathChange(node: RouterPathNode): Promise<void> {
  forwardStack.splice(0, forwardStack.length);
  selectEntry.value = '';
  if (node.query && node.query.documentPath) {
    currentPath.value = node.query.documentPath;
    await listCurrentPath();
  }
}

async function onEntryClicked(entry: WorkspaceHistoryEntryModel): Promise<void> {
  if (entry.isFile()) {
    if (!workspaceInfo.value) {
      return;
    }

    await openPath(workspaceInfo.value.handle, entry.path, informationManager, {
      onlyViewers: true,
      atTime: DateTime.fromJSDate(selectedDateTime.value),
    });
  } else {
    backStack.push(currentPath.value);
    selectEntry.value = '';
    currentPath.value = await Path.join(currentPath.value, entry.name);
    await listCurrentPath();
  }
}

async function onSearchChanged(value: string): Promise<void> {
  // If querying, delay
  if (querying.value) {
    // Clearing the previous timeout
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
    // Add a timeout with the new value
    window.setTimeout(async () => {
      await onSearchChanged(value);
    }, 500);
    return;
  }

  if (!value) {
    await listCurrentPath();
    resultFromSearch.value = false;
  } else {
    await listCurrentPath();
    resultFromSearch.value = true;
  }
}

async function onRestoreClicked(): Promise<void> {
  const selectedEntries = entries.value.getSelectedEntries();

  if (selectedEntries.length === 0 || !workspaceInfo.value) {
    return;
  }
  const answer = await askQuestion(
    'workspaceHistory.restoreConfirmTitle',
    { key: 'workspaceHistory.restoreConfirmQuestion', count: selectedEntries.length },
    { yesText: 'workspaceHistory.actions.restore', noText: 'workspaceHistory.actions.cancel', yesIsDangerous: true },
  );
  if (answer === Answer.No) {
    return;
  }
  const dateTime = DateTime.fromJSDate(selectedDateTime.value);
  for (const entry of selectedEntries) {
    await fileOperationManager.restoreEntry(workspaceInfo.value.handle, workspaceInfo.value.id, entry.path, dateTime);
  }
  entries.value.selectAll(false);
}
</script>

<style scoped lang="scss">
.global-content {
  --background: var(--parsec-color-light-secondary-background);
}

.history-container {
  display: flex;
  flex-direction: column;
  height: 100%;

  @include ms.responsive-breakpoint('sm') {
    padding-top: 0.25rem;
  }
}

.head-content {
  display: flex;
  align-items: end;
  margin-inline: 2.5rem;
  justify-content: space-between;
  position: relative;

  @include ms.responsive-breakpoint('sm') {
    margin-inline: 1rem;
  }

  &__title {
    color: var(--parsec-color-light-secondary-text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-bottom: 0.25rem;

    span {
      color: var(--parsec-color-light-secondary-grey);
    }
  }

  .date-selector {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;

    @include ms.responsive-breakpoint('sm') {
      width: 100%;
    }

    &__label {
      color: var(--parsec-color-light-secondary-hard-grey);
    }
  }
}

.folder-content {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex-grow: 1;

  &__loading,
  &__empty {
    margin: 1rem;
    color: var(--parsec-color-light-secondary-hard-grey);
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 0.5rem;
  }
}

.folder-container {
  // multiple lines for cross-browser compatibility
  height: 100%;
  height: -webkit-fill-available;
  margin: 1.5rem 2.5rem;
  background: var(--parsec-color-light-secondary-white);
  border-radius: var(--parsec-radius-12);
  border: 1px solid var(--parsec-color-light-secondary-medium);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  @include ms.responsive-breakpoint('sm') {
    margin: 1rem;
  }

  .folder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.5rem 0.75rem 1rem;
    border-bottom: 1px solid var(--parsec-color-light-secondary-medium);

    &__navigation {
      display: flex;
      align-items: center;
      height: fit-content;

      .navigation-button {
        min-height: 1rem;

        &::part(native) {
          padding: 0.5rem;
        }
      }
    }

    @include ms.responsive-breakpoint('sm') {
      padding: 0.75rem;
      border-bottom: none;
      border-top: 1px solid var(--parsec-color-light-secondary-medium);
      order: 3;
    }

    &__actions {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    #restore-button {
      min-width: 6rem;
    }
  }

  .folder-content {
    @include ms.responsive-breakpoint('sm') {
      order: 2;
    }
  }

  .current-folder {
    color: var(--parsec-color-light-secondary-grey);
    background: var(--parsec-color-light-secondary-white);
    border-bottom: 1px solid var(--parsec-color-light-secondary-medium);
    padding: 0.5rem 1.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    overflow: hidden;

    @include ms.responsive-breakpoint('sm') {
      order: 1;
      padding: 0.25rem 1rem;
      flex-shrink: 0;
    }

    &__text {
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

  .select-button {
    color: var(--parsec-color-light-primary-500);
    cursor: pointer;
    margin-left: auto;
    font-size: 0.875rem;
    --background: transparent;
    --background-hover: var(--parsec-color-light-primary-50);

    @include ms.responsive-breakpoint('sm') {
      &::part(native) {
        padding: 0.25rem 0.5rem;
      }
    }
  }
}

.folder-list {
  display: flex;
  flex-direction: column;
  overflow: hidden;

  &-main {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
  }
}
</style>
