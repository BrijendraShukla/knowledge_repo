import {
  HttpClient,
  HttpHeaders,
  HttpParams,
  HttpResponse,
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { SearchResultResponse } from '../models/search.model';
import {
  downLoadZipUrl,
  getFile,
  search,
} from '../../../../constant/api-endpoints/reposetory-urls';

@Injectable({
  providedIn: 'root',
})
export class SearchApiService {
  constructor(private http: HttpClient) {}
  getSearchResult(payLoad: any): Observable<SearchResultResponse> {
    if (payLoad.generate_tag) {
      delete payLoad.tags;
    }
    const params: HttpParams = new HttpParams({ fromObject: payLoad });

    return this.http.get<SearchResultResponse>(search(), { params });
  }

  getFile(id: number): Observable<HttpResponse<Blob>> {
    const headers = new HttpHeaders({
      responseType: 'blob',
    });
    return this.http.get<Blob>(getFile(id), {
      observe: 'response',
      responseType: 'blob' as 'json',
    });
  }

  getFilesInZip(payLoad: number[]): Observable<HttpResponse<Blob>> {
    return this.http.post<Blob>(
      downLoadZipUrl(),
      { file_ids: payLoad },
      {
        observe: 'response',
        responseType: 'blob' as 'json',
      }
    );
  }
}
