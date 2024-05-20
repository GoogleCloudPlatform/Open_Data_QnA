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


import { Dialog } from '@angular/cdk/dialog';
import { Component } from '@angular/core';
import { LoginService } from '../shared/services/login.service';
import { SharedService } from '../shared/services/shared.service';

@Component({

  selector: 'app-login-button',
  // standalone: true,
  templateUrl: './login-button.component.html',
  styleUrl: './login-button.component.scss'
})
export class LoginButtonComponent {
  photoURL: any;
  userLoggedIn: boolean = false;
  constructor(public fireservice: SharedService, public loginService: LoginService,
    public dialog: Dialog) {
  }
  getLogin() {
    this.fireservice.googleSignin().then((res => {
      this.userLoggedIn = true;
      this.photoURL = res?.photoURL;
      this.dialog.closeAll()
      this.updateData(res);
    }))
  }

  updateData(userDetails: any): void {
    this.loginService.sendUserDetails(userDetails);
  }
}
