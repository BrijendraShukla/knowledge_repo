import { TestBed } from '@angular/core/testing';

import { MyContributionStore } from './my-contribution.store';

describe('ContributionStore', () => {
  let service: MyContributionStore;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MyContributionStore);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
