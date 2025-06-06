// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

onmessage = function (event): void {
  import('xlsx').then((XLSX) => {
    try {
      const start = Date.now();
      const workbook = XLSX.read(event.data, { type: 'array' });
      const end = Date.now();
      const delay = end - start < 1000 ? 1000 - (end - start) : 0;
      // Adds a small delay if the loading is very fast to avoid blinking
      setTimeout(() => {
        postMessage({ ok: true, value: workbook });
      }, delay);
    } catch (e: any) {
      postMessage({ ok: false, error: e });
    }
  });
};
