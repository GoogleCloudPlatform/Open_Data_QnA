import { Injectable } from '@angular/core';
import { Observable, ReplaySubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoginService {
  constructor() { }
  private userDetails = new ReplaySubject<any>(1);
  userDetails$: Observable<any> = this.userDetails.asObservable();

  private idToken = new ReplaySubject<any>(1);
  idToken$: Observable<any> = this.idToken.asObservable();
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

  getIdToken(): any {
    return this.idToken$;
  }

  setIdToken(token: any) {
    this.idToken.next(token);
  }
}
