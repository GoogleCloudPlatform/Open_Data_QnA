import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupingModalComponent } from './grouping-modal.component';

describe('GroupingModalComponent', () => {
  let component: GroupingModalComponent;
  let fixture: ComponentFixture<GroupingModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupingModalComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(GroupingModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
