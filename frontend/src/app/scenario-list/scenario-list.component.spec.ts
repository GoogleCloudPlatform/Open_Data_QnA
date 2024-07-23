import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioListComponent } from './scenario-list.component';

describe('ScenarioListComponent', () => {
  let component: ScenarioListComponent;
  let fixture: ComponentFixture<ScenarioListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ScenarioListComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ScenarioListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
