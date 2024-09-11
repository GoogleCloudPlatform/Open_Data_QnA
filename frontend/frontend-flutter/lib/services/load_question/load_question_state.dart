import 'package:equatable/equatable.dart';

enum LoadQuestionStatus {initial,loaded, error}

class LoadQuestionState extends Equatable {
  final LoadQuestionStatus status;
  final String? question;
  final String? time;

  LoadQuestionState({
    this.status = LoadQuestionStatus.initial,
    this.question = "",
    this.time = ""
  });

  @override
  List<Object> get props => [this.status,this.question!, this.time!];

  LoadQuestionState copyWith({
    LoadQuestionStatus? status,
    String? question,
    String? time
  })  {
    print('LoadQuestionState : copyWith() : question = $question! : time = $time');
    return LoadQuestionState(
      status: status ?? this.status,
      question: question ?? this.question,
      time: time ?? this.time
    );
  }
}
