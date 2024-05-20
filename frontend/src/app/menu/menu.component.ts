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


import { Component, Input, EventEmitter, Output } from '@angular/core';
import { ThemePalette } from '@angular/material/core';
import { Router } from '@angular/router';


@Component({
  selector: 'app-menu',

  templateUrl: './menu.component.html',
  styleUrl: './menu.component.scss'
})
export class MenuComponent {
  clickedItem: 'Query' | 'Reports' | 'History' | 'Saved'|'Operations Mode' | 'My workspace'| 'Team workspaces' |'Recent' |'Shared with me'|'Trash'|'Templates'  |undefined;
  color: ThemePalette = 'accent';
  checked = false;
  disabled = true;
// @Input() chekckuserType: any ;
@Output() selectedTab = new EventEmitter<string>();

    userType: any;
    constructor(public _router: Router) {
      }
  ngOnInit(){
    this.clickedItem = 'Query';
    this.selectedTab.emit(this.clickedItem);

    // this.userType= this.checkuserType;
    
  }

  onClick(item: 'Query' | 'Reports' | 'History'| 'Saved' |'Operations Mode'| 'My workspace' |'Team workspaces' | 'Recent' |'Shared with me' | 'Trash' | 'Templates' ) {
        this.clickedItem = item;
        this.selectedTab.emit(this.clickedItem);
    
  }
}
