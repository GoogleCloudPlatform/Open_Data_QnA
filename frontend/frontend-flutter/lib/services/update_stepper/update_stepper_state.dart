import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

import '../../utils/stepper_expert_info.dart';

enum StepperStatus {
  initial,
  uploaded,
  extracted,
  compared,
  committed,
  error,
  enter_question,
  generate_sql,
  run_query,
  get_graph_description,
  get_text_summary
}

class UpdateStepperState extends Equatable {
  final StepperStatus status;
  String? message;
  StepState? stateStepper;
  bool? isActiveStepper;
  final StepperExpertInfo debugInfo;

  UpdateStepperState(
      {this.status = StepperStatus.initial,
      this.message = "",
      this.stateStepper = StepState.disabled,
      this.isActiveStepper = false,
      this.debugInfo = const StepperExpertInfo()});

  @override
  List<Object> get props => [
        this.status,
        this.message!,
        this.stateStepper!,
        this.isActiveStepper!,
        this.debugInfo!
      ];

  UpdateStepperState copyWith(
      {StepperStatus? status,
      String? message,
      StepState? stateStepper,
      bool? isActiveStepper,
      StepperExpertInfo? debugInfo}) {
    print(
        'UpdateStepperState : copyWith() : status = $status : message = $message : stateStepper = $stateStepper : isActiveStepper = $isActiveStepper : debugInfo = $debugInfo');

    return UpdateStepperState(
        status: status ?? this.status,
        message: message ?? this.message,
        stateStepper: stateStepper ?? this.stateStepper,
        isActiveStepper: isActiveStepper ?? this.isActiveStepper,
        debugInfo: debugInfo ?? this.debugInfo);
  }
}
