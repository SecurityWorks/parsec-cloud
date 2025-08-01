// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import { answerQuestion, expect, fillIonInput, logout, msTest } from '@tests/e2e/helpers';

msTest('Parsec account login initial page', async ({ parsecAccount }) => {
  const container = parsecAccount.locator('.homepage-content');
  await expect(container.locator('.account-login__title')).toHaveText('My Parsec account');
});

msTest('Parsec account skip login', async ({ parsecAccount }) => {
  const container = parsecAccount.locator('.homepage-content');
  await expect(container.locator('.homepage-skip__button')).toHaveText('Skip this step');
  await container.locator('.homepage-skip__button').click();
  await expect(parsecAccount).toHaveURL(/.+\/home$/);
  await expect(parsecAccount.locator('.organization-content')).toBeVisible();
});

msTest('Parsec account go to customer area', async ({ parsecAccount }) => {
  const container = parsecAccount.locator('.homepage-content');
  const customerAreaContainer = container.locator('.homepage-client-area');
  await expect(customerAreaContainer.locator('.homepage-client-area__title')).toHaveText('Customer area');
  await expect(customerAreaContainer.locator('.homepage-client-area__button')).toHaveText('Access');
  await customerAreaContainer.locator('.homepage-client-area__button').click();
  await expect(parsecAccount).toHaveURL(/.+\/home$/);
  await expect(parsecAccount.locator('.saas-login-container')).toBeVisible();
});

msTest('Parsec account go to creation', async ({ parsecAccount }) => {
  const container = parsecAccount.locator('.homepage-content');
  await expect(container.locator('.account-create__button')).toHaveText('Create an account');
  await container.locator('.account-create__button').click();
  await expect(parsecAccount).toHaveURL(/.+\/createAccount$/);
});

msTest('Open settings in profile homepage popover ', async ({ parsecAccountLoggedIn }) => {
  const accountNameButton = parsecAccountLoggedIn.locator('.profile-header-homepage');
  await expect(accountNameButton).toBeVisible();
  await expect(accountNameButton).toHaveText(/^Agent\d+$/);
  await expect(parsecAccountLoggedIn.locator('.profile-header-homepage-popover')).toBeHidden();
  await accountNameButton.click();
  await expect(parsecAccountLoggedIn.locator('.profile-header-homepage-popover')).toBeVisible();
  const popover = parsecAccountLoggedIn.locator('.profile-header-homepage-popover');
  const header = parsecAccountLoggedIn.locator('.header-list');
  await expect(header.locator('.header-list-email')).toHaveText(/^agent\d+@example.com$/);

  const buttons = popover.locator('.main-list').getByRole('listitem');
  await expect(buttons).toHaveText(['Settings', 'Account', 'Authentication', 'Log out']);
  await popover.locator('.main-list').getByRole('listitem').nth(0).click();
});

msTest('Open settings from header (secondary menu) ', async ({ parsecAccountLoggedIn }) => {
  const settingsButton = parsecAccountLoggedIn.locator('.menu-secondary').locator('#trigger-settings-button');
  await expect(settingsButton).toBeVisible();
  await settingsButton.click();
  await expect(parsecAccountLoggedIn.locator('.profile-content-item').nth(0).locator('.item-header__title')).toHaveText('Settings');
});

msTest('Switch tab from popover ', async ({ parsecAccountLoggedIn }) => {
  const accountNameButton = parsecAccountLoggedIn.locator('.profile-header-homepage');
  await expect(accountNameButton).toBeVisible();
  await expect(accountNameButton).toHaveText(/^Agent\d+$/);
  await expect(parsecAccountLoggedIn.locator('.profile-header-homepage-popover')).toBeHidden();
  await accountNameButton.click();
  await expect(parsecAccountLoggedIn.locator('.profile-header-homepage-popover')).toBeVisible();
  const popover = parsecAccountLoggedIn.locator('.profile-header-homepage-popover');
  const buttons = popover.locator('.main-list').getByRole('listitem');
  await expect(buttons).toHaveText(['Settings', 'Account', 'Authentication', 'Log out']);
  await popover.locator('.main-list').getByRole('listitem').nth(1).click();
  await expect(parsecAccountLoggedIn.locator('.profile-content-item').nth(0).locator('.item-header__title')).toHaveText('My account');
  await accountNameButton.click();
  await expect(parsecAccountLoggedIn.locator('.profile-header-homepage-popover')).toBeVisible();
  await popover.locator('.main-list').getByRole('listitem').nth(2).click();
  await expect(parsecAccountLoggedIn.locator('.profile-content-item').nth(0).locator('.item-header__title')).toHaveText('Authentication');
});

msTest.skip('Account auto-register device', async ({ parsecAccountLoggedIn }) => {
  const home = parsecAccountLoggedIn;
  await home.locator('.organization-list').locator('.organization-card').nth(0).click();
  await fillIonInput(home.locator('#password-input').locator('ion-input'), 'P@ssw0rd.');
  await home.locator('.login-card-footer').locator('.login-button').click();
  await answerQuestion(home, true, {
    expectedNegativeText: 'No',
    expectedPositiveText: 'Store to Parsec Account',
    expectedQuestionText: "This device is not stored in Parsec Account. Do you want to store it so that it'll be available everywhere?",
    expectedTitleText: 'Store this device to Parsec Account',
  });
  await expect(home).toBeWorkspacePage();
  await logout(home);
  await home.locator('.organization-list').locator('.organization-card').nth(0).click();
  // Doesn't ask for the password, using parsec account to authenticate
  await expect(home).toBeWorkspacePage();
});
