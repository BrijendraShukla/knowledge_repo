import { Injectable } from '@angular/core';
import { StateService } from './state.service';
import { Observable } from 'rxjs';

const initialState: { showLoader: boolean } = { showLoader: false };
@Injectable({
  providedIn: 'root',
})
export class LoaderService extends StateService<any> {
  constructor() {
    super(initialState);
  }

  showLoader$: Observable<boolean> = this.select((state) => state.showLoader);

  showLoader() {
    this.setState({ showLoader: true });
  }

  hideLoader() {
    this.setState({ showLoader: false });
  }
}
