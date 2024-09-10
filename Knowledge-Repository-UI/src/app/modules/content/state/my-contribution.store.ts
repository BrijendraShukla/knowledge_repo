import { Injectable } from '@angular/core';
import { Observable, take } from 'rxjs';
import { StateService } from '../../../state/state.service';
import {
  MyContributionApiResponse,
  myContributionData,
  myContributionPayload,
  MyContributionStateModel,
} from '../models/content.model';
import { ContentApiService } from '../agents/content-api.service';

let initialState: MyContributionStateModel = {
  data: {
    results: [],
    count: 0,
    next: null,
  },
  payload: {
    // pageSize: 10,
    // pageNumber: 1,
  },
};
@Injectable({ providedIn: 'root' })
export class MyContributionStore extends StateService<MyContributionStateModel> {
  constructor(private contentApi: ContentApiService) {
    super(initialState);
  }
  myContributionData$: Observable<myContributionData> = this.select(
    (state) => state.data
  );

  payload$: Observable<myContributionPayload> = this.select(
    (state) => state.payload
  );
  setContributionData(data: myContributionData) {
    this.setState({ data });
  }

  setPayload(payload: any) {
    console.log(payload);
    const currentPayload = this.state.payload;
    const updatedPayLoad = { ...currentPayload, ...payload };
    for (let key in updatedPayLoad) {
      if (updatedPayLoad[key] == null) {
        delete updatedPayLoad[key];
      }
    }
    this.setState({ payload: updatedPayLoad });
  }

  getContributionDataFromApi() {
    this.contentApi
      .getContibutionList(this.state.payload)
      .pipe(take(1))
      .subscribe((response: MyContributionApiResponse) => {
        this.setContributionData({
          results: response.results,
          count: response.count,
          next: response.next,
        });
      });
  }

  updateListFromApi() {
    const page_size = this.state.data.results.length;
    const payload = { ...this.state.payload, page_size };
    this.contentApi
      .getContibutionList(payload)
      .pipe(take(1))
      .subscribe((response: MyContributionApiResponse) => {
        this.setContributionData({
          ...this.state.data,
          results: response.results,
          count: response.count,
        });
      });
  }

  resetToInitialState() {
    this.setState(initialState);
  }

  getNextPage() {
    this.contentApi
      .getNextContributionList(this.state.data.next!)
      .pipe(take(1))
      .subscribe((response: MyContributionApiResponse) => {
        const updatedDataList = [
          ...this.state.data.results,
          ...response.results,
        ];

        this.setContributionData({
          results: updatedDataList,
          count: response.count,
          next: response.next,
        });
      });
  }
}
