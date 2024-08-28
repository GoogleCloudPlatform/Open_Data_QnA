import { Injectable } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { BehaviorSubject } from 'rxjs/internal/BehaviorSubject';
import { HomeService } from './home.service';

export interface Message {
  author: string
  message?: any
  user_question: string
  generate_sql?: any
  run_query?: any
  visualize?: any
  dataSource?: any,
  displayedColumns?: any
  dataSet?: any
  ind?: any
  embed_sql?: any
}
interface ChatSession {
  chatMsgs: Message[]
}

@Injectable({
  providedIn: 'root'
})

export class ChatService {
  private chatSess: ChatSession = {
    chatMsgs: []
  }
  public currentActiveSession = new BehaviorSubject<ChatSession>(this.chatSess);
  chatSessionObservable = this.currentActiveSession.asObservable();
  public agentResponseLoader = new BehaviorSubject<boolean>(false);
  agentResponseLoader$ = this.agentResponseLoader.asObservable();
  private _destroy$ = new Subject<void>();
  private currentSessionId: string = '';
  private suggestionList: [] = [];
  selectedGrouping!: string;

  constructor(public homeService: HomeService) {
    this.homeService.currentSelectedGroupingObservable.pipe(takeUntil(this._destroy$)).subscribe((res) => {
      this.selectedGrouping = res
    })
    this.homeService.knownSqlObservable?.pipe(takeUntil(this._destroy$)).subscribe((response: any) => {
      if (response && response != null) {
        this.suggestionList = JSON.parse(response);
        this.createNewSession()
      }
    })
  }

  createNewSession() {
    const newSession: ChatSession = {
      chatMsgs: [{
        'author': 'agent',
        'message': this.suggestionList,
        'user_question': 'Looking for a specific insight or want to browse through your database? Ask what you are looking for in a natural language and Open Data QnA will translate to SQL and bring back results in natural language.'
      }]
    }
    this.currentSessionId = '';
    this.currentActiveSession.next(newSession);
  }

  addToSessionThread(message: Message) {
    const desiredSession = this.currentActiveSession.value;
    if (desiredSession) {
      desiredSession.chatMsgs.push(message);
      if (message.author == 'agent') {
       this.agentResponseLoader.next(false)
      }
      this.currentActiveSession.next(desiredSession);
    }
  }

  addQuestion(question: string, userId: string, agentCase: string, selectedHistory?: any) {
    let newChatMsg: Message = {
      author: 'user',
      message: [],
      user_question: question
    }
    if (agentCase != 'history') {
      this.addToSessionThread(newChatMsg);
    }
    // do API call for agent response.
    switch (agentCase) {
      case 'followup':
        this.generate_sql(question, userId);
        break;
      case 'history':
        this.generate_history_thread(selectedHistory)
        break;
      case 'scenario':
        this.generate_sql(question, userId)
        break;
    }
  }

  generate_sql(question: string, userId: string) {
    this.currentSessionId = this.homeService.getSessionId()
    this.agentResponseLoader.next(true)
    this.homeService.generateSql(question, this.homeService.getSelectedDbGrouping(), this.currentSessionId, userId).subscribe((response: any) => {
      if (response !== undefined) {
        this.homeService.setSessionId(response.SessionID)
        this.currentSessionId = response.SessionID;
        const newChatMsg: Message = {
          'author': 'agent',
          'user_question': question,
          'generate_sql': response,
        }
        this.addToSessionThread(newChatMsg);
      }
    })
  }

  generate_history_thread(selectedHistory: any) {
    for (let i = selectedHistory?.length - 1; i >= 0; i--) {
      const newUserMsg: Message = {
        author: 'user',
        user_question: selectedHistory[i]?.user_question
      }
      this.addToSessionThread(newUserMsg);
      const newAgentMsg: Message = {
        'author': 'agent',
        'user_question': selectedHistory[i]?.user_question,
        'generate_sql': {
          'GeneratedSQL': selectedHistory[i]?.bot_response,
          'SessionID': selectedHistory[i]?.session_id,
          "ResponseCode": 200
        }
      }
      this.homeService.setSessionId(selectedHistory[i]?.session_id)
      this.addToSessionThread(newAgentMsg);
    }
  }
}
