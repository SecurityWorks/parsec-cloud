<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page
    id="page"
    :key="BmsAccessInstance.get().reloadKey"
  >
    <div
      class="resize-divider"
      ref="divider"
    />
    <ion-split-pane
      when="xs"
      content-id="main"
    >
      <ion-menu
        content-id="main"
        class="sidebar"
      >
        <client-area-sidebar
          v-if="loggedIn && currentOrganization"
          :current-page="currentPage"
          :organization="currentOrganization"
          @page-selected="switchPage"
          @organization-selected="onOrganizationSelected"
        />
      </ion-menu>

      <div
        class="ion-page"
        id="main"
      >
        <client-area-header
          v-if="loggedIn"
          :title="getTitleByPage()"
          @page-selected="switchPage"
        />
        <ion-content class="ion-padding">
          <div class="main-content">
            <div
              class="main-page"
              v-if="loggedIn && currentOrganization"
            >
              <billing-details-page
                v-if="currentPage === ClientAreaPages.BillingDetails"
                :organization="currentOrganization"
              />
              <contracts-page
                v-if="currentPage === ClientAreaPages.Contracts"
                :organization="currentOrganization"
              />
              <dashboard-page
                v-if="currentPage === ClientAreaPages.Dashboard"
                :organization="currentOrganization"
              />
              <invoices-page
                v-if="currentPage === ClientAreaPages.Invoices"
                :organization="currentOrganization"
              />
              <payment-methods-page
                v-if="currentPage === ClientAreaPages.PaymentMethods"
                :organization="currentOrganization"
              />
              <personal-data-page
                v-if="currentPage === ClientAreaPages.PersonalData"
                :organization="currentOrganization"
              />
              <statistics-page
                v-if="currentPage === ClientAreaPages.Statistics"
                :organization="currentOrganization"
              />
            </div>
          </div>
        </ion-content>
      </div>
    </ion-split-pane>
  </ion-page>
</template>

<script setup lang="ts">
import { IonPage, IonContent, IonSplitPane, IonMenu, GestureDetail, createGesture } from '@ionic/vue';
import ClientAreaHeader from '@/views/client-area/ClientAreaHeader.vue';
import ClientAreaSidebar from '@/views/client-area/ClientAreaSidebar.vue';
import { BmsAccessInstance, BmsOrganization, DataType } from '@/services/bms';
import { onMounted, onUnmounted, ref, watch } from 'vue';
import { ClientAreaPages } from '@/views/client-area/types';
import BillingDetailsPage from '@/views/client-area/BillingDetailsPage.vue';
import ContractsPage from '@/views/client-area/ContractsPage.vue';
import DashboardPage from '@/views/client-area/DashboardPage.vue';
import InvoicesPage from '@/views/client-area/InvoicesPage.vue';
import PaymentMethodsPage from '@/views/client-area/PaymentMethodsPage.vue';
import PersonalDataPage from '@/views/client-area/PersonalDataPage.vue';
import StatisticsPage from '@/views/client-area/StatisticsPage.vue';
import useSidebarMenu from '@/services/sidebarMenu';
import { Translatable } from 'megashark-lib';
import { ClientAreaQuery, getCurrentRouteQuery, navigateTo, Routes } from '@/router';

const { defaultWidth, initialWidth, computedWidth } = useSidebarMenu();
const organizations = ref<Array<BmsOrganization>>([]);
const divider = ref();
const currentPage = ref<ClientAreaPages>(ClientAreaPages.Dashboard);
const currentOrganization = ref<BmsOrganization | undefined>(undefined);
const sidebarWidthProperty = ref(`${defaultWidth}px`);
const loggedIn = ref(false);

const watchSidebarWidthCancel = watch(computedWidth, (value: number) => {
  sidebarWidthProperty.value = `${value}px`;
  // set toast offset
  setToastOffset(value);
});

function setToastOffset(width: number): void {
  document.documentElement.style.setProperty('--ms-toast-offset', `${width}px`);
}

onMounted(async () => {
  if (!BmsAccessInstance.get().isLoggedIn()) {
    loggedIn.value = await BmsAccessInstance.get().tryAutoLogin();
    if (!loggedIn.value) {
      await navigateTo(Routes.ClientAreaLogin);
      return;
    }
  } else {
    loggedIn.value = true;
  }
  const query = getCurrentRouteQuery<ClientAreaQuery>();
  const response = await BmsAccessInstance.get().listOrganizations();
  if (!response.isError && response.data && response.data.type === DataType.ListOrganizations) {
    organizations.value = response.data.organizations;
    if (organizations.value.length > 0) {
      if (query.organization) {
        currentOrganization.value = organizations.value.find((org) => org.bmsId === query.organization);
      }
      if (!currentOrganization.value) {
        currentOrganization.value = organizations.value[0];
      }
    }
    if (query.page) {
      currentPage.value = query.page as ClientAreaPages;
    }
  }

  setToastOffset(computedWidth.value);
  if (divider.value) {
    const gesture = createGesture({
      gestureName: 'resize-menu',
      el: divider.value,
      onEnd,
      onMove,
    });
    gesture.enable();
  }
});

onUnmounted(() => {
  watchSidebarWidthCancel();
  setToastOffset(0);
});

async function switchPage(page: ClientAreaPages): Promise<void> {
  currentPage.value = page;
  await navigateTo(Routes.ClientArea, { skipHandle: true, query: { organization: currentOrganization.value?.bmsId, page: page } });
}

function onMove(detail: GestureDetail): void {
  requestAnimationFrame(() => {
    let currentWidth = initialWidth.value + detail.deltaX;
    if (currentWidth >= 2 && currentWidth <= 500) {
      if (currentWidth <= 150) {
        currentWidth = 2;
      }
      computedWidth.value = currentWidth;
    }
  });
}

function onEnd(): void {
  initialWidth.value = computedWidth.value;
}

async function onOrganizationSelected(organization: BmsOrganization): Promise<void> {
  await navigateTo(Routes.ClientArea, { skipHandle: true, query: { organization: organization.bmsId } });
  currentOrganization.value = organization;
}

function getTitleByPage(): Translatable {
  switch (currentPage.value) {
    case ClientAreaPages.BillingDetails:
      return 'clientArea.header.titles.billingDetails';
    case ClientAreaPages.Contracts:
      return 'clientArea.header.titles.contracts';
    case ClientAreaPages.Dashboard:
      return 'clientArea.header.titles.dashboard';
    case ClientAreaPages.Invoices:
      return 'clientArea.header.titles.invoices';
    case ClientAreaPages.PaymentMethods:
      return 'clientArea.header.titles.paymentMethods';
    case ClientAreaPages.PersonalData:
      return 'clientArea.header.titles.personalData';
    case ClientAreaPages.Statistics:
      return 'clientArea.header.titles.statistics';
    default:
      return '';
  }
}
</script>

<style scoped lang="scss">
#page {
  position: relative;
  display: flex;
  height: 100%;
}

// -------- sidebar ------------
ion-split-pane {
  --side-min-width: var(--parsec-sidebar-menu-min-width);
  --side-max-width: var(--parsec-sidebar-menu-max-width);
  --side-width: v-bind(sidebarWidthProperty);
}

.resize-divider {
  width: 0.25rem;
  height: 100%;
  position: absolute;
  left: calc(v-bind(sidebarWidthProperty) - 2px);
  top: 0;
  z-index: 10000;
  cursor: ew-resize;
  display: flex;
  justify-content: center;

  &::after {
    content: '';
    width: 0.125rem;
    height: 100%;
    padding: 20rem 0;
  }

  &:hover::after,
  &:active::after {
    background: var(--parsec-color-light-secondary-soft-grey);
  }
}

.sidebar {
  --background: var(--parsec-color-light-secondary-background);
  border-right: 1px solid var(--parsec-color-light-secondary-disabled);
  user-select: none;

  &::part(container) {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
}

// -------- main content ------------
.main-content {
  width: -webkit-fill-available;
  height: 100%;
  font-size: 16px;
  display: flex;
  flex-direction: column;
}

.main-page {
  height: -webkit-fill-available;
  width: -webkit-fill-available;
}
</style>
