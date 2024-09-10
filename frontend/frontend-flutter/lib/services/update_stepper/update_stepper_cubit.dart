import 'package:bloc/bloc.dart';
import 'package:ttmd/services/update_stepper/update_stepper_state.dart';
import 'package:flutter/material.dart';
import 'dart:html' as html;
import 'dart:convert';

import 'package:ttmd/utils/stepper_expert_info.dart';

class UpdateStepperCubit extends Cubit<UpdateStepperState> {
  //List<String>? dicRows;
  //String? message;
  //StepState? stateStepper;
  //bool? isActiveStepper;

  UpdateStepperCubit()
      : super(UpdateStepperState(
            status: StepperStatus.initial,
            message: "Initial state",
            stateStepper: StepState.disabled,
            isActiveStepper: false,
            debugInfo: StepperExpertInfo()));

  Future<void> updateStepperStatusUploaded(
      {required StepperStatus status,
      required String message,
      required StepState stateStepper,
      required bool isActiveStepper,
      StepperExpertInfo? debugInfo}) async {
    print('UpdateStepperCubit : updateStepperStatusUploaded() : DEBUT ');
    print('UpdateStepperCubit : updateStepperStatusUploaded() : status = $status');
    print('UpdateStepperCubit : updateStepperStatusUploaded() : message = $message');
    print(
        'UpdateStepperCubit : updateStepperStatusUploaded() : stateStepper = $stateStepper');
    print(
        'UpdateStepperCubit : updateStepperStatusUploaded() : isActiveStepper = $isActiveStepper');
    print(
        'UpdateStepperCubit : updateStepperStatusUploaded() : debugInfo = $debugInfo');

    try {
      emit(state.copyWith(
          status: status,
          message: message,
          stateStepper: stateStepper,
          isActiveStepper: isActiveStepper,
        debugInfo: debugInfo
      ));
    } catch (e) {
      print(
          'UpdateStepperCubit : updateStepperStatusUploaded() : EXCEPTION : ' +
              e.toString());
      emit(state.copyWith(
          status: StepperStatus.error,
          message: "Une erreur s'est produite.",
          stateStepper: StepState.error,
          isActiveStepper: false,
          debugInfo: StepperExpertInfo()
      ));
    }
  }
}
