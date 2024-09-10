import 'package:equatable/equatable.dart';


enum displayStepperStatus {display_stepper,remove_stepper}

class DisplayStepperState extends Equatable {
  final displayStepperStatus status;

  DisplayStepperState({
    this.status = displayStepperStatus.remove_stepper,
  });

  @override
  List<Object> get props => [this.status];

  DisplayStepperState copyWith({
    displayStepperStatus? status,
  })  {
    print('DisplayStepperState : copyWith() : status = ' + status.toString());
    return DisplayStepperState(
      status: status ?? this.status,
    );
  }
}