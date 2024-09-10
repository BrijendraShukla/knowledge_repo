import { createUrl } from '../constant';
import { REPOSITORY_BASE_URL } from './base-urls';

export const getIndustryUrl = () => createUrl(REPOSITORY_BASE_URL, 'industry');

export const getFileTypeUrl = () => createUrl(REPOSITORY_BASE_URL, 'filetypes');

export const getDocumentTypeUrl = () =>
  createUrl(REPOSITORY_BASE_URL, 'document_type');

export const getUserFilesUrl = () =>
  createUrl(REPOSITORY_BASE_URL, 'get-user-files');

export const getUploadFlleDetailUrl = () =>
  createUrl(REPOSITORY_BASE_URL, 'upload');

export const getUploadFileUrl = () =>
  createUrl(REPOSITORY_BASE_URL, 'upload-multiple-files');

export const updateFileDetailUrl = (id: number) =>
  createUrl(getUploadFlleDetailUrl(), id + '');

export const search = () => createUrl(REPOSITORY_BASE_URL, 'Q&A-search');

export const getFile = (id: number) =>
  createUrl(REPOSITORY_BASE_URL, `view-file/${id}`);

export const downLoadZipUrl = () => createUrl(REPOSITORY_BASE_URL, 'download');
