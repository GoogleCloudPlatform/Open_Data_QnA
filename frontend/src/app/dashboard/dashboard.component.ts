import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthGoogleService } from '../shared/services/auth-google.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {
  private authService = inject(AuthGoogleService);
  private router = inject(Router);
  profile: any;

  ngOnInit(): void {
    this.showData();
  }

  showData() {
    this.profile = this.authService.getProfile();
    console.log(this.profile);
  }

  logOut() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

}
