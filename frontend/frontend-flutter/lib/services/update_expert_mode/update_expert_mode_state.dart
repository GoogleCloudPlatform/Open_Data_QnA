import 'package:equatable/equatable.dart';


enum updateExpertModeStatus {expert_mode_on,expert_mode_off}

class UpdateExpertModeState extends Equatable {
  final updateExpertModeStatus status;

  UpdateExpertModeState({
    this.status = updateExpertModeStatus.expert_mode_off,
  });

  @override
  List<Object> get props => [this.status];

  UpdateExpertModeState copyWith({
    updateExpertModeStatus? status,
  })  {
    print('UpdateExpertModeState : copyWith() : status = ' + status.toString());
    return UpdateExpertModeState(
      status: status ?? this.status,
    );
  }
}