import { Injectable } from '@angular/core';
import { StateService } from './state.service';
import { MasterDataState } from '../models/model';
import { Observable, take } from 'rxjs';
import { MasterApiService } from '../agents/master-api.service';

const initialState = {
  fileType: [],
  industry: [],
  documentType: [],
};

@Injectable({
  providedIn: 'root',
})
export class MasterStore extends StateService<MasterDataState> {
  constructor(private masterApi: MasterApiService) {
    super(initialState);
  }

  private industries$: Observable<string[]> = this.select(
    (state: MasterDataState) => state.industry
  );
  private fileTypes$: Observable<string[]> = this.select(
    (state: MasterDataState) => state.fileType
  );

  private documentType$: Observable<string[]> = this.select(
    (state: MasterDataState) => state.documentType
  );

  getindustries(): Observable<string[]> {
    if (this.state.industry.length <= 0) {
      this.masterApi
        .getIndustry()
        .pipe(take(1))
        .subscribe((response) => {
          const industries = response.map((result) => result.industry);
          this.setState({ industry: industries });
        });
    }
    return this.industries$;
  }

  getfileType(): Observable<string[]> {
    if (this.state.fileType.length <= 0) {
      this.masterApi
        .getFileType()
        .pipe(take(1))
        .subscribe((response) => {
          const fileTypes = response.map((result) => result.file_type);
          this.setState({ fileType: fileTypes });
        });
    }
    return this.fileTypes$;
  }

  getDocumentType(): Observable<string[]> {
    if (this.state.documentType.length <= 0) {
      this.masterApi
        .getDocumentType()
        .pipe(take(1))
        .subscribe((response) => {
          const documentType = response.map((result) => result.document_type);
          this.setState({ documentType });
        });
    }
    return this.documentType$;
  }
}
