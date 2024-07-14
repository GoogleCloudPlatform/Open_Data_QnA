import { AfterViewInit, Component, ElementRef, Input, ViewChild, signal } from '@angular/core';
import { HomeService } from '../shared/services/home.service';
import { format } from 'sql-formatter';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-agent-chat',
  templateUrl: './agent-chat.component.html',
  styleUrl: './agent-chat.component.scss'
})
export class AgentChatComponent implements AfterViewInit {
  msg: any;
  @Input('example_user_question') example_user_question: any;
  @Input('ind') ind: any;
  @Input('sessionId') sessionId: any;
  emptyMsg: any = '';
  @Input('suggestionList') suggestionList: any;
  showResult: boolean = false;
  private _destroy$ = new Subject<void>();
  showChart: boolean = false;
  showLoader: boolean = false;
  isOpen: boolean = false;
  selectedFeedbackOption: any;
  result: any;
  dataSet!: string;
  dataSetName!: string;
  displayedColumns: string[] = [];
  dataSource: any[] = [];
  feedbackForm: FormGroup = this.formBuilder.group({
    feedbackCtrl: [''],
  });
  resultLoader: boolean = false;
  @ViewChild("feedback")
  feedbackElement!: ElementRef;
  readonly panelOpenState = signal(false);

  constructor(public homeService: HomeService, private snackBar: MatSnackBar, private formBuilder: FormBuilder) { }
  ngOnInit() {
    this.dataSet = this.homeService.getselectedDb();
    this.dataSetName = this.homeService.getselectedDbName();
    this.msg = this.homeService.getChatMsgs().at(this.ind);
    this.showResult = true;

  }
  ngAfterViewInit() {
    this.feedbackElement?.nativeElement.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  getResultforSql() {
    this.resultLoader = true;
    // Subscribe to the response data observable
    this.homeService.runQuery(this.msg?.generate_sql.GeneratedSQL, this.homeService.getselectedDb(), this.msg?.user_question, this.sessionId)
      .subscribe((res: any) => {
        const data = JSON.parse(res.KnownDB);
        if (res && res.ResponseCode === 200) {
          if (data.length === 0) {
            this.emptyMsg = 'No data found';
          } else {
            this.emptyMsg = '';
            for (var obj in data) {
              if (data.hasOwnProperty(obj)) {
                for (var prop in data[obj]) {
                  if (data[obj].hasOwnProperty(prop)) {
                    if (this.displayedColumns.indexOf(prop) === -1) {
                      this.displayedColumns.push(prop);
                    }
                  }
                }
              }
            }
            this.updateLocalMessage(this.ind, res, data);
            this.dataSource = data;
          }
        } else {
          this.updateLocalMessage(this.ind, res, data);
          this.emptyMsg = res?.Error;
        }
        this.resultLoader = false;
      });
  }

  async tabClick(event: any, displayedColumns: any) {
    const tab = event?.tab?.textLabel;
    switch (tab) {
      case "Generated SQL": break;
      case "Result": if (!displayedColumns) { this.getResultforSql() }; break;
      case "Data Sources": break;
    }
  }
  visualizeBtn(msg: any, ind: any) {
    this.showLoader = true;
    let sql = format(msg.generate_sql.GeneratedSQL, { language: 'mysql' })
    this.homeService.generateViz(this.msg.user_question, sql, msg.dataSource, this.sessionId).subscribe((res: any) => {
      const object = res.GeneratedChartjs;
      this.msg = {
        ...this.msg, "visualize": res
      }
      for (const [key, value] of Object.entries(object)) {
        let newvalue: string = (value as string).replace('chart_div', ind + '-chart_div');
        this.onChange(newvalue, ind, key);
      }
    })
  }

  onChange(value: any, ind: any, key: any) {
    this.showChart = true;
    this.showLoader = false;
    this.result = eval(value)
  }

  thumbsUp(sql: any, ind: any) {
    let chats = this.homeService.getChatMsgs();
    const sqlExist = this.suggestionList.some((res: { example_user_question: any; example_generated_sql: any; }) => res.example_user_question === chats[ind]?.user_question && res.example_generated_sql === sql);
    if (!sqlExist) {
      // let concatedUserQuestionsList = chats.map((msg: any) => {
      //   if (msg.author == 'user') {
      //     return msg.user_question
      //   }
      // })
      // const concatenatedStr = concatedUserQuestionsList.filter((word) => word).reduce((accumulator, currentValue) => accumulator + ' , ' + currentValue);
      this.homeService.thumbsUp(sql, chats[ind]?.user_question, this.homeService.getselectedDb(), this.sessionId).subscribe((res: any) => {
        if (res && res.ResponseCode === 201) {
          this.updateLocalMessage(ind, res, "");
          this.showSnackbarCssStyles(res?.Message, 'Close', '10000')
          this.isOpen = true;
        } else {
          this.updateLocalMessage(ind, res, "");
          this.showSnackbarCssStyles(res?.Error, 'Close', '10000')
        }
      })
    } else {
      this.showSnackbarCssStyles('Data is present in the suggestion list', 'Close', '4000')
    }
  }

  updateLocalMessage(ind: any, res: any, data: any) {

    let localChatMsgs = this.msg;
    // Update message in case of result tab
    if (data) {
      localChatMsgs =
      {
        ...localChatMsgs, 'dataSource': data,
        'displayedColumns': this.displayedColumns,
        'dataSet': this.dataSet,
        'run_query': res,
        'ind': ind
      };
    }
    // Update message in case of thumbsup
    else {
      localChatMsgs = {
        ...localChatMsgs,
        "embed_sql": res,
        'ind': ind
      };
    }
    this.msg = localChatMsgs;
    console.log(this.msg)
    //this.homeService.updateChatMsgsAtIndex(localChatMsgs, this.ind);
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

  showContentCopiedMsg() {
    this.showSnackbarCssStyles("Content Copied", 'Close', '4000')
  }

  closeFeedback() {
    this.isOpen = false;
  }

  thumbsDown() {
    this.isOpen = true;
  }

  submitFeedback(ind: any, comment: any) {
    this.isOpen = false;

    this.msg = {
      ...this.msg, "feedback": {
        "option": this.selectedFeedbackOption,
        "comment": comment
      }
    }
  }

  feedbackOption(val: any) {
    if (val == 0) {
      this.selectedFeedbackOption = 'Correct answer';
    } else if (val == 1) {
      this.selectedFeedbackOption = 'Easy to understand'
    } else {
      this.selectedFeedbackOption = 'Quick results'
    }
  }

  ngOnDestroy() {
    this._destroy$.next();
  }
}
