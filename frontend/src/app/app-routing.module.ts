import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { UserJourneyComponent } from './user-journey/user-journey.component';
import { HomeComponent } from './home/home.component';
import { BusinessUserComponent } from './business-user/business-user.component';

const routes: Routes = [
  { path: '', component: LoginComponent },
  { path: 'user-journey', component: UserJourneyComponent },
  { path: 'home-page', component: HomeComponent },
  { path: 'business-mode', component: BusinessUserComponent },
]

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
