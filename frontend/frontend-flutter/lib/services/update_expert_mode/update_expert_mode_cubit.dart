import 'package:bloc/bloc.dart';
import 'package:ttmd/services/update_expert_mode/update_expert_mode_state.dart';

import '../../utils/TextToDocParameter.dart';


class UpdateExpertModeCubit extends Cubit<UpdateExpertModeState> {

  UpdateExpertModeCubit()
      : super(UpdateExpertModeState(
      status: updateExpertModeStatus.expert_mode_off));

  Future<void> updateExpertMode(bool isDisplay) async {

    print(
        'UpdateExpertModeCubit : updateExpertMode() : DEBUT ');

    if(isDisplay)
      emit(state.copyWith(
          status: updateExpertModeStatus.expert_mode_on));
    else
      emit(state.copyWith(
          status: updateExpertModeStatus.expert_mode_off));
  }
}