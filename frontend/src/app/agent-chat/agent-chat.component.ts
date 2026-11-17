import { AfterViewInit, ChangeDetectorRef, Component, ElementRef, Input, ViewChild, signal } from '@angular/core';
import { HomeService } from '../shared/services/home.service';
import { format } from 'sql-formatter';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { ChatService } from '../shared/services/chat.service';

declare const google: any;

const ALLOWED_CHART_PACKAGES: Readonly<Record<string, string>> = {
  BarChart: 'corechart',
  ColumnChart: 'corechart',
  LineChart: 'corechart',
  AreaChart: 'corechart',
  PieChart: 'corechart',
  ScatterChart: 'corechart',
  BubbleChart: 'corechart',
  Histogram: 'corechart',
  ComboChart: 'corechart',
  SteppedAreaChart: 'corechart',
  Table: 'table',
  GeoChart: 'geochart',
};

const ALLOWED_CHART_KEYS = new Set<string>(['chart_div', 'chart_div_1']);

@Component({
  selector: 'app-agent-chat',
  templateUrl: './agent-chat.component.html',
  styleUrl: './agent-chat.component.scss'
})
export class AgentChatComponent implements AfterViewInit {
  msg: any;
  @Input('example_user_question') example_user_question: any;
  @Input('ind') ind: any;
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

  constructor(public homeService: HomeService, private snackBar: MatSnackBar, private formBuilder: FormBuilder, public chatService: ChatService, private cdref: ChangeDetectorRef) { }
  ngOnInit() {
    // added this comment for test PR from frontend_dev
    this.homeService.knownSqlObservable?.pipe(takeUntil(this._destroy$)).subscribe((response: any) => {
      if (response && response != null) {
        this.suggestionList = JSON.parse(response);
      }
    })
    this.dataSet = this.homeService.getSelectedDbGrouping();
    this.dataSetName = this.homeService.getselectedDbName();
    this.chatService.chatSessionObservable.pipe(takeUntil(this._destroy$)).subscribe((res) => {
      this.homeService.updateChatMsgs(res.chatMsgs)
      // this.msg = res.chatMsgs.at(this.ind)
    })
    //  this.msg = this.homeService.getChatMsgs().at(this.ind);
    this.showResult = true;

  }
  ngAfterContentChecked() {
    this.cdref.detectChanges();
  }

  ngAfterViewInit() {
    this.msg = this.homeService.getChatMsgs().at(this.ind);
    this.feedbackElement?.nativeElement.scrollIntoView({ behavior: "smooth", block: "start" });
    this.cdref.detectChanges();
  }
  getResultforSql() {
    this.resultLoader = true;
    // Subscribe to the response data observable
    this.homeService.runQuery(this.msg?.generate_sql.GeneratedSQL, this.homeService.getSelectedDbGrouping(), this.msg?.user_question, this.homeService.getSessionId())
      .pipe(takeUntil(this._destroy$)).subscribe((res: any) => {
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
            // console.log(this.ind)
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
    this.homeService.generateViz(this.msg.user_question, sql, msg.dataSource, this.homeService.getSessionId()).subscribe({
      next: (res: any) => {
        const chartSpecs = res?.GeneratedChartjs;
        this.msg = {
          ...this.msg, "visualize": res
        };
        if (chartSpecs && typeof chartSpecs === 'object' && !Array.isArray(chartSpecs)) {
          for (const [key, spec] of Object.entries(chartSpecs)) {
            if (ALLOWED_CHART_KEYS.has(key)) {
              this.onChange(spec, ind, key);
            }
          }
        } else {
          this.showLoader = false;
        }
      },
      error: () => {
        this.showLoader = false;
      }
    });
  }

  private isSafeCellValue(cell: unknown): boolean {
    if (cell === null || typeof cell === 'string' || typeof cell === 'boolean') {
      return true;
    }
    if (typeof cell === 'number') {
      return Number.isFinite(cell);
    }
    return false;
  }

  private buildSafeChartOptions(rawOptions: any): Record<string, any> {
    const safeOptions: Record<string, any> = {
      width: 600,
      height: 300,
      allowHtml: false,
    };
    if (!rawOptions || typeof rawOptions !== 'object' || Array.isArray(rawOptions)) {
      return safeOptions;
    }
    if (typeof rawOptions.title === 'string') {
      safeOptions['title'] = rawOptions.title.slice(0, 300);
    }
    if (typeof rawOptions.width === 'number' && Number.isFinite(rawOptions.width) && rawOptions.width >= 100 && rawOptions.width <= 4000) {
      safeOptions['width'] = Math.trunc(rawOptions.width);
    }
    if (typeof rawOptions.height === 'number' && Number.isFinite(rawOptions.height) && rawOptions.height >= 100 && rawOptions.height <= 4000) {
      safeOptions['height'] = Math.trunc(rawOptions.height);
    }
    if (typeof rawOptions.isStacked === 'boolean') {
      safeOptions['isStacked'] = rawOptions.isStacked;
    }
    if (typeof rawOptions.pieHole === 'number' && Number.isFinite(rawOptions.pieHole) && rawOptions.pieHole >= 0 && rawOptions.pieHole <= 1) {
      safeOptions['pieHole'] = rawOptions.pieHole;
    }
    for (const axisKey of ['hAxis', 'vAxis', 'legend']) {
      const axisVal = rawOptions[axisKey];
      if (axisVal && typeof axisVal === 'object' && !Array.isArray(axisVal)) {
        const safeAxis: Record<string, any> = {};
        if ((axisKey === 'hAxis' || axisKey === 'vAxis') && typeof axisVal.title === 'string') {
          safeAxis['title'] = axisVal.title.slice(0, 200);
        }
        const fontSize = axisVal?.textStyle?.fontSize;
        if (typeof fontSize === 'number' && Number.isFinite(fontSize) && fontSize >= 4 && fontSize <= 48) {
          safeAxis['textStyle'] = { fontSize: Math.trunc(fontSize) };
        }
        if (Object.keys(safeAxis).length > 0) {
          safeOptions[axisKey] = safeAxis;
        }
      }
    }
    if (rawOptions.bar && typeof rawOptions.bar.groupWidth === 'string' && /^\d{1,3}%$/.test(rawOptions.bar.groupWidth.trim())) {
      safeOptions['bar'] = { groupWidth: rawOptions.bar.groupWidth.trim() };
    }
    safeOptions['allowHtml'] = false;
    return safeOptions;
  }

  onChange(spec: any, ind: any, key: string) {
    this.showLoader = false;
    if (!ALLOWED_CHART_KEYS.has(key)) {
      return;
    }
    if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
      return;
    }
    const chartType = spec.chartType;
    if (typeof chartType !== 'string' || !Object.prototype.hasOwnProperty.call(ALLOWED_CHART_PACKAGES, chartType)) {
      return;
    }
    if (!Array.isArray(spec.columns) || spec.columns.length === 0 || !spec.columns.every((c: unknown) => typeof c === 'string' && c.trim().length > 0)) {
      return;
    }
    if (!Array.isArray(spec.rows)) {
      return;
    }
    const colCount = spec.columns.length;
    for (const row of spec.rows) {
      if (!Array.isArray(row) || row.length !== colCount || !row.every((cell: unknown) => this.isSafeCellValue(cell))) {
        return;
      }
    }
    if (typeof google === 'undefined' || !google?.charts) {
      return;
    }

    this.showChart = true;
    const containerId = `${ind}-${key}`;
    const pkg = ALLOWED_CHART_PACKAGES[chartType];
    const safeOptions = this.buildSafeChartOptions(spec.options);
    const tableArray = [spec.columns, ...spec.rows];

    google.charts.load('current', { packages: [pkg] });
    google.charts.setOnLoadCallback(() => {
      const container = document.getElementById(containerId);
      if (!container || !google?.visualization) {
        return;
      }
      const ChartCtor = google.visualization[chartType];
      if (typeof ChartCtor !== 'function') {
        return;
      }
      const dataTable = google.visualization.arrayToDataTable(tableArray);
      const chart = new ChartCtor(container);
      chart.draw(dataTable, safeOptions);
      this.result = true;
    });
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
      this.homeService.thumbsUp(sql, chats[ind]?.user_question, this.homeService.getSelectedDbGrouping(), this.homeService.getSessionId()).subscribe((res: any) => {
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
