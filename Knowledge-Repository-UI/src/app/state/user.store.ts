import { Injectable } from '@angular/core';
import { StateService } from './state.service';
import { BehaviorSubject, Observable } from 'rxjs';

interface InitialStateModel {
  id: number;
  email: string;
  token: string;
  name: string;
}

let initialState: InitialStateModel = {
  id: 0,
  email: '',
  token: '',
  name: 'Steve Smith',
};
@Injectable({
  providedIn: 'root',
})
export class UserStore extends StateService<InitialStateModel> {
  constructor() {
    super(initialState);
  }
  showSideNav$: BehaviorSubject<boolean> = new BehaviorSubject(false);
  user$: Observable<{
    id: number;
    email: string;
    token: string;
    name: string;
  }> = this.select((user) => user);
  setUser(user: any) {
    this.setState(user);
  }
}
