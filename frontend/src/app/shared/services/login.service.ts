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


import { Injectable } from '@angular/core';
import { Observable, ReplaySubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoginService {

  constructor() { }
  private userDetails = new ReplaySubject<any>(1);
  userDetails$: Observable<any> = this.userDetails.asObservable();
  loginErrorMsg: any = new ReplaySubject<any>(1);
  getLoginError(): any {
    return this.loginErrorMsg;
  }
  updateLoginError(msg: any) {
    this.loginErrorMsg.next(msg)
  }
  getUserDetails(): Observable<any> {
    return this.userDetails$;
  }

  sendUserDetails(message: any) {
    this.userDetails.next(message);
  }
}
