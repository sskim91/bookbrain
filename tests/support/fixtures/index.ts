import { test as base, expect } from '@playwright/test';

type TestFixtures = {
  apiUrl: string;
};

export const test = base.extend<TestFixtures>({
  apiUrl: async ({}, use) => {
    await use(process.env.API_URL || 'http://localhost:8000');
  },
});

export { expect };
