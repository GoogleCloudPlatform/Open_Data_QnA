class StepperExpertInfo {
  final String? uri;
  final String? body;
  final String? header;
  final String? response;
  final String? generatedSQLText;
  final List<String> ? answerList;
  final String? knownDB;
  final String? finalNLAnswer;
  final int? statusCode;
  final int? stepDuration;
  final String? graphTitle;
  final String? xAxisTitle;
  final String? yAxisTitle;
  final String? summary;

  const StepperExpertInfo({
    this.uri = "",
    this.body = '{"message" : "No data"}',
    this.header = '{"message" : "No data"}',
    this.response = '{"message" : "No data"}',
    this.generatedSQLText = "",
    this.knownDB = "",
    this.finalNLAnswer = "",
    this.statusCode = 0,
    this.stepDuration = 0,
    this.graphTitle = "",
    this.xAxisTitle = "",
    this.yAxisTitle = "",
    this.summary = "",
    this.answerList = const [""]
  });
}
