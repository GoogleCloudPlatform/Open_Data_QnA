import { Component, Input, EventEmitter, Output, signal, SimpleChanges, inject, ViewChild } from '@angular/core';
import { ThemePalette } from '@angular/material/core';
import { Router } from '@angular/router';
import { HomeService } from '../shared/services/home.service';
import { GroupingModalComponent } from '../grouping-modal/grouping-modal.component';
import { MatDialog } from '@angular/material/dialog';
import { ScenarioListComponent } from '../scenario-list/scenario-list.component';
import { ChatService } from '../shared/services/chat.service';
import { LoginService } from '../shared/services/login.service';
import { UploadTemplateComponent } from '../upload-template/upload-template.component';

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrl: './menu.component.scss',

})
export class MenuComponent {
  clickedMenuItem: 'Query' | 'New Query' | 'Reports' | 'History' | 'Operations Mode' | 'My workspace' | 'Team workspaces' | 'Recent' | 'Shared with me' | 'Trash' | 'Templates' | 'Scenarios' | undefined;
  color: ThemePalette = 'accent';
  checked = false;
  disabled = true;
  @Input('userHistory') userHistory: any
  @Input('userSessions') userSessions: any;
  @Output() selectedTab = new EventEmitter<string>();
  @Output() selectedHistory = new EventEmitter<string>();
  panelOpenState = signal(false);
  scenarioPanelOpenState = signal(false)
  readonly dialog = inject(MatDialog);
  userType: any;
  recentHistory: any;
  showMoreHistory: any;
  selectedGrouping: string = '';
  csvData: any;
  @ViewChild(ScenarioListComponent)
  child!: ScenarioListComponent;
  userId: any;
  showUploadSection: boolean = false;

  constructor(public _router: Router, public homeService: HomeService, public chatService: ChatService, public loginService: LoginService) {
    this.clickedMenuItem = 'Query';
  }
  ngOnInit() {
    // this.homeService.currentSelectedGroupingObservable.subscribe((res) => {
    //   this.selectedGrouping = res
    // })
    this.loginService.getUserDetails().subscribe((res: any) => {
      this.userId = res.uid;
    });
    this.selectedTab.emit(this.clickedMenuItem);
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
              return b.chatThread[0].timestamp - a.chatThread[0].timestamp
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
  onMenuClick(item: 'Query' | 'New Query' | 'Reports' | 'History' | 'Operations Mode' | 'My workspace' | 'Team workspaces' | 'Recent' | 'Shared with me' | 'Trash' | 'Templates' | 'Scenarios') {
    this.clickedMenuItem = item;
    this.selectedGrouping = this.homeService.getSelectedDbGrouping();

    if (this.clickedMenuItem == 'New Query') {
      this.chatService.createNewSession();
      this.homeService.setSessionId('')
      this.child?.resetSelectedScenario()
    }
    this.selectedTab.emit(this.clickedMenuItem);
  }
  onClickHistory(chatThread: any) {
    this.child?.resetSelectedScenario()

    this.selectedGrouping = this.homeService.getSelectedDbGrouping();
    if (this.selectedGrouping) {
      this.homeService.updateChatMsgs(chatThread)
      this.chatService.createNewSession()
      this.homeService.setSessionId(chatThread[0].session_id)
      this.homeService.updateSelectedHistory(chatThread)
      this.chatService.addQuestion(chatThread[chatThread?.length - 1]?.user_question, this.userId, 'history', chatThread)
      // this.sessionId = this.homeService.getSessionId()

      this.selectedHistory.emit(chatThread);
    } else {
      this.openDialog();
    }
  }

  openDialog() {
    this.panelOpenState = signal(false);
    let dialogRef = this.dialog.open(GroupingModalComponent, {
      disableClose: true,
      width: '450px',
    });

    dialogRef.afterClosed().subscribe(result => {
    });
  }

  uploadTemplate() {
    let dialogRef = this.dialog.open(UploadTemplateComponent, {
      disableClose: true,
      width: '450px',
    });

    dialogRef.afterClosed().subscribe(result => {
      this.showUploadSection = result
      console.log(`Dialog result: ${result}`);
    });

  }
  onFileChange(fileInput: any) {
    if (fileInput) {
      const file: File = fileInput.files[0];
      let reader: FileReader = new FileReader();
      reader.readAsText(file);
      reader.onload = (e) => {
        let csv: any = reader.result;
        csv = csv.split('\n')
        for (let i = 0; i < csv.length; i++) {
         csv[i] = csv[i].replace(/(\r\n|\n|\r)/gm,"");
          csv[i] = csv[i].split(',');
          if (i != 0) { // 0th element has the column header 
            csv[i] = this.arrToObject(csv[i], csv[0]);
          }
        }
        this.panelOpenState = signal(false)
        this.csvData = csv.slice(1);
      }
    }
  }
  arrToObject(arr: any[], header: any[]) {
    let rv: any = {};
    for (let i = 0; i < arr.length; ++i)
      if (arr[i] !== undefined && arr.length == header.length) {
        rv[header[i]] = arr[i];
      }
    return rv;
  }
}
