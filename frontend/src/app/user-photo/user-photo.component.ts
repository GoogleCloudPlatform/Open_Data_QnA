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


import { Component, inject } from '@angular/core';
import { LoginButtonComponent } from '../login-button/login-button.component';
import { Subscription } from 'rxjs';
import { Auth, User, user } from '@angular/fire/auth';
import { Router } from '@angular/router';
import { LoginService } from '../shared/services/login.service';
import { Dialog } from '@angular/cdk/dialog';
import { LoadPopupComponent } from '../load-popup/load-popup.component';

@Component({
  selector: 'app-user-photo',
  templateUrl: './user-photo.component.html',
  styleUrl: './user-photo.component.scss'
})
export class UserPhotoComponent {
  photoURL: string | undefined;
  subscription: Subscription | undefined;
  userLoggedIn: boolean = false;
  private auth: Auth = inject(Auth);
  user$ = user(this.auth);
  userSubscription: Subscription;

  constructor(private _router: Router, public dialog: Dialog, public loginService: LoginService) {
    this.userSubscription = this.user$.subscribe((aUser: User | null) => {
      //handle user state changes here. Note, that user will be null if there is no currently logged in user
      if (aUser) {
        this.dialog.closeAll();
        this.userLoggedIn = true;
        this.loginService.sendUserDetails(aUser)
        if (aUser.photoURL) {
          this.photoURL = aUser.photoURL;
        }
      }
      else {
        this.userLoggedIn = false;
        this.showLogIn()
      }
    })
  }

  ngAfterViewInit() {
    if (!this.photoURL) {
      this.showLogIn()
    }
  }

  navigateToUserJourney() {
    this.userLoggedIn = true;
    this._router.navigate(['user-journey'])
  }


  showLogIn(): void {
    this.dialog.open(LoginButtonComponent, {
      disableClose: true,
      width: '350px',
      panelClass: 'login-container'
    });
  }

  ngOnDestroy() {
    // when manually subscribing to an observable remember to unsubscribe in ngOnDestroy
    this.userSubscription.unsubscribe();
  }
}
