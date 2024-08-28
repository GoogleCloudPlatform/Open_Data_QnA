import { Injectable, inject } from '@angular/core';
import { HttpHeaders, HttpClient, HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError, BehaviorSubject } from 'rxjs';
import { ENDPOINT_OPENDATAQNA } from '../../../assets/constants';
import { Firestore, collection, collectionData, doc, docData, orderBy, query, updateDoc, where } from '@angular/fire/firestore';

@Injectable({
  providedIn: 'root'
})
export class HomeService {
  public knownSqlFromDb = new BehaviorSubject(null);
  knownSqlObservable = this.knownSqlFromDb.asObservable();

  public currentSelectedGrouping = new BehaviorSubject('');
  currentSelectedGroupingObservable = this.currentSelectedGrouping.asObservable();
  private databaseList: any;
  private selectedGrouping: any;
  public selectedDBType: any;
  selectedDbName: any;
  chatMsgs: any[] = [];
  selectedHistory: any
  private firestore: Firestore = inject(Firestore);
  session_id: any = '';
  constructor(public http: HttpClient) { }

  ngOnInit() { }

  getUserSessions(userId: string) {
    const sessionCollection = collection(this.firestore, `session_logs`);
    const orderedCollection = query(sessionCollection, orderBy("timestamp", "desc"));
    const filter = query(orderedCollection, where("user_id", "==", userId))
    return collectionData(filter, { idField: 'id' })
  }

  getAvailableDatabases(): any {
    const header = {
      'Content-Type': 'application/json',
    }
    const requestOptions = {
      headers: new HttpHeaders(header),
    };

    return this.http.get(ENDPOINT_OPENDATAQNA + '/available_databases', requestOptions).pipe(catchError(this.handleError))
  }

  sqlSuggestionList(grouping: any, dbtype: any) {

    const header = {
      'Content-Type': 'application/json',
    }
    const requestOptions = {
      headers: new HttpHeaders(header),
    };

    const body =
    {
      "user_grouping": grouping
    }
    this.selectedDBType = dbtype;

    return this.http.post(ENDPOINT_OPENDATAQNA + '/get_known_sql', body, requestOptions)
      .pipe(catchError(this.handleError));

  }
  
  generateSql(userQuestion: any, grouping: any, session_id: any, user_id: any) {

    const header = {
      'Content-Type': 'application/json',
    }
    const requestOptions = {
      headers: new HttpHeaders(header),
    };
    const body =
    {
      "user_question": userQuestion,
      "user_grouping": grouping,
      "session_id": session_id,
      "user_id": user_id
    }
    let endpoint = ENDPOINT_OPENDATAQNA;

    return this.http.post(endpoint + "/generate_sql", body, requestOptions)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: HttpErrorResponse) {
    if (error.error instanceof ErrorEvent) {
      console.error('An error occurred:', error.error);
    } else {
    }
    return throwError(
      'Something bad happened; please try again later.');
  }
  
  setAvailableDBList(databaseList: string) {
    this.databaseList = databaseList;
  }
  getAvailableDBList(): string {
    return this.databaseList;
  }
  setSelectedDbGrouping(selectedDBGroup: any) {
    this.selectedGrouping = selectedDBGroup;
  }
  getSelectedDbGrouping(): string {
    return this.selectedGrouping;
  }

  setselectedDbName(databaseList: any) {
    this.selectedDbName = databaseList;
  }
  getselectedDbName(): string {
    return this.selectedDbName;
  }

  setSessionId(session_id: any) {
    this.session_id = session_id;
  }
  getSessionId(): string {
    return this.session_id;
  }

  getChatMsgs(): any[] {
    return this.chatMsgs
  }

  updateChatMsgs(chatMsgs: any) {
    this.chatMsgs = chatMsgs;
  }

  getSelectedHistory() {
    return this.selectedHistory
  }

  updateSelectedHistory(selectedHistory: any) {
    this.selectedHistory = selectedHistory
  }

  updateChatMsgsAtIndex(chatMsg: any, ind: any) {
    this.chatMsgs[ind] = chatMsg
  }

  runQuery(query: any, grouping: any, user_question: any, session_id: any) {
    const header = {
      'Content-Type': 'application/json',
    }
    const requestOptions = {
      headers: new HttpHeaders(header),
    };
    const body =
    {
      "generated_sql": query,
      "user_grouping": grouping,
      "user_question": user_question,
      "session_id": this.session_id
    }
    let endpoint = ENDPOINT_OPENDATAQNA;

    return this.http.post(endpoint + "/run_query", body, requestOptions);
  }

  thumbsUp(sql: any, user_question: any, selectedGrouping: any, session_id: any) {

    const header = {
      'Content-Type': 'application/json',
    }
    const requestOptions = {
      headers: new HttpHeaders(header),
    };
    const body =
    {
      user_grouping: selectedGrouping,
      generated_sql: sql,
      user_question: user_question,
      session_id: this.session_id
    }
    let endpoint = ENDPOINT_OPENDATAQNA;
    return this.http.post(endpoint + "/embed_sql", body, requestOptions)
      .pipe(catchError(this.handleError));
  }

  generateViz(question: any, query: any, result: any, session_id: any) {
    const header = {
      'Content-Type': 'application/json',
    }
    const requestOptions = {
      headers: new HttpHeaders(header),
    };
    const body =
    {
      "user_question": question,
      "sql_generated": query,
      "sql_results": result,
      "session_id": this.session_id
    }
    return this.http.post(ENDPOINT_OPENDATAQNA + "/generate_viz", body, requestOptions)
      .pipe(catchError(this.handleError));
  }
}
