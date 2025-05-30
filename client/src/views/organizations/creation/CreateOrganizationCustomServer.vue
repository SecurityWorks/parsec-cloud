<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page>
    <organization-name-and-server-page
      v-if="initialized"
      v-show="step === Steps.OrganizationNameAndServer"
      :class="step === Steps.OrganizationNameAndServer ? 'active' : ''"
      :organization-name="organizationName ?? ''"
      :server-addr="serverAddr ?? ''"
      :disable-server-addr-field="bootstrapLink !== undefined"
      :disable-organization-name-field="bootstrapLink !== undefined"
      @organization-name-and-server-chosen="onOrganizationNameAndServerChosen"
      @go-back-requested="$emit('backRequested')"
      @close-requested="$emit('closeRequested')"
      :hide-previous="bootstrapLink !== undefined"
    />
    <organization-user-information-page
      v-show="step === Steps.PersonalInformation"
      :class="step === Steps.PersonalInformation ? 'active' : ''"
      @user-information-filled="onUserInformationFilled"
      @close-requested="$emit('closeRequested')"
      @go-back-requested="onGoBackRequested"
    />
    <organization-authentication-page
      v-show="step === Steps.Authentication"
      :class="step === Steps.Authentication ? 'active' : ''"
      @authentication-chosen="onAuthenticationChosen"
      @close-requested="$emit('closeRequested')"
      @go-back-requested="onGoBackRequested"
    />
    <organization-summary-page
      v-show="step === Steps.Summary"
      :class="step === Steps.Summary ? 'active' : ''"
      v-if="email && name && saveStrategy && organizationName"
      :error="currentError"
      :email="email"
      :name="name"
      :save-strategy="saveStrategy.tag"
      :organization-name="organizationName"
      :server-type="ServerType.Custom"
      :can-edit-email="true"
      :can-edit-name="true"
      :can-edit-organization-name="props.bootstrapLink === undefined"
      :can-edit-server-address="props.bootstrapLink === undefined"
      :can-edit-save-strategy="true"
      @create-clicked="onCreateClicked"
      @update-email-clicked="onUpdatePersonalInformationClicked"
      @update-name-clicked="onUpdatePersonalInformationClicked"
      @update-organization-name-clicked="onUpdateOrganizationNameClicked"
      @update-server-address-clicked="onUpdateOrganizationNameClicked"
      @update-save-strategy-clicked="onUpdateSaveStrategyClicked"
      @close-requested="$emit('closeRequested')"
      @go-back-requested="onGoBackRequested"
    />
    <organization-creation-page
      v-show="step === Steps.Creation"
      :class="step === Steps.Creation ? 'active' : ''"
    />
    <organization-created-page
      v-show="step === Steps.Created"
      :class="step === Steps.Created ? 'active' : ''"
      v-if="organizationName"
      @go-clicked="onGoClicked"
      :organization-name="organizationName"
    />
  </ion-page>
</template>

<script setup lang="ts">
import { IonPage } from '@ionic/vue';
import { ref, onMounted, isProxy, toRaw } from 'vue';
import OrganizationNameAndServerPage from '@/views/organizations/creation/OrganizationNameAndServerPage.vue';
import {
  DeviceSaveStrategy,
  OrganizationID,
  ParsedParsecAddrTag,
  parseParsecAddr,
  createOrganization as parsecCreateOrganization,
  bootstrapOrganization as parsecBootstrapOrganization,
  Result,
  AvailableDevice,
  BootstrapOrganizationError,
  BootstrapOrganizationErrorTag,
} from '@/parsec';
import OrganizationUserInformationPage from '@/views/organizations/creation/OrganizationUserInformationPage.vue';
import OrganizationAuthenticationPage from '@/views/organizations/creation/OrganizationAuthenticationPage.vue';
import OrganizationSummaryPage from '@/views/organizations/creation/OrganizationSummaryPage.vue';
import { ServerType } from '@/services/parsecServers';
import { getDefaultDeviceName } from '@/common/device';
import { wait } from '@/parsec/internals';
import OrganizationCreationPage from '@/views/organizations/creation/OrganizationCreationPage.vue';
import OrganizationCreatedPage from '@/views/organizations/creation/OrganizationCreatedPage.vue';
import { Translatable } from 'megashark-lib';

enum Steps {
  OrganizationNameAndServer,
  PersonalInformation,
  Authentication,
  Summary,
  Creation,
  Created,
}

const props = defineProps<{
  bootstrapLink?: string;
}>();

const emits = defineEmits<{
  (e: 'closeRequested'): void;
  (e: 'backRequested'): void;
  (e: 'organizationCreated', organizationName: OrganizationID, device: AvailableDevice, saveStrategy: DeviceSaveStrategy): void;
}>();

const bootstrapLink = ref<string | undefined>(props.bootstrapLink);
const step = ref<Steps>(Steps.OrganizationNameAndServer);
const organizationName = ref<OrganizationID | undefined>(undefined);
const serverAddr = ref<string | undefined>(undefined);
const email = ref<string | undefined>(undefined);
const name = ref<string | undefined>(undefined);
const saveStrategy = ref<DeviceSaveStrategy | undefined>(undefined);
const currentError = ref<Translatable | undefined>(undefined);
const availableDevice = ref<AvailableDevice | undefined>(undefined);
const initialized = ref(false);

onMounted(async () => {
  if (bootstrapLink.value) {
    const result = await parseParsecAddr(bootstrapLink.value);
    if (result.ok && result.value.tag === ParsedParsecAddrTag.OrganizationBootstrap) {
      organizationName.value = result.value.organizationId;
      serverAddr.value = `parsec3://${result.value.hostname}:${result.value.port}`;
    }
  }
  initialized.value = true;
});

async function onOrganizationNameAndServerChosen(chosenOrganizationName: OrganizationID, chosenServerAddr: string): Promise<void> {
  if (!props.bootstrapLink) {
    organizationName.value = chosenOrganizationName;
    serverAddr.value = chosenServerAddr;
  }

  step.value = Steps.PersonalInformation;
}

async function onUserInformationFilled(chosenName: string, chosenEmail: string): Promise<void> {
  email.value = chosenEmail;
  name.value = chosenName;
  step.value = Steps.Authentication;
}

async function onAuthenticationChosen(chosenSaveStrategy: DeviceSaveStrategy): Promise<void> {
  currentError.value = undefined;
  saveStrategy.value = chosenSaveStrategy;
  step.value = Steps.Summary;
}

async function createOrganization(): Promise<Result<AvailableDevice, BootstrapOrganizationError>> {
  if (!name.value || !email.value || !serverAddr.value || !organizationName.value || !saveStrategy.value) {
    return { ok: false, error: { tag: BootstrapOrganizationErrorTag.Internal, error: 'Missing data' } };
  }

  const result = await parsecCreateOrganization(
    serverAddr.value,
    organizationName.value,
    name.value,
    email.value,
    getDefaultDeviceName(),
    isProxy(saveStrategy.value) ? toRaw(saveStrategy.value) : saveStrategy.value,
  );
  return result;
}

async function bootstrapOrganization(): Promise<Result<AvailableDevice, BootstrapOrganizationError>> {
  if (!name.value || !email.value || !saveStrategy.value || !bootstrapLink.value) {
    return { ok: false, error: { tag: BootstrapOrganizationErrorTag.Internal, error: 'Missing data' } };
  }
  const result = await parsecBootstrapOrganization(
    bootstrapLink.value,
    name.value,
    email.value,
    getDefaultDeviceName(),
    isProxy(saveStrategy.value) ? toRaw(saveStrategy.value) : saveStrategy.value,
  );
  return result;
}

async function onCreateClicked(): Promise<void> {
  if (!organizationName.value || !serverAddr.value || !email.value || !name.value || !saveStrategy.value) {
    window.electronAPI.log('error', 'OrganizationCreation: missing data at the creation step, should not happen');
    return;
  }

  step.value = Steps.Creation;

  const startTime = new Date().valueOf();
  let result;
  if (bootstrapLink.value) {
    result = await bootstrapOrganization();
  } else {
    result = await createOrganization();
  }

  const endTime = new Date().valueOf();
  // If we're too fast, a weird blinking will occur. Add some artificial time.
  if (endTime - startTime < 1500) {
    await wait(1500 - (endTime - startTime));
  }

  if (!result.ok) {
    if (result.error.tag === BootstrapOrganizationErrorTag.AlreadyUsedToken) {
      currentError.value = 'CreateOrganization.errors.alreadyExists';
    } else if (result.error.tag === BootstrapOrganizationErrorTag.Offline) {
      currentError.value = 'CreateOrganization.errors.customOffline';
    } else if (result.error.tag === BootstrapOrganizationErrorTag.Internal && result.error.error.includes('Unsupported API version')) {
      currentError.value = 'CreateOrganization.errors.incompatibleServer';
    } else {
      currentError.value = { key: 'CreateOrganization.errors.generic', data: { reason: result.error.tag } };
    }
    step.value = Steps.Summary;
    window.electronAPI.log('error', `Failed to create organization: ${JSON.stringify(result.error)}`);
    return;
  }
  availableDevice.value = result.value;

  step.value = Steps.Created;
}

async function onGoClicked(): Promise<void> {
  if (!saveStrategy.value || !availableDevice.value || !organizationName.value) {
    window.electronAPI.log('error', 'OrganizationCreation: missing data at the end step, should not happen');
    return;
  }
  emits('organizationCreated', organizationName.value, availableDevice.value, saveStrategy.value);
}

async function onUpdatePersonalInformationClicked(): Promise<void> {
  step.value = Steps.PersonalInformation;
}

async function onUpdateOrganizationNameClicked(): Promise<void> {
  step.value = Steps.OrganizationNameAndServer;
}

async function onUpdateSaveStrategyClicked(): Promise<void> {
  step.value = Steps.Authentication;
}

async function onGoBackRequested(): Promise<void> {
  if (step.value === Steps.PersonalInformation) {
    step.value = Steps.OrganizationNameAndServer;
  } else if (step.value === Steps.Authentication) {
    step.value = Steps.PersonalInformation;
  } else if (step.value === Steps.Summary) {
    step.value = Steps.Authentication;
  } else {
    console.log(`Cannot go back from ${step.value}: should not happen`);
  }
}
</script>

<style scoped lang="scss"></style>
