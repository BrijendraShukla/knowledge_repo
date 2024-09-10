import { TestBed } from '@angular/core/testing';

import { MasterStore } from './master.store';

describe('MasterStoreService', () => {
  let service: MasterStore;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MasterStore);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
