import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import {
  FileUploadApiResponse,
  MyContributionApiResponse,
} from '../models/content.model';
import {
  getFile,
  getUploadFileUrl,
  getUploadFlleDetailUrl,
  getUserFilesUrl,
  updateFileDetailUrl,
} from '../../../../constant/api-endpoints/reposetory-urls';

@Injectable({ providedIn: 'root' })
export class ContentApiService {
  constructor(private http: HttpClient) {}

  getContibutionList(payLoad: any): Observable<MyContributionApiResponse> {
    const params: HttpParams = new HttpParams({ fromObject: payLoad });

    return this.http.get<MyContributionApiResponse>(getUserFilesUrl(), {
      params,
    });
  }

  getNextContributionList(url: string): Observable<MyContributionApiResponse> {
    return this.http.get<MyContributionApiResponse>(url);
  }

  uploadFile(file: File): Observable<FileUploadApiResponse> {
    const formData = new FormData();

    formData.append('files', file);

    return this.http.post<FileUploadApiResponse>(getUploadFileUrl(), formData);
  }

  uploadFileDetails(payLoad: any, fileMap: Map<string, File>) {
    //need to change the type of payload
    //need to add one more parameter to share the id in params
    const formData = new FormData();
    payLoad.data.forEach((group: any) => {
      const file: File = fileMap.get(group.id)!;
      console.log(group);
      console.log(file.name);
      formData.append('files', file);
      formData.append('name', group.fileName);
      formData.append('industry', group.industry);
      formData.append('summary', group.summary);
      formData.append('file_type', group.fileCategory);
      formData.append('document_type', group.documentType);

      const tags = group.tags.map((tag: any) => tag.name);
      formData.append('tags', tags);
    });
    return this.http.post(getUploadFlleDetailUrl(), formData);
  }

  deleteContribution(id: number) {
    return this.http.delete(updateFileDetailUrl(id));
  }

  updateContribution(payLoad: any) {
    const formData = new FormData();

    formData.append('name', payLoad.fileName);
    formData.append('industry', payLoad.industry);
    formData.append('summary', payLoad.summary);
    formData.append('file_type', payLoad.fileCategory);
    formData.append('document_type', payLoad.documentType);

    payLoad.tags = payLoad.tags.map((tag: any) => tag.name);
    formData.append('tags', payLoad.tags);

    return this.http.patch(updateFileDetailUrl(payLoad.id), formData);
  }
}
