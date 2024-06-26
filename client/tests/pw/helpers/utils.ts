// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import { BrowserContext, Locator, Page } from '@playwright/test';
import { expect } from '@tests/pw/helpers/assertions';

interface QuestionOptions {
  expectedTitleText?: string | RegExp;
  expectedQuestionText?: string | RegExp;
  expectedPositiveText?: string | RegExp;
  expectedNegativeText?: string | RegExp;
}

export async function answerQuestion(page: Page, positiveAnswer: boolean, options?: QuestionOptions): Promise<void> {
  const modal = page.locator('.question-modal');
  const positiveButton = modal.locator('#next-button');
  const negativeButton = modal.locator('#cancel-button');

  await expect(modal).toBeVisible();

  if (options) {
    if (options.expectedTitleText) {
      await expect(modal.locator('.ms-modal-header__title')).toHaveText(options.expectedTitleText);
    }
    if (options.expectedQuestionText) {
      await expect(modal.locator('.ms-modal-header__text')).toHaveText(options.expectedQuestionText);
    }
    if (options.expectedPositiveText) {
      await expect(positiveButton).toHaveText(options.expectedPositiveText);
    }
    if (options.expectedNegativeText) {
      await expect(negativeButton).toHaveText(options.expectedNegativeText);
    }
  }
  if (positiveAnswer) {
    await positiveButton.click();
  } else {
    await negativeButton.click();
  }
  await expect(modal).toBeHidden();
}

export async function fillIonInput(ionInput: Locator, text: string): Promise<void> {
  const input = ionInput.locator('input');
  await input.fill(text);
  await input.blur();
}

export async function fillInputModal(root: Locator | Page, text: string, clear?: boolean): Promise<void> {
  const modal = root.locator('.text-input-modal');
  if (clear) {
    await fillIonInput(modal.locator('ion-input'), '');
  }
  const okButton = modal.locator('.ms-modal-footer-buttons').locator('#next-button');
  await expect(okButton).toHaveDisabledAttribute();
  await fillIonInput(modal.locator('ion-input'), text);
  await expect(okButton).not.toHaveDisabledAttribute();
  await okButton.click();
  await expect(modal).toBeHidden();
}

export async function getClipboardText(page: Page): Promise<string> {
  return await page.evaluate(() => navigator.clipboard.readText());
}

export async function setWriteClipboardPermission(context: BrowserContext, allow: boolean): Promise<void> {
  if (allow) {
    await context.grantPermissions(['clipboard-write']);
  } else {
    // There doesn't seem to be a function to remove specific permissions, so we clear
    // them all and re-add clipboard-read.
    await context.clearPermissions();
    await context.grantPermissions(['clipboard-read']);
  }
}

export async function selectDropdown(button: Locator, select: string, currentlySelected?: string): Promise<void> {
  const page = button.page();
  await expect(page.locator('.dropdown-popover')).toBeHidden();
  await button.click();
  const dropdown = page.locator('.dropdown-popover');
  await expect(dropdown).toBeVisible();

  const options = dropdown.getByRole('listitem');
  if (currentlySelected) {
    await expect(options.filter({ hasText: currentlySelected })).toHaveTheClass('selected');
  }
  await options.filter({ hasText: select }).click();
  await expect(page.locator('.dropdown-popover')).toBeHidden();
}

export async function sortBy(sortButton: Locator, clickOnLabel: string): Promise<void> {
  await sortButton.click();
  const popover = sortButton.page().locator('.sorter-popover');
  await popover.getByRole('listitem').filter({ hasText: clickOnLabel }).click();
  await expect(popover).toBeHidden();
}
