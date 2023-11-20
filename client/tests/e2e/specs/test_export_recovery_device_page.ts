// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

describe('Display export recovery device page', () => {
  beforeEach(() => {
    cy.visitApp();
    cy.login('Boby', 'P@ssw0rd.');
    cy.get('#profile-button').click();
    cy.get('.popover-viewport').find('ion-item').eq(1).click();
    cy.get('.restore-password-button').click();
  });

  afterEach(() => {
    cy.dropTestbed();
  });

  it('Check export recovery device', () => {
    cy.get('.topbar-left__title').find('.title-h2').contains('Recovery files');
    cy.get('.recovery-container').find('.block').as('blocks').should('have.length', 2);
    cy.get('@blocks').eq(0).contains('Recovery File');
    cy.get('@blocks').eq(1).contains('Secret Key');
    cy.get('.password-input-modal').should('not.exist');
    cy.get('.recovery-container').find('#exportDevice').contains('I understand').click();
    cy.get('.password-input-modal').should('exist');
    cy.get('.password-input-modal').find('.ms-modal-header__title').contains('Password needed');
    cy.get('.password-input-modal').find('.footer-md').find('#next-button').as('okButton').contains('Validate');
    cy.get('@okButton').should('have.class', 'button-disabled');
    cy.get('.password-input-modal').find('#ms-password-input').find('input').type('P@ssw0rd.');
    cy.get('@okButton').should('not.have.class', 'button-disabled');
    cy.get('@okButton').click();
  });
});
