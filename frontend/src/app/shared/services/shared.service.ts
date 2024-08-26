import { Injectable, inject } from '@angular/core';
import { LoginService } from './login.service';
import { GoogleAuthProvider, signInWithPopup } from '@firebase/auth';
import { Auth } from '@angular/fire/auth';

@Injectable({
  providedIn: 'root'
})
export class SharedService {
  userData: any;
  private auth: Auth = inject(Auth);

  constructor(public loginservice: LoginService) { }

  async googleSignin() {
    const provider = new GoogleAuthProvider();

    return await signInWithPopup(this.auth, provider)
      .then(async (result) => {
        const token = await this.auth.currentUser?.getIdToken(); 
        this.loginservice.setIdToken(token); 
        return result.user;
      }).
      catch((error) => {
        if (error.message.indexOf('Cloud Function') === 15) {
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

