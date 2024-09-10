import 'package:bloc/bloc.dart';
import 'package:ttmd/services/text_to_doc_question/text_to_doc_question_state.dart';


class TextToDocQuestionCubit extends Cubit<TextToDocQuestionState> {

  TextToDocQuestionCubit()
      : super(TextToDocQuestionState(
      status: textToDocStatus.not_text_to_doc , message: ""));

  Future<void> switchToTextToDoc({required bool isTextToDoc, String? message = ""}) async {
    print(
        'TextToDocQuestionCubit : switchToTextToDoc() : DEBUT ');
    print(
        'TextToDocQuestionCubit : switchToTextToDoc() : isTextToDoc = $isTextToDoc ');

    if(isTextToDoc) {
      emit(state.copyWith(
          status: textToDocStatus.text_to_doc, message: message));
    } else {
      emit(state.copyWith(
          status: textToDocStatus.not_text_to_doc, message: message));
    }
  }
}
