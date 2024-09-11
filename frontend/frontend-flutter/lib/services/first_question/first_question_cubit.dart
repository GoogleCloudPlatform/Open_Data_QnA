import 'package:bloc/bloc.dart';
import 'package:ttmd/services/first_question/first_question_state.dart';


class FirstQuestionCubit extends Cubit<FirstQuestionState> {

  FirstQuestionCubit()
      : super(FirstQuestionState(
      status: firstQuestionStatus.display_welcome_message , message: ""));

  Future<void> removeWelcomeMessage({String? message = ""}) async {
    print(
        'FirstQuestionCubit : removeWelcomeMessage() : DEBUT ');

    emit(state.copyWith(
        status: firstQuestionStatus.remove_welcome_message , message: message));
  }
}
