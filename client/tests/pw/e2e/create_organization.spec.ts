// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import { expect } from '@tests/pw/helpers/assertions';
import { msTest } from '@tests/pw/helpers/fixtures';

msTest('Opens the create organization modal', async ({ home }) => {
  await expect(home.locator('#create-organization-button')).toHaveText('Create or join');
  await expect(home.locator('.homepage-popover')).toBeHidden();
  await home.locator('#create-organization-button').click();
  await expect(home.locator('.homepage-popover')).toBeVisible();
  await expect(home.locator('.create-organization-modal')).toBeHidden();
  const createButton = home.locator('.homepage-popover').getByRole('listitem').nth(0);
  await expect(createButton.locator('ion-label')).toHaveText('Create');
  await expect(createButton.locator('ion-text')).toHaveText('I want to create an organization');
  await createButton.click();
  const modal = home.locator('.create-organization-modal');
  await expect(modal).toBeVisible();
  await expect(modal.locator('.modal-header-title__text')).toHaveText('Create an organization');
  await expect(modal.locator('.modal-header__text')).toHaveText('Choose the option that best suits your needs:');
  await expect(modal.locator('.server-choice-item').locator('.server-choice-item__label')).toHaveText([
    'Create my organization on Parsec',
    'Try Parsec for 15 days (Your organization and associated data will be deleted at the end of the trial period)',
  ]);
  await expect(modal.locator('.server-modal-footer').locator('ion-button').nth(0)).toHaveText('Use a different Parsec server');

  // Select one option
  const nextButton = modal.locator('.server-modal-footer').locator('ion-button').nth(1);
  await expect(nextButton).toBeTrulyDisabled();
  await expect(nextButton).toHaveText('Continue');
  await modal.locator('.server-choice-item').nth(0).click();
  await expect(nextButton).toBeTrulyEnabled();

  // Check if the close button closes the modal
  await expect(modal.locator('.closeBtn')).toBeVisible();
  await modal.locator('.closeBtn').click();
  await expect(modal).toBeHidden();
});
