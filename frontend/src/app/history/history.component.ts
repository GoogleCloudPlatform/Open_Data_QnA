import { Component } from '@angular/core';
import { HomeService } from '../shared/services/home.service';
import { LoginService } from '../shared/services/login.service';

/**
 * @title Basic use of `<table mat-table>`
 */
@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss'
})
export class HistoryComponent {
  displayedColumns: string[] = ['name', 'ownedBy', 'lastOpened'];
  userSessions: any
  userId: any;
  constructor(public homeService: HomeService, public loginService: LoginService) {
    this.loginService.getUserDetails().subscribe((res: any) => {
      this.userId = res.uid;
    })
  }
  ngOnInit() {
    this.homeService.getUserSessions(this.userId)
      .subscribe((res: any) => {
        this.userSessions = res;
       // console.log(this.userSessions.slice(0, 3))
      })
  }
}
