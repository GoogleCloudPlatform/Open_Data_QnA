import 'package:bloc/bloc.dart';
import 'package:ttmd/services/update_popular_questions/update_popular_questions_state.dart';

import '../../utils/most_popular_questions.dart';

class UpdatePopularQuestionsCubit extends Cubit<UpdatePopularQuestionsState> {
  UpdatePopularQuestionsCubit()
      : super(UpdatePopularQuestionsState(
            status: UpdateMostPopularQuestionStatus.initial,
            mostPopularQuestionsList: [
              MostPopularQ("", 0, ""),
              MostPopularQ("", 0, ""),
              MostPopularQ("", 0, "")
            ],
            time: ""));

  Future<void> updateMostPopularQuestions(
      {List<MostPopularQ>? mostPopularQuestionsList, String? time}) async {
    print(
        'UpdatePopularQuestionsCubit : UpdatePopularQuestionsCubit() : DEBUT ');

    emit(state.copyWith(
        status: UpdateMostPopularQuestionStatus.loaded,
        mostPopularQuestionsList: mostPopularQuestionsList,
        time: time));
  }
}
