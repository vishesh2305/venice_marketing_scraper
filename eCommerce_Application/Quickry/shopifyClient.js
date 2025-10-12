import { createStorefrontApiClient } from '@shopify/storefront-api-client';

export const client = createStorefrontApiClient({
  storeDomain: 'iwyyib-k6.myshopify.com',
  apiVersion: '2025-01',
  publicAccessToken: '731502b536fef6d451f2a84ee51077a6',
});