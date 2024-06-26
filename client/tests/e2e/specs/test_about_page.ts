// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

describe('Check about page', () => {
  beforeEach(() => {
    cy.visitApp('coolorg');
    cy.login('Boby', 'P@ssw0rd.');
    cy.get('#profile-button').click();
    cy.get('.popover-viewport').find('.version').click();
  });

  afterEach(() => {
    cy.dropTestbed();
  });

  it('Opens the about page', () => {
    cy.get('.topbar-left__title').find('.title-h2').contains('About');
    cy.get('.about-container').find('.info-list').find('.app-info-key').as('keys').should('have.length', 4);
    cy.get('.about-container').find('.info-list').find('.app-info-value').as('values').should('have.length', 4);
    cy.get('@keys').eq(0).contains('Version');
    cy.get('@keys').eq(1).contains('Developer');
    cy.get('@keys').eq(2).contains('License');
    cy.get('@keys').eq(3).contains('Project');
    cy.get('@values')
      .eq(0)
      .contains(/v[\da-z.-]+/);
    cy.get('@values').eq(1).contains('Parsec Cloud');
    cy.get('@values').eq(2).contains('BUSL-1.1');
    cy.get('@values').eq(3).contains('GitHub');
    cy.get('.about').find('#notuptodate').contains('A new version is available.');
    cy.get('.info-list').find('.changelog-btn').contains('Show changelog');
  });

  it('Go back to workspaces', () => {
    cy.get('.topbar-left').find('.topbar-left__title').contains('About');
    cy.get('.topbar-left__breadcrumb').should('not.contain', 'My workspaces');
    cy.get('.topbar-left').find('.back-button').click();
    cy.get('.topbar-left__breadcrumb').contains('My workspaces');
  });
});
