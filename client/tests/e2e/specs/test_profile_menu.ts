// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

describe('Check profile menu links', () => {
  beforeEach(() => {
    cy.visitApp();
    cy.login('Boby', 'P@ssw0rd.');
  });

  afterEach(() => {
    cy.dropTestbed();
  });

  it('Checks initial status', () => {
    cy.get('#profile-button').click();
    cy.get('.popover-viewport').contains('My profile');
    cy.get('.popover-viewport').contains('Settings');
    cy.get('.popover-viewport').contains('Help and feedback');
    cy.get('.popover-viewport').contains('Log out');
  });

  it('Click profile link', () => {
    cy.get('#profile-button').click();
    cy.get('.popover-viewport').contains('My profile').click();
    cy.url().should('include', '/myProfile');
    cy.get('.topbar-left__title').contains('My profile');
  });

  it('Click settings link', () => {
    cy.get('#profile-button').click();
    cy.get('.popover-viewport').contains('Settings').click();
    cy.get('ion-modal').get('ion-title').contains('Settings');
  });

  it('Click help and feedback link', () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').callsFake(() => true);
    });
    cy.get('#profile-button').click();
    cy.get('.popover-viewport').contains('Help and feedback').click();
    cy.window().its('open').should('be.called.with', 'https://my.parsec.cloud/help');
  });
});
