import 'package:equatable/equatable.dart';

enum textToDocStatus {not_text_to_doc,text_to_doc}

class TextToDocQuestionState extends Equatable {
   textToDocStatus status;
   String? message;

  TextToDocQuestionState({
    this.status = textToDocStatus.not_text_to_doc,
    this.message = "",
  });

  @override
  List<Object> get props => [this.status,this.message!];

  TextToDocQuestionState copyWith({
    textToDocStatus? status,
    String? message
  })  {
    print('TextToDocQuestionState : copyWith() : status = $status :  message = $message');
    this.status = status!;
    this.message = message;
    return TextToDocQuestionState(
      status: status ?? this.status,
      message: message ?? this.message,
    );
  }
}

