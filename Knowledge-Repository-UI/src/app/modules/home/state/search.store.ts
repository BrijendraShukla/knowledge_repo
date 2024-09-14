import { Injectable } from '@angular/core';
import { Observable, take } from 'rxjs';
import { StateService } from '../../../state/state.service';
import {
  SearchPayload,
  SearchResultResponse,
  SearchStateModel,
} from '../models/search.model';
import { SearchApiService } from '../agents/search-api.service';
import { HttpErrorResponse } from '@angular/common/http';

let initialState: SearchStateModel = {
  data: {
    tags: [],
    results: [],
    count: 0,
    next: null,
  },
  payload: {
    query: '',
    generate_tag: true,
  },
};
@Injectable({ providedIn: 'root' })
export class SearchStore extends StateService<SearchStateModel> {
  constructor(private searchApi: SearchApiService) {
    super(initialState);
  }
  searchResultData$: Observable<SearchResultResponse> = this.select(
    (state) => state.data
  );

  tagList$: Observable<string[]> = this.select(
    (state) => state.payload.tags ?? []
  );

  payload$: Observable<SearchPayload> = this.select((state) => state.payload);
  setSearchResultData(data: SearchResultResponse) {
    this.setState({ data });
  }

  getSearchTerm() {
    return this.state.payload.query;
  }

  removeTag(tag: string) {
    const currentPayload = this.state.payload;
    let tags = currentPayload.tags?.filter((tagValue) => tagValue != tag);

    this.setState({
      payload: { ...currentPayload, tags, generate_tag: false },
    });
  }
  setPayload(payload: any) {
    const currentPayload = this.state.payload;
    const updatedPayLoad = { ...currentPayload, ...payload };
    for (let key in updatedPayLoad) {
      if (updatedPayLoad[key] == null) {
        delete updatedPayLoad[key];
      }
    }
    let finalTag: Set<string>;
    if (currentPayload.tags) {
      finalTag = new Set(currentPayload.tags);
    } else {
      finalTag = new Set();
    }
    if (updatedPayLoad.tags?.length > 0) {
      updatedPayLoad.tags.forEach((tag: string) => {
        finalTag.add(tag);
      });
    }
    updatedPayLoad.tags = Array.from(finalTag);
    this.setState({ payload: updatedPayLoad });
  }

  getSearchDataFromApi() {
    this.searchApi
      .getSearchResult(this.state.payload)
      .pipe(take(1))
      .subscribe({
        next: (response: SearchResultResponse) => {
          this.setSearchResultData(response);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status == 404) {
            this.setSearchResultData({
              tags: [],
              results: [],
              count: 0,
              next: null,
            });
            const currentPayload = this.state.payload;
            delete currentPayload?.tags;
            this.setPayload(currentPayload);
          }
        },
      });
  }

  resetToInitialState() {
    this.setState(initialState);
  }
}
