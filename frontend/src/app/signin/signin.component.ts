import { Component, inject } from '@angular/core';
import { AuthGoogleService } from '../shared/services/auth-google.service';

@Component({
  selector: 'app-signin',
  templateUrl: './signin.component.html',
  styleUrl: './signin.component.scss'
})
export class SigninComponent {
  private authService = inject(AuthGoogleService);

  constructor(){
    console.log("I am in signin const")
  }

  signInWithGoogle() {
    console.log("I am in signin")
    this.authService.login();
  }
}
