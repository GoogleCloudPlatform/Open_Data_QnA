import { Component, inject } from '@angular/core';
import { LoginButtonComponent } from '../login-button/login-button.component';
import { Subscription, take } from 'rxjs';
import { Auth, User, user } from '@angular/fire/auth';
import { Router } from '@angular/router';
import { LoginService } from '../shared/services/login.service';
import { Dialog } from '@angular/cdk/dialog';

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
    this.dialog.closeAll();
    this.userSubscription = this.user$.pipe(take(1)).subscribe((aUser: User | null) => {
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

  // ngOnInit() {
  //   if (!this.photoURL) {
  //     this.showLogIn()
  //   }
  // }

  showLogIn(): void {
    this.dialog.open(LoginButtonComponent, {
      disableClose: true,
      width: '350px',
      panelClass: 'login-container'
    });
  }

  ngOnDestroy() {
    this.dialog.closeAll();
    // when manually subscribing to an observable remember to unsubscribe in ngOnDestroy
    this.userSubscription.unsubscribe();
    // this.idTokenSubscription.unsubscribe();
  }
}
