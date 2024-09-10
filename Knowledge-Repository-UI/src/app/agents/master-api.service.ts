import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import {
  getDocumentTypeUrl,
  getFileTypeUrl,
  getIndustryUrl,
} from '../../constant/api-endpoints/reposetory-urls';

@Injectable({
  providedIn: 'root',
})
export class MasterApiService {
  constructor(private http: HttpClient) {}

  getIndustry(): Observable<{ industry: string }[]> {
    return this.http.get<{ industry: string }[]>(getIndustryUrl());
  }

  getFileType(): Observable<{ file_type: string }[]> {
    return this.http.get<{ file_type: string }[]>(getFileTypeUrl());
  }

  getDocumentType(): Observable<{ document_type: string }[]> {
    return this.http.get<{ document_type: string }[]>(getDocumentTypeUrl());
  }
}
