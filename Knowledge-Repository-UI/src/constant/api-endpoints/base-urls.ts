import { createBaseUrl, createUrl } from '../constant';

export const REPOSITORY_BASE_URL = createBaseUrl('repository');

export const ACCOUNT = createBaseUrl('accounts');
export const getAuth = () => createUrl(ACCOUNT, 'login');
