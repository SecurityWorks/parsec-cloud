// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

export interface SidebarSavedData {
  width?: number;
  hidden?: boolean;
}

export const SIDEBAR_MENU_DATA_KEY = 'SidebarMenu';

export const SidebarDefaultData: Required<SidebarSavedData> = { width: 300, hidden: false };
