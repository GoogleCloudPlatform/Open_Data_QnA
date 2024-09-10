import 'dart:convert';
import 'dart:math';

import 'package:bloc/bloc.dart';
import 'package:intl/intl.dart';
import 'package:ttmd/utils/TextToDocParameter.dart';
import 'package:ttmd/services/new_suggestions/new_suggestion_state.dart';
import 'dart:html' as html;

class NewSuggestionCubit extends Cubit<NewSuggestionState> {
  NewSuggestionCubit()
      : super(NewSuggestionState(
            status: NewSuggestionStateStatus.initial,
            suggestionList: const ["x:", "x:", "x:"],
            time: "",
            scenarioNumber: 0));

  Future<void> generateNewSuggestions(int scenarioNumber, String question,
      {String? lastCannedQuestion,
      bool? isACannedQuestion,
      String? userGrouping}) async {
    List<String> respLLMQuestion = [];
    List<String> respCannedQuestions = [];
    List<String> resp = [];
    List<String> tmpQuestions = [];
    String body = "";
    Uri url;
    String question1 = "";
    String question2 = "";
    String question3 = "";
    String question4 = "";
    String timeString = "";
    String originalQuestion = "";

    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : START');
    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : userGrouping = $userGrouping');
    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : TextToDocParameter.lastCannedQuestion = ${TextToDocParameter.lastCannedQuestion}');
    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : lastCannedQuestion= ${lastCannedQuestion}');

    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : scenarioNumber = $scenarioNumber');
    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : question = $question');

    timeString = displayDateTime();
    //TextToDocParameter.lastCannedQuestion = question;
    //TextToDocParameter.lastCannedQuestion = lastCannedQuestion?? "";

    isACannedQuestion = isACannedQuestion ?? false;
    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : Not a canned question : isACannedQuestion = $isACannedQuestion');
    originalQuestion = question;

    print(
        'NewSuggestionCubit : NewSuggestionCubit() : generateNewSuggestions : Not a canned question : originalQuestion = $originalQuestion');

    //Create the header
    Map<String, String>? _headers = {
      "Content-Type": "application/json",
      //"Authorization": " Bearer ${client!.credentials.accessToken.toString()}",
    };

    //Create the body
    body = '''{
          "user_grouping": "$userGrouping"
      }''';

    print(
        'NewSuggestionCubit : generateNewSuggestions() : Not a canned question : body = ' +
            body);

    try {
      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/get_known_sql',
          method: "POST",
          sendData: body);

      print(
          'NewSuggestionCubit : generateNewSuggestions() : Not a canned question : response = ' +
              response.toString());

      final jsonData = jsonDecode(response);

      if (jsonData != null) {
        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : jsonData = $jsonData');

        //KnownSQL = [{"example_user_question": "question1", "example_generated_sql": "sql1"},
        // {"example_user_question": "question2", "example_generated_sql": "sql2"},
        // ...]

        var knownSql =
            jsonData["KnownSQL"].replaceAll(RegExp(r'((\\n)|(\\r))'), '');

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSql = $knownSql');

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSql.runtimeType = ${knownSql.runtimeType}');

        if (knownSql is Map)
          print(
              'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSql is a Map');
        if (knownSql is List)
          print(
              'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSql is a List');
        if (knownSql is String)
          print(
              'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSql is a String');

        var knownSqlMap = jsonDecode(knownSql);

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSqlMap.runtimeType = ${knownSqlMap.runtimeType}');

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSqlMap[0].runtimeType = ${knownSqlMap[0].runtimeType}');

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSqlMap = ${knownSqlMap}');

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : knownSqlMap[0] = ${knownSqlMap[0].toString()}');

        for (int i = 0; i < knownSqlMap.length; i++) {
          for (var entry in knownSqlMap[i].entries) {
            print('${entry.key} : ${entry.value}');
            if (entry.key == "example_user_question")
              tmpQuestions.add(entry.value);
          }
        }

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : Before pickUpRandomQuestion() : tmpQuestions = ${tmpQuestions}');

        tmpQuestions = pickUpRandomQuestion(question, tmpQuestions);

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : After pickUpRandomQuestion() : tmpQuestions = ${tmpQuestions}');

        if (tmpQuestions.length > 0)
          question1 = tmpQuestions[0] ?? "No suggestion for question1";
        if (tmpQuestions.length > 1)
          question2 = tmpQuestions[1] ?? "No suggestion for question2";
        if (tmpQuestions.length > 2)
          question3 = tmpQuestions[2] ?? "No suggestion for question3";
        if (tmpQuestions.length > 3)
          question4 = tmpQuestions[3] ?? "No suggestion for question4";

        //Adding scenarioNumber + ":" and ":userGrouping" to have same format as for Business KPI questions
        question1 = "$scenarioNumber:" + question1 + ":" + userGrouping!;
        question2 = "$scenarioNumber:" + question2 + ":" + userGrouping!;
        question3 = "$scenarioNumber:" + question3 + ":" + userGrouping!;
        question4 = "$scenarioNumber:" + question4 + ":" + userGrouping!;

        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : question1 = ${question1}');
        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : question2 = ${question2}');
        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : question3 = ${question3}');
        print(
            'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : question4 = ${question4}');
      }
    } catch (e) {
      print(
          'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : EXCEPTION = $e');
      throw Exception('Failed to get suggestions: $e');
    } finally {
      respLLMQuestion.add(question1);
      respLLMQuestion.add(question2);
      respLLMQuestion.add(question3);
      respLLMQuestion.add(question4);

      print(
          'NewSuggestionCubit: generateNewSuggestions() : Not a canned question :scenarioNumber = $scenarioNumber >= 9 : respLLMQuestion = $respLLMQuestion');

      //2024-07-14 respCannedQuestions = pickUpNextQuestions(scenarioNumber, question);
      print(
          'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : scenarioNumber = $scenarioNumber >= 9 : respCannedQuestions = $respCannedQuestions');

      resp.addAll(respLLMQuestion);

      print(
          'NewSuggestionCubit: generateNewSuggestions() : Not a canned question : scenarioNumber = $scenarioNumber >= 9 : resp = $resp');
    }

    emit(state.copyWith(
        status: NewSuggestionStateStatus.loaded,
        suggestionList: resp,
        time: timeString,
        scenarioNumber: scenarioNumber));
  }

  Future<void> getAllquestions(String userGrouping) async {
    List<String> resp = [];
    String body = "";
    String timeString = "";

    print('NewSuggestionCubit : getAllquestions()  : START');

    timeString = displayDateTime();

    //Create the header
    Map<String, String>? _headers = {
      "Content-Type": "application/json",
      //"Authorization": " Bearer ${client!.credentials.accessToken.toString()}",
    };

    //Create the body
    body = '''{
          "user_grouping": "$userGrouping"
      }''';

    print('NewSuggestionCubit : getAllquestions() : body = ' + body);

    try {
      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/get_known_sql',
          method: "POST",
          sendData: body);

      print('NewSuggestionCubit : getAllquestions() : response = ' +
          response.toString());

      final jsonData = jsonDecode(response);

      if (jsonData != null) {
        print('NewSuggestionCubit: getAllquestions() : jsonData = $jsonData');

        //KnownSQL = [{"example_user_question": "question1", "example_generated_sql": "sql1"},
        // {"example_user_question": "question2", "example_generated_sql": "sql2"},
        // ...]

        var knownSql =
            jsonData["KnownSQL"].replaceAll(RegExp(r'((\\n)|(\\r))'), '');

        print('NewSuggestionCubit: getAllquestions() : knownSql = $knownSql');

        var knownSqlMap = jsonDecode(knownSql);

        for (int i = 0; i < knownSqlMap.length; i++) {
          for (var entry in knownSqlMap[i].entries) {
            print('${entry.key} : ${entry.value}');
            if (entry.key == "example_user_question") resp.add(entry.value);
          }
        }
      }
    } catch (e) {
      print('NewSuggestionCubit: getAllquestions() : EXCEPTION = $e');
      throw Exception('Failed to get questions: $e');
    } finally {
      print('NewSuggestionCubit: getAllquestions() : resp = ${resp}');
    }

    emit(state.copyWith(
        status: NewSuggestionStateStatus.all_questions_loaded,
        suggestionList: resp,
        time: timeString,
        scenarioNumber: 0,
        userGrouping: userGrouping));
  }

  String displayDateTime() {
    String? dateTimeS;

    final now = DateTime.now();
    dateTimeS = DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
    return dateTimeS!;
  }

  List<String> pickUpNextQuestions(int scenarioNumber, String question) {
    List<String> list = [];
    return list;
  }

  int getIndexOfQuestion(
      int scenarioNumber, String question, List<String> listQuestionsScenario) {
    print('NewSuggestionCubit: getIndexOfQuestion() : START');
    print(
        'NewSuggestionCubit: getIndexOfQuestion() : question = $scenarioNumber:$question');
    for (String q in listQuestionsScenario) print('q = $q');

    int index = 0;
    index = listQuestionsScenario.indexOf("$scenarioNumber:$question");

    print('NewSuggestionCubit: getIndexOfQuestion() : index = $index');

    return index;
  }

  List<String> pickUpRandomQuestion(
      String question, List<String> questionList) {
    List<String> list = [];
    int lengthScenario = 0;
    Random random = new Random();
    List<String> listQuestionsScenario = [];
    int randomNumber = 0;
    String candidateQuestion = "";
    Map<String, String> map = {};

    print('NewSuggestionCubit: pickUpRandomQuestion() : START');
    print('NewSuggestionCubit: pickUpRandomQuestion() : question = $question');

    for (int i = 0; list.length <= 3; i++) {
      randomNumber = random.nextInt(questionList.length);
      candidateQuestion = questionList[randomNumber];
      print(
          'NewSuggestionCubit: pickUpRandomQuestion() : candidateQuestion = $candidateQuestion');
      if (question != candidateQuestion) {
        print(
            'NewSuggestionCubit: pickUpRandomQuestion() : if(question != candidateQuestion) : candidateQuestion = $candidateQuestion');
        if (!map.containsKey(candidateQuestion)) {
          print(
              'NewSuggestionCubit: pickUpRandomQuestion() : !map.containsKey(candidateQuestion : adding candidateQuestion');
          map[candidateQuestion] = candidateQuestion;
          list.add(candidateQuestion);
        }
      }
      //listQuestionsScenario may contain less than 3 questions (including the asked question
      //so we check that and break the loop if we retreived all the candidate questions
      if (list.length == questionList.length - 1) {
        break;
      }
    }

    print('NewSuggestionCubit: pickUpRandomQuestion() : list = $list');

    return list;
  }
}
