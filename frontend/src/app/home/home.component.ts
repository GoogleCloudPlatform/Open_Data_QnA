import { Component, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { HomeService } from '../shared/services/home.service';
import { ThemePalette } from '@angular/material/core';
import { MatSidenav } from '@angular/material/sidenav';
import { BreakpointObserver } from '@angular/cdk/layout';
import { LoginService } from '../shared/services/login.service';
import { Router } from '@angular/router';
import { Subject, Subscription, take, takeUntil } from 'rxjs';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  title = 'material-responsive-sidenav';
  isCollapsed = true;
  groupingsListCtrl = new FormControl<string>('');

  private _destroy$ = new Subject<void>();
  groupingsList: any;
  groupingString: any;
  checkStyle: boolean | undefined;
  userType: String | undefined;
  color: ThemePalette = 'accent';
  checkSideNav: string = 'Query';
  @ViewChild(MatSidenav)
  sidenav!: MatSidenav;
  isMobile = true;
  selectedGrouping: any;
  photoURL: any;
  reloadComp: boolean = false;
  userId: any;
  userSessions: any = [];
  userHistory: any = [];
  Subscription!: Subscription
  selectedHistory: any;
  selectedScenario: any;

  constructor(private homeService: HomeService, private observer: BreakpointObserver, private _router: Router, private loginService: LoginService) {
    this.loginService.getUserDetails().subscribe(message => {
      this.userId = message.uid;
      this.photoURL = message?.photoURL
    });
  }

  links = ['Business Mode', 'Technical Mode', 'Operational Mode'];
  activeLink = this.links[0];
  background: ThemePalette = undefined;

  toggleBackground() {
    this.background = this.background ? undefined : 'primary';
  }

  addLink() {
    this.links.push(`Link ${this.links.length + 1}`);
  }
  async ngOnInit() {
    if (!this.photoURL) {
      this._router.navigate(['']);
    }
    this.observer.observe(['(max-width: 800px)']).subscribe((screenSize) => {
      if (screenSize.matches) {
        this.isMobile = true;
      } else {
        this.isMobile = false;
      }
    });
    if (this.userId) {
      this.Subscription = this.homeService.getUserSessions(this.userId)
        .pipe(takeUntil(this._destroy$))
        .subscribe({
          next: (res: any) => {
            this.userSessions = res;
          },
          error: (error: any) => {
            throw error;
          },
          complete: () => {
            //console.log("complete")
          }
        })
    }
    this.groupingValAndKnownSql()
  }
  groupingValAndKnownSql() {
    this.homeService.setSelectedDbGrouping("");
    this.groupingString = this.homeService.getAvailableDBList();
    if (this.groupingString !== null && this.groupingString !== undefined) {
      this.groupingsList = JSON.parse(this.groupingString);
      this.homeService.currentSelectedGrouping.next('');
      this.homeService.currentSelectedGroupingObservable.subscribe((res) => {
        this.groupingsListCtrl.setValue(res);
        if (!res) {
          this.homeService.sqlSuggestionList("", "").subscribe((data: any) => {
            if (data && data.ResponseCode === 200) {
              this.homeService.knownSqlFromDb.next(data.KnownSQL);
            }
          })
        }
      })
    } else {
      this.homeService.getAvailableDatabases().subscribe((res: any) => {
        if (res && res.ResponseCode === 200) {
          this.groupingsList = JSON.parse(res.KnownDB);
        }
      });
    }
  }
  changeDb(dbtype: any) {
    let selectedDbtype = dbtype.target.value.split("-");
    this.homeService.setSelectedDbGrouping(dbtype.target.value);
    this.homeService.setSessionId('');
    this.homeService.setselectedDbName(selectedDbtype[1])
    this.homeService.currentSelectedGrouping.next(dbtype.target.value)
    this.homeService.sqlSuggestionList(dbtype.target.value, selectedDbtype[1]).subscribe((data: any) => {
      if (data && data.ResponseCode === 200) {
        this.homeService.knownSqlFromDb.next(data.KnownSQL);
      }
    })
  }

  updateBackgroundStyle(data: boolean) {
    this.checkStyle = data;
  }
  checkSideNavTAb(data: any) {
    if (data == 'New Query') {
      this.reloadComp = true;
    }
    this.checkSideNav = data;
  }

  sendHistory(data: any) {
    this.selectedHistory = data
  }

  toggleMenu() {
    if (this.isMobile) {
      this.sidenav.toggle();
    } else {
      // do nothing for now
    }
  }

  ngOnDestroy() {
    this.userHistory = [];
    this.Subscription?.unsubscribe();
    this._destroy$.next()
  }
}
