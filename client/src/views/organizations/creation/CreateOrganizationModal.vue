<!-- Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS -->

<template>
  <ion-page class="modal-container">
    <div class="modal-content inner-content">
      <server-type-choice
        v-if="serverType === undefined"
        @server-chosen="onServerChosen"
        @close-requested="onCloseRequested"
      />
      <create-organization-saas
        v-if="serverType === ServerType.Saas"
        :bootstrap-link="bootstrapLink"
        :information-manager="informationManager"
        @close-requested="onCloseRequested"
        @organization-created="onOrganizationCreated"
        @back-requested="onBackToServerChoice"
      />
      <create-organization-custom-server
        v-if="serverType === ServerType.Custom"
        :bootstrap-link="bootstrapLink"
        @close-requested="onCloseRequested"
        @organization-created="onOrganizationCreated"
        @back-requested="onBackToServerChoice"
      />
      <create-organization-trial
        v-if="serverType === ServerType.Trial"
        :bootstrap-link="bootstrapLink"
        @close-requested="onCloseRequested"
        @organization-created="onOrganizationCreated"
        @back-requested="onBackToServerChoice"
        :information-manager="informationManager"
      />
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import {
  parseParsecAddr,
  ParsedParsecAddrTag,
  OrganizationID,
  AvailableDevice,
  DeviceSaveStrategy,
  DeviceSaveStrategyTag,
  AccessStrategy,
  DeviceSaveStrategyPassword,
} from '@/parsec';
import { InformationManager } from '@/services/informationManager';
import { onMounted, ref } from 'vue';
import ServerTypeChoice from '@/views/organizations/creation/ServerTypeChoice.vue';
import { ServerType, getServerTypeFromHost } from '@/services/parsecServers';
import { IonPage, modalController } from '@ionic/vue';
import CreateOrganizationCustomServer from '@/views/organizations/creation/CreateOrganizationCustomServer.vue';
import CreateOrganizationSaas from '@/views/organizations/creation/CreateOrganizationSaas.vue';
import CreateOrganizationTrial from '@/views/organizations/creation/CreateOrganizationTrial.vue';
import { Answer, askQuestion, MsModalResult } from 'megashark-lib';

const props = defineProps<{
  informationManager: InformationManager;
  bootstrapLink?: string;
  defaultChoice?: ServerType;
}>();

const serverType = ref<ServerType | undefined>(props.defaultChoice);

onMounted(async () => {
  if (props.bootstrapLink) {
    const result = await parseParsecAddr(props.bootstrapLink);
    if (result.ok && result.value.tag === ParsedParsecAddrTag.OrganizationBootstrap) {
      serverType.value = getServerTypeFromHost(result.value.hostname, result.value.port, result.value.useSsl);
    }
  }
});

async function onServerChosen(chosenServerType: ServerType): Promise<void> {
  serverType.value = chosenServerType;
}

async function onCloseRequested(force = false): Promise<void> {
  let answer = Answer.Yes;
  // No point in having confirmation at this stage
  if (serverType.value !== undefined && !force) {
    answer = await askQuestion('CreateOrganization.cancelConfirm', 'CreateOrganization.cancelConfirmSubtitle', {
      keepMainModalHiddenOnYes: true,
      yesText: 'CreateOrganization.cancelYes',
      noText: 'CreateOrganization.cancelNo',
      yesIsDangerous: true,
      backdropDismiss: false,
    });
  }

  if (answer === Answer.Yes) {
    await modalController.dismiss(null, MsModalResult.Cancel);
  }
}

async function onOrganizationCreated(
  _organizationName: OrganizationID,
  device: AvailableDevice,
  saveStrategy: DeviceSaveStrategy,
): Promise<void> {
  const accessStrategy =
    saveStrategy.tag === DeviceSaveStrategyTag.Keyring
      ? AccessStrategy.useKeyring(device)
      : AccessStrategy.usePassword(device, (saveStrategy as DeviceSaveStrategyPassword).password);
  await modalController.dismiss({ device: device, access: accessStrategy }, MsModalResult.Confirm);
}

async function onBackToServerChoice(): Promise<void> {
  serverType.value = undefined;
}
</script>

<style lang="scss" scoped>
.modal-content {
  --height: 100%;
  height: 100%;
  overflow: auto;

  @media only screen and (max-height: 500px) {
    --height: 90vh;
    height: 90vh;
  }

  @include ms.responsive-breakpoint('sm') {
    min-width: 100%;
    --max-height: 90vh;
    max-height: 90vh;
  }
}
</style>
