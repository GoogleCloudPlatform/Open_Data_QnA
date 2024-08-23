import { Component } from '@angular/core';
import { LoginService } from '../shared/services/login.service';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { HomeService } from '../shared/services/home.service';
import { ThemePalette } from '@angular/material/core';

@Component({
  selector: 'app-user-journey',
  // standalone: true,
  templateUrl: './user-journey.component.html',
  styleUrl: './user-journey.component.scss'
})
export class UserJourneyComponent {
  photoURL: string | undefined;
  subscription: Subscription | undefined;
  showProgress: boolean = false
  color: ThemePalette = 'accent';
  loginError = false;
  loginErrorMessage: any;
  demoVideo = false;
  constructor(public _router: Router, public loginService: LoginService, public homeService: HomeService) {
    this.subscription = this.loginService.getUserDetails().subscribe(message => {
      this.photoURL = message?.photoURL;
      if (!this.photoURL) {
        this._router.navigate(['']);
      }
    });
  }

  onDemoVideoClick(){
    this.demoVideo = true;
  }
  ngOnInit() {

    // this.loginService.getLoginError().subscribe((res: any) => {
    //   this.loginErrorMessage = res
    //   this.loginError = true;
    //   if(this.loginError){
    //     this._router.navigate(['']);
    //   }
    // });

  }

  userJourneyList: any = [{
    userId: "User journey 1",
    userTitle: "Business User",
    userContent: [
      "This demo will help you to ask the questions in natural language, view the SQL, get results and visualize data",
    ]
  }];

  async navigateToHome(userTitle: String) {

    if (userTitle === 'Business User') {
      //this.homeService.checkuserType = 'Business';
      this.showProgress = true;
      this.homeService.getAvailableDatabases().subscribe((res: any) => {
        if (res && res.ResponseCode === 200) {
          this.homeService.setAvailableDBList(res.KnownDB);
          this.showProgress = false;
          this._router.navigate(['home-page']);
        }
      })
    }
  }

  ngOnDestroy() {
    this.subscription?.unsubscribe()
  }
}
