/*
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


import {Component} from '@angular/core';
import {MatTableModule} from '@angular/material/table';

export interface ReportData {
  name: string;
  ownedBy: string;
  lastOpened: string;
}

const ELEMENT_DATA: ReportData[] = [
  { name: 'Analysis Jan 2022', ownedBy: 'John Smith', lastOpened: 'Feb 10, 2022'},
  { name: 'Analysis Jan 2022', ownedBy: 'John Smith', lastOpened: 'Feb 10, 2022'},
  { name: 'Analysis Jan 2022', ownedBy: 'John Smith', lastOpened: 'Feb 10, 2022'},
  { name: 'Analysis Jan 2022', ownedBy: 'John Smith', lastOpened: 'Feb 10, 2022'},
  { name: 'Analysis Jan 2022', ownedBy: 'John Smith', lastOpened: 'Feb 10, 2022'},
  { name: 'Analysis Jan 2022', ownedBy: 'John Smith', lastOpened: 'Feb 10, 2022'}
];

/**
 * @title Basic use of `<table mat-table>`
 */
@Component({
    selector: 'app-results',
    templateUrl: './reports.component.html',
    styleUrl: './reports.component.scss'
})
export class ReportsComponent {
  displayedColumns: string[] = ['name', 'ownedBy', 'lastOpened'];
  dataSource = ELEMENT_DATA;
}
