import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { logInApiResponse, logInPayload } from '../models/login.model';
import { getAuth } from '../../constant/api-endpoints/base-urls';

@Injectable()
export class LoginApiService {
  constructor(private http: HttpClient) {}

  getAuth(logInPayload: logInPayload): Observable<logInApiResponse> {
    console.log('in auth function');
    return this.http.post<logInApiResponse>(getAuth(), logInPayload);
  }
}
