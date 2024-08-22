import { Component, ChangeDetectorRef, Output, EventEmitter, Input, SimpleChanges, inject } from '@angular/core';
import { LoginService } from '../shared/services/login.service';
import { FormControl, FormGroup } from '@angular/forms';
import { HomeService } from '../shared/services/home.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, Subscription, takeUntil } from 'rxjs';
import { Router } from '@angular/router';
import { GroupingModalComponent } from '../grouping-modal/grouping-modal.component';
import { MatDialog } from '@angular/material/dialog';
import { ChatService } from '../shared/services/chat.service';

export interface Tabledata {
  city_id: string;
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
  currentScenario: any;
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
  dataSetName!: string;
  userId: any;
  private _destroy$ = new Subject<void>();
  sessionId !: string;
  subscription!: Subscription;
  sub!: Subscription;
  //ind: number = 0;

  constructor(public loginService: LoginService, public homeService: HomeService, public chatService: ChatService,
    private snackBar: MatSnackBar, private change: ChangeDetectorRef, public router: Router) {
    this.loginService.getUserDetails().pipe(takeUntil(this._destroy$)).subscribe((res: any) => {
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
          case 'selectedHistory': {
            if (this.selectedHistory) {
              this.showResult = false;
              this.sessionId = this.homeService.getSessionId()
            }
          }
            break;
        }
      }
    }
  }
  ngOnInit() {
    this.sessionId = '';
    this.loadInitialChat();
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

  loadInitialChat() {
    this.chatService.chatSessionObservable.pipe(takeUntil(this._destroy$)).subscribe((res) => {
      this.chatMsgs = res.chatMsgs
      this.dataSet = this.homeService.getSelectedDbGrouping();
      this.dataSetName = this.homeService.getselectedDbName();
      this.sub = this.chatService.agentResponseLoader$.pipe(takeUntil(this._destroy$)).subscribe((res) => {
        this.resultLoader = res
      })
      this.sessionId = this.homeService.getSessionId()
    })
  }
  followUp(query: any, event?: any) {
    if (this.dataSet) {
      event?.preventDefault();
      if (this.sqlSearchForm.controls.name?.value !== null) {
        this.showResult = false;
        this.chatService.addQuestion(query, this.userId, "followup")
        this.sqlSearchForm.controls['name'].setValue("");
        this.chatService.agentResponseLoader.next(true)
        this.resultLoader = true;
        //  this.generate_sql(query);
      } else {
        this.setErrorCSS = true;
      }
    } else {
      let dialogRef = this.dialog.open(GroupingModalComponent, {
        disableClose: true,
        width: '450px',
      });

      dialogRef.afterClosed().subscribe(result => {
        
      });

    }
  }

  suggestionResult(selectedsql: any) {
    this.showResult = true;
    this.chatService.addQuestion(selectedsql.example_user_question, this.userId, "followup")
    this.resultLoader = true;
    this.generatedSql.example_user_question = selectedsql.example_user_question;
    this.sqlSearchForm.controls['name'].setValue("");
    this.updateStyleEvent.emit(this.showResult);
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
    //this.subscription.unsubscribe();
    this._destroy$.next();
    this.sessionId = "";
    this.sub.unsubscribe()
  }
}
