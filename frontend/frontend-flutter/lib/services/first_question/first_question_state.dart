import 'package:equatable/equatable.dart';


enum firstQuestionStatus {display_welcome_message,remove_welcome_message}

class FirstQuestionState extends Equatable {
  final firstQuestionStatus status;
  final String? message;

  FirstQuestionState({
    this.status = firstQuestionStatus.display_welcome_message,
    this.message = "",
  });

  @override
  List<Object> get props => [this.status,this.message!];

  FirstQuestionState copyWith({
    firstQuestionStatus? status,
    String? message
  })  {
    print('FirstQuestionState : copyWith() : message = ' + message!);
    return FirstQuestionState(
      status: status ?? this.status,
      message: message ?? this.message,
    );
  }
}

