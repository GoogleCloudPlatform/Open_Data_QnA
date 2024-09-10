import 'package:equatable/equatable.dart';


enum NewSuggestionStateStatus {initial,loading,loaded, all_questions_loaded}

class NewSuggestionState extends Equatable {
  final NewSuggestionStateStatus status;
  final List<String>? suggestionList;
  final String? time;
  final int? scenarioNumber;
  final String? userGrouping;

  NewSuggestionState({
    this.status = NewSuggestionStateStatus.initial,
    this.suggestionList = const ["x:","x:", "x:"],
    this.time = "",
    this.scenarioNumber = 0,
    this.userGrouping = ""
  });

  @override
  List<Object> get props => [this.status,this.suggestionList!, this.time!, this.scenarioNumber!, this.userGrouping!];

  NewSuggestionState copyWith({
    NewSuggestionStateStatus? status,
    List<String>? suggestionList,
    String? time,
    int? scenarioNumber,
    String? userGrouping
  })  {
    print('NewSuggestionState : copyWith() : suggestion = $suggestionList');
    return NewSuggestionState(
        status: status ?? this.status,
        suggestionList: suggestionList ?? this.suggestionList,
        time: time ?? this.time,
        scenarioNumber: scenarioNumber ?? this.scenarioNumber,
        userGrouping: userGrouping ?? this.userGrouping
    );
  }
}
