import { Component, EventEmitter, Input, Output, SimpleChanges } from '@angular/core';
import { NestedTreeControl, TreeControl } from '@angular/cdk/tree';
import { MatTreeNestedDataSource } from '@angular/material/tree';
import { HomeService } from '../shared/services/home.service';
import { ChatService } from '../shared/services/chat.service';
import { LoginService } from '../shared/services/login.service';

/**
 * Scenario data with nested structure.
 * Each node has a name and an optional list of children.
 */
interface Question {
  name: string;
  child?: Question[];
}

interface ScenarioNode {
  dataSource: MatTreeNestedDataSource<Question>;
  questions: Question[];
  name: string;
  userGrouping: string
}

@Component({
  selector: 'app-scenario-list',
  templateUrl: './scenario-list.component.html',
  styleUrl: './scenario-list.component.scss'
})
export class ScenarioListComponent {
  @Input('csvData') csvData: any
  scenarioData: ScenarioNode[] = [];
  treeControl = new NestedTreeControl<Question>(node => node.child);
  hasChild = (_: number, node: Question) => !!node.child && node.child.length > 0;
  selectedGrouping: string = '';
  selectedScenario: string = '';
  userId: any;
  constructor(public homeService: HomeService, public chatService: ChatService, public loginService: LoginService) {
    this.loginService.getUserDetails().subscribe((res: any) => {
      this.userId = res.uid;
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    for (const propName in changes) {
      if (changes.hasOwnProperty(propName)) {
        switch (propName) {
          case 'csvData': {
            if (this.csvData) {
              this.formatCsvData()
            }
          }
        }
      }
    }
  }
  ngOnInit() {
    this.formatCsvData();
  }

  formatCsvData() {
    this.scenarioData = [];
    let result: any = [];
    this.csvData.forEach((current: any) => {
      let desiredObj: any = result?.find((ele: any) => {
        if (ele.user_grouping == current.user_grouping &&
          ele.scenario == current.scenario) {
          return ele
        }
      });

      if (desiredObj === undefined) {
        result.push(
          {
            user_grouping: current.user_grouping,
            scenario: current.scenario,
            question: [current.question]
          });
      }
      else {
        desiredObj.question.push(current.question);
      }
    });
    result?.map((ele: any) => {
      if (ele.user_grouping) {
        var nestedQues: any = this.constructNestedTree(ele.question);
        let dataSource = new MatTreeNestedDataSource<Question>();
        dataSource.data = [nestedQues];
        this.scenarioData.push({
          dataSource: dataSource,
          questions: [nestedQues],
          name: ele.scenario,
          userGrouping: ele.user_grouping
        })
      }
    })
    this.treeControl = new NestedTreeControl<Question>(node => node.child)
  }

  onClickScenario(question: any, scenario: any) {
    this.homeService.setSelectedDbGrouping(scenario.userGrouping);
    this.selectedGrouping = this.homeService.getSelectedDbGrouping();
    this.homeService.currentSelectedGrouping.next(scenario.userGrouping)
    if (this.selectedScenario == scenario.name) {
      this.chatService.addQuestion(question.name, this.userId, 'scenario')
      this.chatService.agentResponseLoader.next(true)
      //this.chatService.setAgentResponseLoader(true)
    }
    else {
      this.chatService.createNewSession()
      this.chatService.addQuestion(question.name, this.userId, 'scenario')
      this.chatService.agentResponseLoader.next(true)
    }
    this.homeService.currentSelectedGroupingObservable.subscribe((res) => {
      this.selectedGrouping = res
    })
    this.selectedScenario = scenario.name
  }

  resetSelectedScenario() {
    this.selectedScenario = '';
  }
  constructNestedTree(questions: any[]) {
    if (questions.length == 1) {
      var ques: Question = {
        name: questions[0]
      }
    }
    else {
      var ques: Question = {
        name: questions[0],
        child: [this.constructNestedTree(questions.slice(1))]
      }
    }
    return ques;
  }
}
