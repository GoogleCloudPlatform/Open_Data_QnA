import { Component, ChangeDetectorRef, Output, EventEmitter, Input, SimpleChanges, inject } from '@angular/core';
import { LoginService } from '../shared/services/login.service';
import { FormControl, FormGroup } from '@angular/forms';
import { HomeService } from '../shared/services/home.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Timestamp } from '@angular/fire/firestore'
import { Subject, Subscription, takeUntil } from 'rxjs';
import { Router } from '@angular/router';
import { GroupingModalComponent } from '../grouping-modal/grouping-modal.component';
import { MatDialog } from '@angular/material/dialog';

export interface Tabledata {
  city_id: string;
}

type Author = "User" | "Agent" | "System";

export interface ChatMessage {
  author: Author,
  language: string,
  user_question: string,
  timestamp?: Timestamp,
  link?: string,
  iconURL?: string,
  sentiment_score?: number;
  sentiment_magnitude?: number
}

@Component({
  selector: 'app-business-user',
  templateUrl: './business-user.component.html',
  styleUrl: './business-user.component.scss'
})
export class BusinessUserComponent {
  @Input('checkSideNav') checkSideNav: any
  @Input("selectedHistory")
  selectedHistory!: any;
  @Input('selectedGrouping') selectedGrouping: any
  @Input('userSessions') userSessions!: string;
  chatMsgs: any[] = [];
  userLoggedIn: boolean = false;
  photoURL: any;
  resultLoader: boolean = false;
  isSuggestions: boolean = true;
  suggestionList: any;
  showResult: boolean = false;
  generatedSql: any = {
    example_user_question: '',
    example_generated_sql: '',
    unfilteredSql: ''
  };
  @Output() updateStyleEvent = new EventEmitter<boolean>();
  setErrorCSS: boolean = false;
  readonly dialog = inject(MatDialog);
  isOpen: boolean = false;
  dataSet: string | undefined;
  showChart: boolean = false;
  showLoader: boolean = false;
  selectedFeedbackOption: any;
  dataSetName!: string;
  subscription!: Subscription;
  userId: any;
  private _destroy$ = new Subject<void>();
  sessionId !: string;

  constructor(public loginService: LoginService, public homeService: HomeService,
    private snackBar: MatSnackBar, private change: ChangeDetectorRef, public router: Router) {
    this.loginService.getUserDetails().subscribe((res: any) => {
      this.userId = res.uid;
      this.userLoggedIn = true;
      this.photoURL = res?.photoURL
    });
  }
  sqlSearchForm = new FormGroup({
    name: new FormControl(),
  });

  ngOnChanges(changes: SimpleChanges) {
    for (const propName in changes) {
      if (changes.hasOwnProperty(propName)) {
        switch (propName) {
          case 'checkSideNav': {
            if (this.checkSideNav === 'New Query') {
              let initialChat =
                [{
                  'author': 'agent',
                  'message': this.suggestionList,
                  'user_question': 'Looking for a specific insight or want to browse through your database? Ask what you are looking for in a natural language and Open Data QnA will translate to SQL and bring back results in natural language.'
                }];
              this.chatMsgs = []
              this.homeService.updateChatMsgs(initialChat);
              this.chatMsgs = this.homeService.getChatMsgs();
              this.homeService.setSessionId('')
              this.sessionId = ''
            };
          }
            break;
          case 'selectedHistory': {
            if (this.selectedHistory) {
              this.resultLoader = true;
              this.showResult = false;
              let initialChat =
                [{
                  'author': 'agent',
                  'message': this.suggestionList,
                  'user_question': 'Looking for a specific insight or want to browse through your database? Ask what you are looking for in a natural language and Open Data QnA will translate to SQL and bring back results in natural language.'
                }];
              this.chatMsgs = [];
              this.homeService.updateChatMsgs(initialChat);
              this.chatMsgs = this.homeService.getChatMsgs()
              for (let i = this.selectedHistory.length - 1; i >= 0; i--) {
                this.chatMsgs.push({
                  'author': 'user',
                  'user_question': this.selectedHistory[i]?.user_question
                });
                this.chatMsgs.push({
                  'author': 'agent',
                  'user_question': this.selectedHistory[i]?.user_question,
                  'generate_sql': {
                    'GeneratedSQL': this.selectedHistory[i]?.bot_response,
                    'SessionID': this.selectedHistory[i]?.session_id,
                    "ResponseCode": 200
                  }
                });
                this.homeService.setSessionId(this.selectedHistory[i]?.session_id)
                this.sessionId = this.homeService.getSessionId()
              }
              this.homeService.updateChatMsgs(this.chatMsgs);
              this.chatMsgs = this.homeService.getChatMsgs()
              this.resultLoader = false;
            }
          }
            break;
          case 'selectedGrouping': {
            this.sessionId = "";
            this.homeService.setSessionId('')
            this.sessionId = this.homeService.getSessionId();
            this.chatMsgs = [];
            if (this.selectedHistory) {
              this.resultLoader = true;
              this.showResult = false;
              let initialChat =
                [{
                  'author': 'agent',
                  'message': this.suggestionList,
                  'user_question': 'Looking for a specific insight or want to browse through your database? Ask what you are looking for in a natural language and Open Data QnA will translate to SQL and bring back results in natural language.'
                }];
              this.chatMsgs = [];
              this.homeService.updateChatMsgs(initialChat);
              this.chatMsgs = this.homeService.getChatMsgs()
              this.resultLoader = false;
            }
          }
        }
      }
    }
  }
  ngOnInit() {
    this.sessionId = '';
    if (this.checkSideNav === 'New Query') {
      this.reloadComponent(true);
    }
    this.chatMsgs = []

    this.subscription = this.homeService.databaseObservable?.pipe(takeUntil(this._destroy$)).subscribe((response: any) => {
      if (response && response != null) {
        this.showResult = false;
        this.chatMsgs = []
        this.suggestionList = JSON.parse(response);
        let initialChat =
          [{
            'author': 'agent',
            'message': this.suggestionList,
            'user_question': 'Looking for a specific insight or want to browse through your database? Ask what you are looking for in a natural language and Open Data QnA will translate to SQL and bring back results in natural language.'
          }]
        this.homeService.updateChatMsgs(initialChat);
        this.chatMsgs = this.homeService.getChatMsgs();
      }
      this.dataSet = this.homeService.getselectedDb();
      this.dataSetName = this.homeService.getselectedDbName();
    });
  }
  reloadComponent(self: boolean, urlToNavigateTo?: string) {
    //skipLocationChange:true means dont update the url to / when navigating
    console.log("Current route I am on:", this.router.url);
    const url = self ? this.router.url : urlToNavigateTo;
    this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
      this.router.navigate([`/${url}`]).then(() => {
        console.log(`After navigation I am on:${this.router.url}`)
      })
    })
  }
  followUp(query: any, event?: any) {
    if (this.dataSet) {
      event?.preventDefault();
      if (this.sqlSearchForm.controls.name?.value !== null) {
        this.resultLoader = true;
        this.showResult = false;
        this.chatMsgs = this.homeService.getChatMsgs()
        this.chatMsgs.push({
          'author': 'user',
          'user_question': query
        });
        this.homeService.updateChatMsgs(this.chatMsgs);
        this.generate_sql(query);
      } else {
        this.setErrorCSS = true;
      }
    } else {
      let dialogRef = this.dialog.open(GroupingModalComponent, {
        disableClose: true,
        width: '450px',
      });

      dialogRef.afterClosed().subscribe(result => {
        console.log(`Dialog result`);
      });

    }
  }

  generate_sql(query: any) {
    this.sqlSearchForm.controls['name'].setValue("");
    this.homeService.generateSql(query, this.homeService.getselectedDb(), this.sessionId, this.userId).subscribe((response: any) => {
      if (response && response.ResponseCode === 200) {
        this.resultLoader = false
        this.showResult = true;
        this.generatedSql.example_user_question = query;
        this.homeService.setSessionId(response.SessionID)
        this.sessionId = this.homeService.getSessionId()
        // this.sessionId = response.SessionID
        this.chatMsgs = this.homeService.getChatMsgs()
        this.chatMsgs.push({
          'author': 'agent',
          'user_question': query,
          'generate_sql': response,
        })
        this.homeService.updateChatMsgs(this.chatMsgs);
        //this.change.markForCheck();
      }
      else if (response && response.ResponseCode != 200) {
        this.chatMsgs.push({
          'author': 'agent',
          'generate_sql': response,
        });
        this.homeService.setSessionId(response.SessionID)
        this.sessionId = this.homeService.getSessionId();
        //  this.sessionId = response.SessionID
        this.resultLoader = false;
      }
    })
  }
  suggestionResult(selectedsql: any) {
    this.showResult = true;
    this.chatMsgs = this.homeService.getChatMsgs()
    this.chatMsgs.push(
      {
        'author': 'user',
        'user_question': selectedsql.example_user_question,
      }
    );
    this.homeService.updateChatMsgs(this.chatMsgs);
    this.resultLoader = true;
    this.generatedSql.example_user_question = selectedsql.example_user_question;
    this.updateStyleEvent.emit(this.showResult);
    this.generate_sql(selectedsql.example_user_question);
    //this.change.markForCheck();
  }

  showSnackbarCssStyles(content: any, action: any, duration: any) {
    let sb = this.snackBar.open(content, action, {
      duration: duration,
      panelClass: ["custom-style"]
    });
    sb.onAction().subscribe(() => {
      sb.dismiss();
    });
  }
  updateStyleItem(value: boolean) {
    this.updateStyleEvent.emit(value);
  }
  showContentCopiedMsg() {
    this.showSnackbarCssStyles("Content Copied", 'Close', '4000')
  }

  ngOnDestroy() {
    this.chatMsgs = [];
    this.subscription.unsubscribe();
    this._destroy$.next();
    console.log(this.sessionId)
    this.sessionId = ""
  }
}
