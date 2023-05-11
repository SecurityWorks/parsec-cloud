// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

// cSpell:disable

import WorkspaceCard from '@/components/WorkspaceCard.vue';
import { MockWorkspace } from '@/common/mocks';

import { DateTime } from 'luxon';
import { createI18n } from 'vue-i18n';
import enUS from '@/locales/en-US.json';

const WORKSPACE: MockWorkspace = {
  id: 'id1',
  name: 'Waukeen\'s Promenade',
  sharedWith: ['Aerie', 'Cernd'],
  size: 60_817_408,
  role: 'Reader',
  availableOffline: true,
  lastUpdate: DateTime.fromISO('2023-05-08T12:00:00')
};

it('display the workspace card', () => {
  cy.mount(WorkspaceCard, {
    props: {
      workspace: WORKSPACE
    }
  }).as('workspaceCard');

  cy.get('@workspaceCard').get('.workspace-label').should('have.text', WORKSPACE.name);
  cy.get('@workspaceCard').get('.workspace-info').find('ion-label').eq(0).should('have.text', '60.8 MB');
  cy.get('@workspaceCard').get('.workspace-info').find('ion-label').eq(1).should('have.text', '2 people');
});

// it('displays different sizes correctly', () => {
//   const SIZES: [number, string][] = [
//     [56_965_123, '56.96 MB'],
//     [4_394_102_583_412, '4.39 TB'],
//     [12, '12 B'],
//     [123_876, '123 KB']
//   ];

//   SIZES.forEach(item => {
//     WORKSPACE.size = item[0];

//     cy.mount(WorkspaceCard, {
//       props: {
//         workspace: WORKSPACE
//       }
//     }).as('workspaceCard');

//     cy.get('@workspaceCard').get('.workspace-size').should('have.text', item[1]);
//   });
// });
