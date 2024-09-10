import { Injectable } from '@angular/core';
import { StateService } from './state.service';
import { ToasterData } from '../models/model';
import { Observable } from 'rxjs';

interface initialStateModel {
  toasterData: ToasterData[];
}
const initialState: initialStateModel = { toasterData: [] };
@Injectable({
  providedIn: 'root',
})
export class ToasterService extends StateService<any> {
  constructor() {
    super(initialState);
  }
  toasterData$: Observable<ToasterData[]> = this.select(
    (state) => state.toasterData
  );

  showToater(data: ToasterData) {
    let currentToasterData: Array<ToasterData> = this.state.toasterData;
    currentToasterData.push(data);
    this.setState({ toasterData: currentToasterData });
    setTimeout(() => {
      this.closeToaster(data);
    }, 3000);
  }
  closeToaster(data: ToasterData) {
    let toasterData: Array<ToasterData> = this.state.toasterData;
    let index = toasterData.findIndex((obj) => (obj.msg = data.msg));
    if (index !== -1) {
      toasterData.splice(index, 1);
    }
    this.setState({ toasterData });
  }
}
