import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ContentActionComponent } from './content-action.component';

describe('ContentActionComponent', () => {
  let component: ContentActionComponent;
  let fixture: ComponentFixture<ContentActionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ContentActionComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ContentActionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
