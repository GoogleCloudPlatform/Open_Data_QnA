import 'package:equatable/equatable.dart';

import '../../utils/most_popular_questions.dart';


enum UpdateMostPopularQuestionStatus {initial,loaded}

class UpdatePopularQuestionsState extends Equatable {
  final UpdateMostPopularQuestionStatus status;
  final List<MostPopularQ>? mostPopularQuestionsList;
  final String? time;

  UpdatePopularQuestionsState({
    this.status = UpdateMostPopularQuestionStatus.initial,
    this.mostPopularQuestionsList,
    this.time = ""
  });

  @override
  List<Object> get props => [this.status,this.mostPopularQuestionsList!, this.time!];

  UpdatePopularQuestionsState copyWith({
    UpdateMostPopularQuestionStatus? status,
    List<MostPopularQ>? mostPopularQuestionsList,
    String? time
  })  {
    print('UpdatePopularQuestionsState : copyWith() : List<MostPopularQ>? mostPopularQuestionsList = ' + mostPopularQuestionsList!.toString());
    return UpdatePopularQuestionsState(
      status: status ?? this.status,
      mostPopularQuestionsList: mostPopularQuestionsList ?? this.mostPopularQuestionsList,
      time: time ?? this.time
    );
  }
}
