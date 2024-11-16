// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

/* eslint-disable camelcase */

import { Page, Route } from '@playwright/test';
import {
  DEFAULT_ORGANIZATION_DATA_SLICE,
  DEFAULT_ORGANIZATION_INFORMATION,
  DEFAULT_USER_INFORMATION,
  UserData,
} from '@tests/e2e/helpers/data';
import { DateTime } from 'luxon';

async function mockRoute(
  page: Page,
  url: string | RegExp,
  options: MockRouteOptions | undefined,
  handler: (route: Route) => Promise<void>,
): Promise<void> {
  async function _handleError(route: Route, options: MockMethodOptions): Promise<boolean> {
    if (options.timeout) {
      await route.abort('timedout');
      return true;
    }
    if (options.errors) {
      await route.fulfill({
        status: options.errors.status ?? 400,
        json: {
          type: 'error',
          errors: [{ code: options.errors.code ?? 'error', attr: options.errors.attribute ?? 'attr', detail: 'Default error' }],
        },
      });
      return true;
    }
    return false;
  }

  await page.route(url, async (route) => {
    const method = route.request().method().toUpperCase();

    if (method === 'GET' && options && options.GET) {
      if (await _handleError(route, options.GET)) {
        return;
      }
    } else if (method === 'POST' && options && options.POST) {
      if (await _handleError(route, options.POST)) {
        return;
      }
    } else if (method === 'PUT' && options && options.PUT) {
      if (await _handleError(route, options.PUT)) {
        return;
      }
    } else if (method === 'PATCH' && options && options.PATCH) {
      if (await _handleError(route, options.PATCH)) {
        return;
      }
    }

    await handler(route);
  });
}

interface MockMethodOptions {
  timeout?: boolean;
  errors?: {
    code?: string;
    attribute?: string;
    status?: number;
  };
}

interface MockRouteOptions {
  PATCH?: MockMethodOptions;
  GET?: MockMethodOptions;
  PUT?: MockMethodOptions;
  POST?: MockMethodOptions;
}

async function mockLogin(page: Page, options?: MockRouteOptions): Promise<void> {
  const TOKEN_RAW = {
    email: DEFAULT_USER_INFORMATION.email,
    is_staff: true,
    token_type: 'access',
    user_id: DEFAULT_USER_INFORMATION.id,
    exp: DateTime.utc().plus({ years: 42 }).toJSDate().valueOf(),
    iat: 0,
  };
  const TOKEN = btoa(JSON.stringify(TOKEN_RAW));

  await mockRoute(page, '**/api/token', options, async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        access: TOKEN,
        refresh: TOKEN,
      },
    });
  });
}

interface MockUserOverload {
  billingSystem?: 'STRIPE' | 'CUSTOM_ORDER' | 'NONE' | 'EXPERIMENTAL_CANDIDATE';
}

async function mockUserRoute(page: Page, overload: MockUserOverload = {}, options?: MockRouteOptions): Promise<void> {
  await mockRoute(page, `**/users/${DEFAULT_USER_INFORMATION.id}`, options, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        json: {
          id: DEFAULT_USER_INFORMATION.id,
          created_at: '2024-07-15T13:21:32.141317Z',
          email: UserData.email,
          client: {
            firstname: UserData.firstName,
            lastname: UserData.lastName,
            id: '1337',
            job: UserData.job,
            company: UserData.company,
            phone: UserData.phone,
            billing_system: overload.billingSystem ?? 'STRIPE',
          },
        },
      });
    } else if (route.request().method() === 'PATCH') {
      const data = await route.request().postDataJSON();
      if (data.client) {
        if (data.client.firstname) {
          UserData.firstName = data.client.firstname;
        }
        if (data.client.lastname) {
          UserData.lastName = data.client.lastname;
        }
        if (data.client.phone) {
          UserData.phone = data.client.phone;
        }
        if (data.client.job || data.client.job === null) {
          UserData.job = data.client.job;
        }
        if (data.client.company || data.client.job === null) {
          UserData.company = data.client.company;
        }
      }
      await route.fulfill({
        status: 200,
      });
    }
  });
}

async function mockCreateOrganization(page: Page, bootstrapAddr: string, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/organizations`,
    options,
    async (route) => {
      await route.fulfill({
        status: 201,
        json: {
          bootstrap_link: bootstrapAddr,
        },
      });
    },
  );
}

async function mockListOrganizations(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/organizations`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          results: [
            {
              pk: DEFAULT_ORGANIZATION_INFORMATION.bmsId,
              created_at: '2024-12-04T00:00:00.000',
              expiration_date: null,
              name: DEFAULT_ORGANIZATION_INFORMATION.name,
              parsec_id: DEFAULT_ORGANIZATION_INFORMATION.name,
              suffix: DEFAULT_ORGANIZATION_INFORMATION.name,
              stripe_subscription_id: 'stripe_id',
              bootstrap_link: '',
            },
            {
              pk: `${DEFAULT_ORGANIZATION_INFORMATION.bmsId}-2`,
              created_at: '2024-12-04T00:00:00.000',
              expiration_date: null,
              name: DEFAULT_ORGANIZATION_INFORMATION.name,
              parsec_id: `${DEFAULT_ORGANIZATION_INFORMATION.name}-2`,
              suffix: `${DEFAULT_ORGANIZATION_INFORMATION.name}-2`,
              stripe_subscription_id: 'stripe_id2',
              bootstrap_link: '',
            },
          ],
        },
      });
    },
  );
}

interface MockOrganizationStatsOverload {
  dataSize?: number;
  metadataSize?: number;
  freeSliceSize?: number;
  payingSliceSize?: number;
  users?: number;
  activeUsers?: number;
  status?: string;
  usersPerProfileDetails?: {
    [profile: string]: { active: number; revoked: number };
  };
}

async function mockOrganizationStats(page: Page, overload: MockOrganizationStatsOverload = {}, options?: MockRouteOptions): Promise<void> {
  const usersPerProfileDetail: { [profile: string]: { active: number; revoked: number } } = {};
  usersPerProfileDetail.ADMIN =
    overload.usersPerProfileDetails && overload.usersPerProfileDetails.ADMIN
      ? overload.usersPerProfileDetails.ADMIN
      : { active: 4, revoked: 1 };
  usersPerProfileDetail.STANDARD =
    overload.usersPerProfileDetails && overload.usersPerProfileDetails.STANDARD
      ? overload.usersPerProfileDetails.STANDARD
      : { active: 54, revoked: 1 };
  usersPerProfileDetail.OUTSIDER =
    overload.usersPerProfileDetails && overload.usersPerProfileDetails.OUTSIDER
      ? overload.usersPerProfileDetails.OUTSIDER
      : { active: 1, revoked: 142 };

  await mockRoute(
    page,
    // eslint-disable-next-line max-len
    `*/**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/organizations/*/stats`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          users_per_profile_detail: usersPerProfileDetail,
          data_size: overload.dataSize ?? 400000000000,
          metadata_size: overload.metadataSize ?? 400000000,
          free_slice_size: overload.freeSliceSize ?? DEFAULT_ORGANIZATION_DATA_SLICE.free,
          paying_slice_size: overload.payingSliceSize ?? DEFAULT_ORGANIZATION_DATA_SLICE.paying,
          users: overload.users ?? 203,
          active_users: overload.activeUsers ?? 59,
          status: overload.status ?? 'ok',
        },
      });
    },
  );
}

interface MockOrganizationStatusOverload {
  activeUsersLimit?: number;
  isBootstrapped?: boolean;
  isFrozen?: boolean;
  isInitialized?: boolean;
  outsiderAllowed?: boolean;
}

async function mockOrganizationStatus(
  page: Page,
  overload: MockOrganizationStatusOverload = {},
  options?: MockRouteOptions,
): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/organizations/*/status`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          active_users_limit: overload.activeUsersLimit ?? 1000,
          is_bootstrapped: overload.isBootstrapped ?? true,
          is_frozen: overload.isFrozen ?? false,
          is_initialized: overload.isInitialized ?? true,
          user_profile_outsider_allowed: overload.outsiderAllowed ?? true,
        },
      });
    },
  );
}

interface MockGetInvoicesOverload {
  count?: number;
}

async function mockGetInvoices(page: Page, overload: MockGetInvoicesOverload = {}, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/invoices`,
    options,
    async (route) => {
      let invoices = [];
      for (let year = 2019; year < 2022; year++) {
        for (let month = 1; month < 13; month++) {
          invoices.push({
            id: `Id${year}-${month}`,
            pdf: `https://fake/pdfs/${year}-${month}.pdf`,
            period_start: DateTime.fromObject({ year: year, month: month }).toFormat('yyyy-LL-dd'),
            period_end: DateTime.fromObject({ year: year, month: month }).endOf('month').toFormat('yyyy-LL-dd'),
            total: Math.round(Math.random() * 1000),
            status: ['paid', 'draft', 'open'][Math.floor(Math.random() * 3)],
            organization: DEFAULT_ORGANIZATION_INFORMATION.name,
            number: `${year}-${month}`,
            receiptNumber: `${year}-${month}`,
          });
        }
      }
      if (overload.count !== undefined) {
        invoices = invoices.slice(0, overload.count);
      }

      await route.fulfill({
        status: 200,
        json: {
          count: invoices.length,
          results: invoices,
        },
      });
    },
  );
}

interface MockBillingDetailsOverload {
  cardsCount?: number;
  sepaCount?: number;
  email?: string;
  name?: string;
  address?: {
    line1?: string;
    line2?: string;
    city?: string;
    postalCode?: string;
    country?: string;
  };
}

async function mockBillingDetails(page: Page, overload: MockBillingDetailsOverload = {}, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/billing_details`,
    options,
    async (route) => {
      if (route.request().method() === 'GET') {
        const paymentMethods = [];
        for (let i = 0; i < (overload.cardsCount ?? 1); i++) {
          paymentMethods.push({
            type: 'card',
            id: `card${i}`,
            brand: 'mastercard',
            exp_date: '12/47',
            last_digits: '4444',
            default: true,
          });
        }
        for (let i = 0; i < (overload.sepaCount ?? 1); i++) {
          paymentMethods.push({
            type: 'debit',
            id: `debit${i}`,
            bank_name: 'Bank',
            last_digits: '1234',
            default: overload.cardsCount === undefined || overload.cardsCount === 0 ? true : false,
          });
        }
        await route.fulfill({
          status: 200,
          json: {
            email: overload.email ?? UserData.email,
            name: overload.name ?? `${UserData.firstName} ${UserData.lastName}`,
            address: {
              line1: (overload.address && overload.address.line1) ?? UserData.address.line1,
              line2: (overload.address && overload.address.line2) ?? '',
              city: (overload.address && overload.address.city) ?? UserData.address.city,
              postal_code: (overload.address && overload.address.postalCode) ?? UserData.address.postalCode,
              country: (overload.address && overload.address.country) ?? UserData.address.country,
            },
            payment_methods: paymentMethods,
          },
        });
      } else if (route.request().method() === 'PATCH') {
        const data = await route.request().postDataJSON();
        if (data.address) {
          if (data.address.line1) {
            UserData.address.line1 = data.address.line1;
          }
          if (data.address.line2) {
            UserData.address.line2 = data.address.line2;
          }
          if (data.address.postal_code) {
            UserData.address.postalCode = data.address.postal_code;
          }
          if (data.address.city) {
            UserData.address.line1 = data.address.city;
          }
          if (data.address.country) {
            UserData.address.line1 = data.address.country;
          }
        }
        await route.fulfill({
          status: 200,
        });
      }
    },
  );
}

async function mockAddPaymentMethod(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/add_payment_method`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          payment_method: '123456',
        },
      });
    },
  );
}

async function mockSetDefaultPaymentMethod(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/default_payment_method`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          payment_method: '123456',
        },
      });
    },
  );
}

async function mockDeletePaymentMethod(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/delete_payment_method`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          payment_method: '123456',
        },
      });
    },
  );
}

async function mockUpdateEmailSendCode(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(page, '**/email_validation/send_code', options, async (route) => {
    await route.fulfill({
      status: 200,
    });
  });
}

async function mockUpdateEmail(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(page, `**/users/${DEFAULT_USER_INFORMATION.id}/update_email`, options, async (route) => {
    const data = await route.request().postDataJSON();
    if (data.email) {
      UserData.email = data.email;
    }
    await route.fulfill({
      status: 200,
    });
  });
}

async function mockUpdateAuthentication(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(page, `**/users/${DEFAULT_USER_INFORMATION.id}/update_authentication`, options, async (route) => {
    await route.fulfill({
      status: 204,
    });
  });
}

async function mockChangePassword(page: Page, options?: MockRouteOptions): Promise<void> {
  await mockRoute(page, '**/users/change_password', options, async (route) => {
    await route.fulfill({
      status: 200,
    });
  });
}

interface MockCustomOrderDetailsOverload {
  created?: DateTime;
  amountWithTaxes?: number;
  amountWithoutTaxes?: number;
  amountDue?: number;
  licenseStart?: DateTime;
  licenseEnd?: DateTime;
  adminAmountWithTaxes?: number;
  outsiderAmountWithTaxes?: number;
  standardAmountWithTaxes?: number;
  storageAmountWithTaxes?: number;
  adminOrdered?: number;
  standardOrdered?: number;
  outsiderOrdered?: number;
  storageOrdered?: number;
}

async function mockCustomOrderDetails(
  page: Page,
  overload: MockCustomOrderDetailsOverload = {},
  options?: MockRouteOptions,
): Promise<void> {
  await mockRoute(
    page,
    // eslint-disable-next-line max-len
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/organizations/custom_order_details`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          id: 'custom_order_id',
          created: overload.created ? overload.created.toISO() : '1988-04-07T00:00:00+00:00',
          number: 'FACT001',
          amounts: {
            total_excl_tax: overload.amountWithoutTaxes ? overload.amountWithoutTaxes.toString() : '42.00',
            // x10, damn government
            total_incl_tax: overload.amountWithTaxes ? overload.amountWithTaxes.toString() : '420.00',
            total_remaining_due_incl_tax: overload.amountDue ? overload.amountDue.toString() : '420.00',
          },
          pdf_link: 'https://parsec.cloud',
          rows: [
            {
              reference: 'Psc_D0_Adm_M',
              amount_tax_inc: overload.adminAmountWithTaxes ? overload.adminAmountWithTaxes.toString() : '160.00',
            },
            {
              reference: 'Psc_D0_Std_User_M',
              amount_tax_inc: overload.standardAmountWithTaxes ? overload.standardAmountWithTaxes.toString() : '200.00',
            },
            {
              reference: 'Psc_D0_Ext_User_M',
              amount_tax_inc: overload.outsiderAmountWithTaxes ? overload.outsiderAmountWithTaxes.toString() : '80.00',
            },
            {
              // cspell:disable-next-line
              reference: 'Psc_Stck_100_Go_M',
              amount_tax_inc: overload.storageAmountWithTaxes ? overload.storageAmountWithTaxes.toString() : '120.00',
            },
          ],
          _embed: {
            custom_fields: [
              {
                value: 'parsec-saas-custom-order-start-date',
                code: overload.licenseStart ? overload.licenseStart.toISO() : '1988-04-07T00:00:00+00:00',
              },
              {
                value: 'parsec-saas-custom-order-end-date',
                code: overload.licenseStart ? overload.licenseStart.toISO() : DateTime.now().plus({ year: 1 }).toISO(),
              },
              {
                value: 'parsec-saas-custom-order-admin-license-count',
                code: overload.adminOrdered ? overload.adminOrdered.toString() : '32',
              },
              {
                value: 'parsec-saas-custom-order-outsider-license-count',
                code: overload.outsiderOrdered ? overload.outsiderOrdered.toString() : '100',
              },
              {
                value: 'parsec-saas-custom-order-standard-license-count',
                code: overload.standardOrdered ? overload.standardOrdered.toString() : '50',
              },
              {
                value: 'parsec-saas-custom-order-storage-license-count',
                code: overload.storageOrdered ? overload.storageOrdered.toString() : '10',
              },
            ],
          },
        },
      });
    },
  );
}

async function mockCustomOrderStatus(page: Page, options?: MockRouteOptions): Promise<void> {
  const data: { [key: string]: string } = {};
  data[DEFAULT_ORGANIZATION_INFORMATION.name] = 'invoice_paid';

  await mockRoute(
    page,
    `**/users/${DEFAULT_USER_INFORMATION.id}/clients/${DEFAULT_USER_INFORMATION.clientId}/organizations/custom_order_status`,
    options,
    async (route) => {
      await route.fulfill({
        status: 200,
        json: data,
      });
    },
  );
}

export const MockBms = {
  mockLogin,
  mockUserRoute,
  mockCreateOrganization,
  mockListOrganizations,
  mockOrganizationStats,
  mockOrganizationStatus,
  mockGetInvoices,
  mockBillingDetails,
  mockAddPaymentMethod,
  mockSetDefaultPaymentMethod,
  mockDeletePaymentMethod,
  mockUpdateEmail,
  mockUpdateAuthentication,
  mockChangePassword,
  mockCustomOrderStatus,
  mockCustomOrderDetails,
  mockUpdateEmailSendCode,
};