import { Component, Input, EventEmitter, Output, signal, SimpleChanges, inject } from '@angular/core';
import { ThemePalette } from '@angular/material/core';
import { Router } from '@angular/router';
import { HomeService } from '../shared/services/home.service';
import { GroupingModalComponent } from '../grouping-modal/grouping-modal.component';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrl: './menu.component.scss'
})
export class MenuComponent {
  clickedItem: 'Query' | 'New Query' | 'Reports' | 'History' | 'Operations Mode' | 'My workspace' | 'Team workspaces' | 'Recent' | 'Shared with me' | 'Trash' | 'Templates' | undefined;
  color: ThemePalette = 'accent';
  checked = false;
  disabled = true;
  @Input('userHistory') userHistory: any
  @Input('userSessions') userSessions: any;
  @Output() selectedTab = new EventEmitter<string>();
  @Output() selectedHistory = new EventEmitter<string>();
  panelOpenState = signal(false);
  readonly dialog = inject(MatDialog);
  userType: any;
  recentHistory: any;
  showMoreHistory: any;
  selectedGrouping: string = '';
  constructor(public _router: Router, public homeService: HomeService) {
    this.clickedItem = 'Query';
  }
  ngOnInit() {
    this.selectedTab.emit(this.clickedItem);
  }

  ngOnChanges(changes: SimpleChanges) {
    for (const propName in changes) {
      if (changes.hasOwnProperty(propName)) {
        switch (propName) {
          case 'userSessions': {
            //group user sessions based on session id
            let grouped = this.userSessions?.reduce(
              (result: any, currentValue: any) => {
                (result[currentValue['session_id']] = result[currentValue['session_id']] || []).push(currentValue);
                return result;
              }, {});
            //map the grouped user sessions as a chatThread , sort and display in side nav
            let sessionToDisplayQuery: any = []
            Object.keys(grouped).map(function (sessionId: string) {
              let chatThreadArray: any[] = grouped[sessionId];
              let obj = {
                'sessionId': sessionId,
                'question': chatThreadArray[chatThreadArray.length - 1].user_question,
                'chatThread': chatThreadArray,
                'timestamp': chatThreadArray[chatThreadArray.length - 1].timestamp.seconds
              }
              sessionToDisplayQuery.push(obj);
            });

            sessionToDisplayQuery?.sort((a: any, b: any) => {
              return b.timestamp - a.timestamp
            });
            this.userHistory = sessionToDisplayQuery;
            this.recentHistory = this.userHistory.slice(0, 5);
          }
            break;
        }
      }
    }
  }
  showMore() {
    this.showMoreHistory = this.userHistory.slice(5, 10)
  }
  onClick(item: 'Query' | 'New Query' | 'Reports' | 'History' | 'Operations Mode' | 'My workspace' | 'Team workspaces' | 'Recent' | 'Shared with me' | 'Trash' | 'Templates') {
    this.clickedItem = item;
    if (this.clickedItem == 'History') {
      this.selectedGrouping = this.homeService.getselectedDb();
      if (!this.selectedGrouping) {
        this.openDialog();
      }

    }
    this.selectedTab.emit(this.clickedItem);
  }
  onClickHistory(chatThread: any) {
    this.selectedHistory.emit(chatThread)
  }

  openDialog() {
    this.panelOpenState = signal(false);
    let dialogRef = this.dialog.open(GroupingModalComponent, {
      disableClose: true,
      width: '450px',
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log(`Dialog result: ${result}`);
    });
  }

}
