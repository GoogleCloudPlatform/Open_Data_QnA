import 'package:bloc/bloc.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:ttmd/services/display_stepper/display_stepper_state.dart';

import '../../utils/TextToDocParameter.dart';


class DisplayStepperCubit extends Cubit<DisplayStepperState> {

  DisplayStepperCubit()
      : super(DisplayStepperState(
      status: displayStepperStatus.remove_stepper));

  Future<void> displayStepper(bool isDisplay) async {

    print(
        'DisplayStepperCubit : displayStepper() : DEBUT ');

    if(isDisplay)
      emit(state.copyWith(
        status: displayStepperStatus.display_stepper));
    else
      emit(state.copyWith(
          status: displayStepperStatus.remove_stepper));
  }
}