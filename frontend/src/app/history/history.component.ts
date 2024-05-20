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

/**
 * @title Basic use of `<table mat-table>`
 */
@Component({
    selector: 'app-history',
    templateUrl: './history.component.html',
    styleUrl: './history.component.scss'
})
export class HistoryComponent {
  displayedColumns: string[] = ['name', 'ownedBy', 'lastOpened'];
}
