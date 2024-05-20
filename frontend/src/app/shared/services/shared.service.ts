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


import { Injectable, inject } from '@angular/core';
import { LoginService } from './login.service';
import { Firestore } from '@angular/fire/firestore';
import { GoogleAuthProvider, signInWithPopup } from '@firebase/auth';
import { Auth } from '@angular/fire/auth';
import { AngularFireAuth } from '@angular/fire/compat/auth';

@Injectable({
  providedIn: 'root'
})
export class SharedService {
  userData: any;
  private auth: Auth = inject(Auth);


  constructor(private fs: Firestore, public loginservice: LoginService,
    private afAuth: AngularFireAuth
  ) { }


  async googleSignin() {
    const provider = new GoogleAuthProvider();

    return await signInWithPopup(this.auth, provider)
      .then((result) => {
        return result.user
      }).
      catch((error) => {
        if (error.message.indexOf('Cloud Function') === 15) {
          // console.log(error.message.indexOf('Cloud Function'))
          // console.log(error.message)
          const jsonStart = error.message.indexOf('{');
          const jsonEnd = error.message.lastIndexOf('}');
          const jsonString = error.message.substring(jsonStart, jsonEnd + 1);
          const errorObject = JSON.parse(jsonString);
          this.loginservice.updateLoginError(errorObject.error.message)
        } else {
          this.loginservice.updateLoginError(error.message)
        }
      });
  }
}

