import 'dart:typed_data';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:intl/intl.dart';
import 'package:flutter_chat_ui/flutter_chat_ui.dart';
import 'package:flutter_chat_types/flutter_chat_types.dart' as types;
import 'dart:convert';
import 'dart:math';
import 'package:file_picker/file_picker.dart';
import 'package:bubble/bubble.dart';
import 'package:http/http.dart' as http;
import 'package:deep_pick/deep_pick.dart';
import 'package:ttmd/utils/stepper_expert_info.dart';
import '../services/first_question/first_question_cubit.dart';
import '../services/load_question/load_question_cubit.dart';
import '../services/new_suggestions/new_suggestion_cubit.dart';
import '../services/update_stepper/update_stepper_cubit.dart';
import '../services/update_stepper/update_stepper_state.dart';
import '../utils/TextToDocParameter.dart';
import '../utils/custom_input_field.dart' as cif;
import '../utils/custom_input_field.dart';
import 'dart:html' as html;
import 'package:screenshot/screenshot.dart';
import '../utils/tabbed_container.dart';
import 'package:simple_http_api/simple_http_api.dart';
import "dart:js" as js;

// For the testing purposes, you should probably use https://pub.dev/packages/uuid.
String randomString() {
  final random = Random.secure();
  final values = List<int>.generate(16, (i) => random.nextInt(255));
  return base64UrlEncode(values);
}

class Bot extends StatefulWidget {
  final TextEditingController? textEditingController;
  final FirebaseFirestore? db;
  const Bot({Key? key, this.textEditingController, this.db}) : super(key: key);

  @override
  State<Bot> createState() => BotState();
}

class BotState extends State<Bot> with SingleTickerProviderStateMixin {
  final List<types.Message> _messages = [];
  final Map<String, Uint8List> _graphsImagesMap = {};
  final _user = types.User(
      id: '82091008-a484-4a89-ae75-a22bf8d6f3ac',
      firstName: '${TextToDocParameter.firstName}',
      lastName: '${TextToDocParameter.lastName}'
  );
  final _userAvatar = types.User(
      id: '82091010-a484-4a89-ae75-a22bf8d6f3ab',
      firstName: '${TextToDocParameter.firstName}',
      lastName: '${TextToDocParameter.lastName}'
  );
  final _user1 = const types.User(
      id: '82091009-a485-4a90-ae76-a22bf8d6f3ad',
      firstName: 'Open Data QnA',
      lastName: 'Assistant');
  String textMLKit = "";
  String textDocAi = "";
  String responsePalMBody = "";
  String streamingText = "";
  String requestPalMBody = "";
  String responseDLPMBody = "";
  String requestDLPBody = "";
  List<String> sourceList = [];
  Map<String, List<String>> mapSource = Map();
  String colorBubble = "user";
  Chat? chat;
  Size? screenSize;
  bool isFirstQuestion = true;
  bool isProcessing = false;
  ScreenshotController screenshotController = ScreenshotController();
  ScreenshotController screenshotController1 = ScreenshotController();
  List<GlobalKey<PaginatedDataTableState>> tableKeyList = [];
  Map<String, PaginatedDataTable> tableKeyMap = {};
  String? imageId;
  bool isGraphKeyAdded = false;
  bool isTableKeyAdded = false;
  Map mainQuestionsFollowUpQuestions = {};
  late TabController _tabController;
  bool _isThumbsUpHovered = false;
  bool _isThumbsDownHovered = false;
  bool _isCopyHovered = false;
  static bool isTextToDoc = false;
  int _selectedIndex = 0;
  InAppWebViewController? webViewController;
  Map<String,String> mapAnonymisationGraph = {};
  Container? graphContainer;

  @override
  void initState() {
    setup();
    super.initState();
  }

  @override
  void dispose() {
    _tabController!.dispose();
    webViewController!.dispose();
    super.dispose();
  }

  Future<void> setup() async {
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  Widget build(BuildContext context) {

    screenSize = MediaQuery.of(context).size;

    chat = Chat(
      emptyState: Text(""),
      avatarBuilder: avatarBuilder,
      customBottomWidget: CustomInputField(
          onAttachmentPressed: _handleAttachmentPressed,
          onSendPressed: _handleSendPressed,
          db: widget.db,
          options: cif.InputOptions(
              textEditingController: widget.textEditingController)),
      customMessageBuilder: customMessageBuilder,
      //inputOptions: InputOptions(textEditingController: widget.textEditingController),
      messages: _messages,
      onSendPressed: _handleSendPressed,
      //onAttachmentPressed: _handleImageSelection,
      //onAttachmentPressed: _handleFileSelection
      onAttachmentPressed: _handleAttachmentPressed,
      onMessageTap: _handleMessageTap,
      onPreviewDataFetched: _handlePreviewDataFetched,
      showUserAvatars: true,
      showUserNames: true,
      bubbleBuilder: _bubbleBuilder,
      user: _user,
      messageWidthRatio: 0.9,
      theme: DefaultChatTheme(
        seenIcon: Text(
          'read',
          style: TextStyle(
            fontSize: 10.0,
          ),
        ),
        backgroundColor: Color(
            0xFFF0F2F6), //Color.fromRGBO(242, 242, 242, 1.0),//Colors.black12,
        messageMaxWidth: screenSize!.width,
      ),
    );

    print(
        " bot: build() : TextToDocParameter.isTextTodocGlobal = ${TextToDocParameter.isTextTodocGlobal}");
    return Flexible(
      fit: FlexFit.loose,
      flex: 9,
      child: Stack(children: <Widget>[
        Screenshot(child: chat!, controller: screenshotController1),
        isProcessing
            ? Positioned(
                left: 650,
                top: 300,
                child: SizedBox(
                  width: 100,
                  height: 100,
                  child: CircularProgressIndicator(
                    strokeWidth: 6,
                  ),
                ),
              )
            : dummyFunction(),
      ]),
    );
  }

  Text dummyFunction() {
    print("Bot: dummyFunction() : START");
    Future.delayed(const Duration(seconds: 2), () {
      generateSnapshot();
    });

    return Text("");
  }

  Future<void> generateSnapshot() async {
    print("Bot: generateSnapshot() : START");
    //Does not work for now because the flutter_inappwebview is not supported by the creenshot package
    //it return a blank image. InAppWebViewController.takeScreenshot() is not implemented for the web platform.
    //So commenting out the code below :

    /*if (isGraphKeyAdded == true &&
        !TextToDocParameter.isTextTodocGlobal) {
      print(
          "Bot: generateSnapshot() : isGraphKeyAdded = $isGraphKeyAdded");
      print("Bot: generateSnapshot() : imageId = ${imageId}");
      Uint8List img = await _generateImage(graphContainer!);
      _graphsImagesMap[imageId!] = img;
      isGraphKeyAdded = false;
      print("Bot: generateSnapshot() : isGraphKeyAdded = $isGraphKeyAdded");
      print("Bot: generateSnapshot() : _graphsImagesMap.length = ${_graphsImagesMap.length}");
    } */
    if (tableKeyList.isNotEmpty &&
        isTableKeyAdded == true &&
        !TextToDocParameter.isTextTodocGlobal) {
      print(
          "Bot: generateSnapshot() : tableKeyList.length = ${tableKeyList.length}");
      print(
          "Bot: generateSnapshot() : tableKeyList.isNotEmpty = ${tableKeyList.isNotEmpty} && isTableKeyAdded = $isTableKeyAdded");
      print(
          "Bot: generateSnapshot() : tableKeyList.last = ${tableKeyList.last.toString()}");
      /* Commenting out this code until syncfusion_flutter_pdfviewer package is replaced
      PaginatedDataTable pdfGrid = await tableKeyList.last.currentState!.widget;
      print("Bot: generateSnapshot() : pdfGrid = $pdfGrid");
      tableKeyMap[tableKeyList.last.toString()] = pdfGrid!;
      print(
          "Bot: generateSnapshot() : tableKeyMap.length = ${tableKeyMap.length}");
      print("Bot: generateSnapshot() : isTableKeyAdded = $isTableKeyAdded"); */
      isTableKeyAdded = false;
    }
    //tableKeyMap
  }

  void _addMessage(types.Message message) {
    print('Bot : _addMessage() message.text = ' + message.toJson().toString());
    setState(() {
      _messages.insert(0, message);
    });

    print('Bot : _addMessage() : _messages.length = ' +
        _messages.length.toString());
    print('Bot : _addMessage() : _messages = ' + _messages.toString());
  }

  void _handleSendPressed(types.PartialText message) {
    final textMessage = types.TextMessage(
        author: _userAvatar,
        createdAt: DateTime.now().millisecondsSinceEpoch,
        id: randomString(),
        text: message.text,
        type: types.MessageType.text,
        metadata: {"dataSource": "user"});
    bool isACannedQuestion = false;

    print('Bot : _handleSendPressed() textMessage.text = ' + textMessage.text);
    print('Bot : _handleSendPressed() textMessage.author.firstName = ' +
        textMessage.author.firstName!);

    _addMessage(textMessage);

    //Remove the welcome message after the first question asked
    if (isFirstQuestion) {
      print('Bot : _handleSendPressed() : isFirstQuestion = ' +
          isFirstQuestion.toString());
      isFirstQuestion = false;
      BlocProvider.of<FirstQuestionCubit>(context).removeWelcomeMessage();
    }

    print(
        "main: initState() : After BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded() : TextToDocParameter.lastScenarioNumber =  ${TextToDocParameter.lastScenarioNumber}");

    BlocProvider.of<NewSuggestionCubit>(context).generateNewSuggestions(
        TextToDocParameter.lastScenarioNumber, message.text,
        lastCannedQuestion: TextToDocParameter.lastCannedQuestion,
        isACannedQuestion: isACannedQuestion);

    //Update the question history on the side menu
    //BlocProvider.of<LoadQuestionCubit>(context).loadQuestionToChat(question: message.text, time: displayDateTime());
    BlocProvider.of<LoadQuestionCubit>(context)
        .loadQuestionToChat(question: message.text, time: "rr");

    //Update stepper state
    BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded(
        status: StepperStatus.enter_question,
        message: "Question entered.",
        stateStepper: StepState.complete,
        isActiveStepper: true);
    print(
        "main: initState() : After BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded() : stepper initialized");

    _handleReceivedResponse(textMessage.text, "text");

    setState(() {
      isProcessing = true;
    });
  }

  void _handleReceivedResponse(String msg, String type) async {
    String mime = "";
    String id = randomString();
    bool isText = true;
    dynamic dataViz;
    GlobalKey<PaginatedDataTableState> tableKey = GlobalKey();
    imageId = randomString();
    PaginatedDataTable? tableGrid;

    //TextToDocParameter.isTextTodocGlobal = true;
    print('Bot : _handleReceivedResponse(): START ');
    print('Bot : _handleReceivedResponse(): isTextToDoc = ' +
        isTextToDoc.toString());
    print(
        'Bot : _handleReceivedResponse(): TextToDocParameter.isTextTodocGlobal = ${TextToDocParameter.isTextTodocGlobal}');

    switch (type) {
      case "text":
        mime = "application/json";
        break;
      case "pdf":
        mime = "application/pdf";
        break;
      case "png":
        //case "image":
        mime = "image/png";
        break;
      case "jpeg":
        //case "image":
        mime = "image/jpeg";
        break;
      default:
        print('Error, out of range : index = $type ');
    }

    print('Bot : _handleReceivedResponse(): type = ' +
        type +
        ' : mime = ' +
        mime);

    print('Bot : _handleReceivedResponse(): msg = ' + msg);

    if (!TextToDocParameter.isTextTodocGlobal) {
      //NL2SQL request
      print('Bot : _handleReceivedResponse(): USING NL2SQL');

      //Get generated reponse
      var rep = await getChatResponseNew(msg, mime, id, user: _user1);

      print(
          'Bot : _handleReceivedResponse(): back from getChatResponseNew() : rep = $rep');

      //graphConfig = rep![2] as GraphConfig;
      dataViz = rep![2];

      if ((rep![0] as String).length == 0) {
        //knownDB
        rep[0] =
            '[{"response": "The request did not return meaningful information. It could be because the question has not been formulated properly or some context is missing."}]';
      } else {
        //The request has been successful and an entry has been created on ${TextToDocParameter.firestore_database_id}
        //Adding the user_grouping and scenario_name to the entry because as of now it does not contain this data.
        //If in the future user_grouping is added, _updateUserGroupingInSessionLogs() below can be removed
        _updateUserGroupingInSessionLogs();

        tableGrid = createPaginatedTable(rep[0] as String);

        tableKeyList.add(tableKey);
        isTableKeyAdded = true;
        print(
            'Bot : _handleReceivedResponse():  tableKey = $tableKey : isTableKeyAdded = $isTableKeyAdded');
      }
      isText = rep[1] as bool;

      print(
          'Bot : _handleReceivedResponse():  repFinal = ' + (rep[0] as String));
      print(
          'Bot : _handleReceivedResponse():  isText = ' + (rep[1].toString()));

      print(
          'Bot : _handleReceivedResponseNew() : CustomMessage : isText = ${isText}');

      if (isText) {
        print(
            'Bot : _handleReceivedResponseNew() : isText = $isText : dataViz = ${dataViz}');
        imageId = "no_image";
      } else {
        print(
            'Bot : _handleReceivedResponseNew() : CustomMessage : imageId = $imageId');
      }

      final customMessage = types.CustomMessage(
          author: _user1,
          createdAt: DateTime.now().millisecondsSinceEpoch,
          id: randomString(),
          type: types.MessageType.custom,
          metadata: {
            "graph": dataViz,
            "textSummary": rep[3] as String,
            "imageId": imageId,
            "dataSource": tableGrid,
            "tableKey": tableKey.toString(),
          });

      _addMessage(customMessage);
    } else {
      print('Bot : _handleReceivedResponse(): USING TEXT2DOC');

      var rep =
          await getChatResponseTextToDoCStream(msg, mime, id, user: _user1);

      imageId = "no_image";

      final customMessage = types.CustomMessage(
          author: _user1,
          createdAt: DateTime.now().millisecondsSinceEpoch,
          id: randomString(),
          type: types.MessageType.custom,
          metadata: {
            "graph": dataViz,
            "textSummary": rep![3] as String,
            "imageId": imageId,
            "dataSource": null,
            "tableKey": tableKey.toString(),
            "stream": rep![4] as Stream<BaseChunk<Object>> ?? null,
            "stopWatch": rep![5] as Stopwatch ?? null
          });

      _addMessage(customMessage);
    }

    setState(() {
      isProcessing = false;
    });
  }

  Future<List<Object>?> getChatResponseTextToDoCStream(
      String msg, String mime, String id,
      {types.User? user}) async {
    List<String>? reqResp = [];
    List<Object> RespList = [];
    Uri url;
    String userQuestion = "";
    String body = "";

    print('Bot : getChatResponseTextToDoCStream() : START');
    url = Uri.parse(
        'https://colab-cloudrun-template-ra1-uz6w7mqrka-uc.a.run.app/generate_streaming');

    print('Bot : getChatResponseTextToDoCStream() : url = ' +
        url.host +
        url.path);

    Map<String, String>? headers = {
      "Content-Type": "$mime",
    };

    print('Bot : getChatResponseTextToDoCStream() : headers = $headers');

    userQuestion = msg;
    print(
        'Bot : getChatResponseTextToDoCStream() : userQuestion = $userQuestion');

    body = '''{
    "query": "${userQuestion}"
    }''';
    print('Bot : getChatResponseTextToDoCStream() : request_body = $body');

    var eventSource = EventSource(url, ApiMethod.post);
    eventSource.setHeaders(headers);

    final cancelToken = TimingToken(Duration(seconds: 5));

    final stopwatchtextToDoc = Stopwatch()..start();
    //final stream = eventSource.send(body: body, cancelToken: cancelToken);
    var stream = eventSource.send(body: body).asBroadcastStream();

    print('Bot : getChatResponseTextToDoCStream() : stream = $stream');

    RespList.add("test"); // 0 : body of the answer
    RespList.add(true); //1 : is text
    RespList.add("dump"); // 2 : Graph config
    //RespList.add("Your request can not be answered right now. Please try again.");
    RespList.add("firstChunck"); // 3: text
    RespList.add(stream); //4: stream
    RespList.add(stopwatchtextToDoc); //5: stopwatchtextToDoc

    print('Bot : getChatResponseTextToDoCStream() : END');
    return RespList;
  }

  Future<String> waitForFirstSSEData(
      Stream<BaseChunk<Object>> stream, EventSource eventSource) async {
    int count = 0;
    print('Bot : waitForFirstSSEData() : START');

    stream.listen(
      (event) {
        if (eventSource.isWeb) {
          print('Bot : waitForFirstSSEData(): eventSource.isWeb');
          print('Bot : waitForFirstSSEData(): count = $count');
          print('Bot : waitForFirstSSEData(): event.chunk = ${event.chunk}');

          responsePalMBody = responsePalMBody + event.chunk.toString();
          var answerPlainTextChunck =
              pickFromJson(event.chunk.toString(), 'response').asStringOrNull();
          print(
              'Bot : waitForFirstSSEData(): answerPlainTextChunck = ${answerPlainTextChunck}');

          setState(() {
            streamingText = streamingText + answerPlainTextChunck!;
          });

          if (count == 0) {
            final textMessage = types.TextMessage(
                author: _user1,
                createdAt: DateTime.now().millisecondsSinceEpoch,
                id: randomString(),
                text: streamingText,
                type: types.MessageType.text,
                metadata: {"dataSource": null});

            _addMessage(textMessage);
          }
          count++;
        } else {
          print('Bot : waitForFirstSSEData(): eventSource.isNotWeb');
          final encoding = event.getEncoding();

          print(
              'Bot : waitForFirstSSEData(): eventSource.isNotWeb : encoding.decode(event.chunk as List<int>) = ${encoding.decode(event.chunk as List<int>)}');
        }
      },
      onError: (err) => print('Bot : waitForFirstSSEData(): err = $err'),
      onDone: () {
        eventSource.close;
        streamingText = "";
      },
    );

    return "";
  }

  Future<List<Object>?> getChatResponseTextToDoC(
      String msg, String mime, String id,
      {types.User? user}) async {
    List<String>? reqResp = [];
    List<Object> RespList = [];
    Uri url;
    String userQuestion = "";
    String body = "";
    String finalAnswer = "";

    print('Bot : getChatResponseTextToDoC() : START');
    url = Uri.parse(
        'https://multi-modal-rag-dgujjntxuq-uc.a.run.app/generate-answer');

    print('Bot : getChatResponseTextToDoC() : url = ' + url.host + url.path);

    print('Bot : getChatResponseTextToDoC() : mime = ' + mime);

    Map<String, String>? _headers = {
      "Content-Type": "$mime",
    };

    userQuestion = msg;
    print('Bot : getChatResponseTextToDoC() : userQuestion = ' + userQuestion);

    body = '''{
    "query": "${userQuestion}"
    }''';

    print('Bot : getChatResponseTextToDoC() : request_body = ' + body);

    final stopwatchtextToDoc = Stopwatch()..start();
    final _response = await http.post(url, headers: _headers, body: body);
    stopwatchtextToDoc.stop();

    if (_response.statusCode == 200) {
      print('Bot : getChatResponseTextToDoC() : Status code 200 ');
      responsePalMBody = _response.body
          .replaceAll(RegExp(r'(\\u003cb|\\u003e|\\u003c|\\u003e|(\/n))'), '');

      var answerPlainText =
          pickFromJson(responsePalMBody, 'response').asStringOrNull();

      if (answerPlainText != null) {
        finalAnswer = answerPlainText;
        print(
            'Bot : getChatResponseTextToDoC() : answerPlainText != null : finalAnswer = ' +
                finalAnswer);
      } else {
        finalAnswer =
            "Your request can not be answered right now. Please try again.";
        print(
            'Bot : getChatResponseTextToDoC() : answerPlainText == null : finalAnswer = ' +
                finalAnswer);
      }

      reqResp.add(body);
      reqResp.add(responsePalMBody);

      print(
          'Bot : getChatResponseTextToDoC() : /generate_answer : reqResp[0] = ' +
              reqResp[0]);
      print(
          'Bot : getChatResponseTextToDoC() : /generate_answer : reqResp[1] = ' +
              reqResp[1]);

      RespList.add(responsePalMBody); // 0 : body of the answer
      RespList.add(true); //1 : is text
      RespList.add("dump"); // 2 : Grah config
      RespList.add(finalAnswer); //3 : answer in plain text

      //Update stepper state to get_text_summary
      BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded(
          status: StepperStatus.get_text_summary,
          message: "NL answer received in",
          stateStepper: StepState.complete,
          isActiveStepper: true,
          debugInfo: StepperExpertInfo(
            uri: url!.host + url!.path,
            body: body,
            header: jsonEncode(_headers!),
            response: responsePalMBody,
            summary: finalAnswer,
            statusCode: _response.statusCode,
            stepDuration: stopwatchtextToDoc.elapsed.inMilliseconds,
          ));
    } else {
      print(
          'Bot : getChatResponseTextToDoC() : _response.statusCode = ${_response.statusCode}');
      RespList.add("test"); // 0 : body of the answer
      RespList.add(true); //1 : is text
      RespList.add("dump"); // 2 : Grah config
      RespList.add(
          "Your request can not be answered right now. Please try again."); //3 : answer in plain text
    }

    print('Bot : getChatResponseTextToDoC() : END');
    return RespList;
  }

  Future<dynamic> ShowCapturedWidget(
      BuildContext context, Uint8List capturedImage) {
    print("Bot: ShowCapturedWidget() : START");
    return showDialog(
      useSafeArea: false,
      context: context,
      builder: (context) => Scaffold(
        appBar: AppBar(
          title: Text("Captured widget screenshot"),
        ),
        body: Center(child: Image.memory(capturedImage)),
      ),
    );
  }

  List<String> transfromDynamicListToStringList(List<dynamic> list) {
    List<String> dataList = [];

    print(
        'Bot: transfromDynamicListToStringList() :  list.length = ${list.length}');
    print('Bot: transfromDynamicListToStringList() :  list = $list');

    for (int i = 0; i <= list.length - 1; i++) {
      dataList.add(list.elementAt(i) as String);
    }

    if (dataList is List<String>)
      print(
          'BarGraph: transfromDynamicListToStringList() :  dataList is of type List<String>');

    print(
        'BarGraph: transfromDynamicListToStringList() :  dataList = $dataList');
    return dataList;
  }

  void _handleFileSelection() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );

    if (result != null && result.files.single.path != null) {
      String res = "";
      final message = types.FileMessage(
        author: _user,
        createdAt: DateTime.now().millisecondsSinceEpoch,
        id: randomString(),
        name: result.files.single.name,
        size: result.files.single.size,
        uri: result.files.single.path!,
      );

      _addMessage(message);

      print('Bot : _handleReceivedResponse() uri = ' + message.uri);
      textDocAi = "not implemented yet"; //await extractTextMLKit(message.uri);
      res = textDocAi.replaceAll('"', " ");

      print('Bot : _handleReceivedResponse() : textDocAi = ' + res);

      _handleReceivedResponse(
          'Ecris en français un résumé du texte ci-dessous en mois de 50 mots:\n' +
              res,
          "png");
    }
  }

  void _handleMessageTap(BuildContext _, types.Message message) async {
    print('Bot : _handleMessageTap() : DEBUT = ');
    if (message is types.FileMessage) {
      print('Bot : _handleMessageTap() : types.FileMessage : message.uri = ' +
          message.uri);
    }
  }

  void _handlePreviewDataFetched(
    types.TextMessage message,
    types.PreviewData previewData,
  ) {
    final index = _messages.indexWhere((element) => element.id == message.id);
    final updatedMessage = (_messages[index] as types.TextMessage).copyWith(
      previewData: previewData,
    );

    setState(() {
      _messages[index] = updatedMessage;
    });
  }

  void _handleAttachmentPressed() {
    showModalBottomSheet<void>(
      context: context,
      builder: (BuildContext context) => SafeArea(
        child: SizedBox(
          height: 144,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: const Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: Text('Photo'),
                ),
              ),
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  _handleFileSelection();
                },
                child: const Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: Text('File'),
                ),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: Text('Cancel'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _bubbleBuilder(
    Widget child, {
    required message,
    required nextMessageInGroup,
  }) {
    String colorString = colorBubble;

    return Container(
      width: screenSize!.width,
      child: Bubble(
        child: child,
        color: message.author.id !=
                '82091010-a484-4a89-ae75-a22bf8d6f3ab'
            ? const Color(0xfff5f5f7) //Color(0xfff5f5f7)
            : const Color(0xffffffff), //Color(0xfffaf9de),
        margin: null,
        nip: BubbleNip.no,
      ),
    );
  }

  Widget customMessageBuilder(types.CustomMessage customMessage,
      {required int messageWidth}) {
    print('Bot : customMessageBuilder(): START');
    String inputString = "";

    return Container(
        //width: 500,
        child: Column(
      mainAxisAlignment: MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.center,
      mainAxisSize: MainAxisSize.min,
      children: [
        //Display the firstname and lastname
        Container(
            padding: const EdgeInsets.only(top: 20, left: 20),
            width: screenSize!.width,
            child: Text(_user1.firstName! + " " + _user1.lastName! + "\n",
                style: TextStyle(
                    fontSize: 12,
                    color: Colors.green,
                    fontWeight: FontWeight.bold),
                textAlign: TextAlign.left)),
        //Display answer
        !customMessage.metadata!.containsKey('stream') ||
                customMessage.metadata!['textSummary'] != "firstChunck"
            ? Container(
                padding: const EdgeInsets.only(top: 20, left: 20),
                width: screenSize!.width,
                child: Text(customMessage.metadata!['textSummary'],
                    textAlign: TextAlign.start, style: TextStyle(fontSize: 16)),
              )
            : StreamBuilder<BaseChunk<Object>>(
                stream: customMessage.metadata!['stream'],
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    print(
                        'Bot : customMessageBuilder(): StreamBuilder : snapshot.connectionState : WAITING');
                    streamingText = "";
                    return SizedBox(
                      width: 100,
                      height: 100,
                      child: CircularProgressIndicator(
                        strokeWidth: 6,
                      ),
                    ); // Display a loading indicator when waiting for data.
                  } else if (snapshot.hasError) {
                    print(
                        'Bot : customMessageBuilder(): StreamBuilder : snapshot.hasError : ERROR');
                    return Text(
                        'Error: ${snapshot.error}'); // Display an error message if an error occurs.
                  } else if (!snapshot.hasData) {
                    print(
                        'Bot : customMessageBuilder(): StreamBuilder : !snapshot.hasData : No data available');
                    return Text(
                        'No data available'); // Display a message when no data is available.
                  } else {
                    print(
                        'Bot : customMessageBuilder(): StreamBuilder : snapshot.hasData');
                    var answerPlainTextChunck = pickFromJson(
                            snapshot.data!.chunk.toString(), 'response')
                        .asStringOrNull();

                    if (answerPlainTextChunck != "end_stream") {
                      //streamingText = streamingText + answerPlainTextChunck!;
                      inputString = inputString + answerPlainTextChunck!;
                      print(
                          'Bot : customMessageBuilder(): StreamBuilder : snapshot.hasData : answerPlainTextChunck != end_stream');
                      //customMessage.metadata!['eventSource'].close();
                    } else {
                      customMessage.metadata!['textSummary'] = inputString;
                      print(
                          'Bot : customMessageBuilder(): StreamBuilder : snapshot.hasData : answerPlainTextChunck == end_stream');
                      Stopwatch stopwatchStreaming =
                          customMessage.metadata!['stopWatch'] as Stopwatch;
                      stopwatchStreaming.stop();

                      //Update stepper state to get_text_summary
                      BlocProvider.of<UpdateStepperCubit>(context)
                          .updateStepperStatusUploaded(
                              status: StepperStatus.get_text_summary,
                              message: "NL answer received in",
                              stateStepper: StepState.complete,
                              isActiveStepper: true,
                              debugInfo: StepperExpertInfo(
                                uri:
                                    "https://colab-cloudrun-template-ra1-uz6w7mqrka-uc.a.run.app/generate_streaming",
                                body: '{"N/A": "N/A"}',
                                header: '{"Content-Type": "app/json}',
                                response: responsePalMBody,
                                summary: inputString,
                                statusCode: 200,
                                stepDuration: stopwatchStreaming.elapsed
                                    .inMilliseconds, //stopwatchtextToDoc.elapsed.inMilliseconds,
                              ));
                    }
                    return Container(
                      padding: const EdgeInsets.only(top: 20, left: 20),
                      width: screenSize!.width,
                      child: Text(inputString, //streamingText,
                          textAlign: TextAlign.start,
                          style: TextStyle(fontSize: 16)),
                    );
                  }
                }),
        if (customMessage.metadata!['dataSource'] != null &&
            !customMessage.metadata!['textSummary']
                .contains("The request did not return meaningful information"))
          Container(
            child: TabbedContainer(
              initialIndex: customMessage.metadata!['graph'] != null ? 1 : 0,
              controller: _tabController,
              tabs: const [
                Tab(text: "Table", icon: Icon(Icons.table_rows_sharp)),
                Tab(text: "Graph", icon: Icon(Icons.bar_chart)),
              ],
              tabViews: [
                Center(
                    child: SingleChildScrollView(child: Container(width: screenSize!.width ,child: customMessage.metadata!['dataSource'] ?? Text('No Data')))),
                Center(
                    child: getGoogleGraph(customMessage.metadata!['graph']) ?? Text('No Graph')),
              ],
            ),
          ),
        SizedBox(height: 40),
        //Add feedback
        Container(
          width: screenSize!.width / 10,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10.0),
            color: Colors.black12, // Adjust the radius as needed
          ),
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                InkWell(
                  onTap: () {
                    showFeedbackDialog();
                  },
                  onHover: (value) {
                    setState(() {
                      _isThumbsUpHovered = value;
                    });
                  },
                  child: Tooltip(
                    message: "Provide your feedback on the generated answer",
                    child: new Image(
                      image: new AssetImage("assets/images/thumbs_up1.png"),
                      width: 20,
                      height: 20,
                      color: _isThumbsUpHovered
                          ? Colors.grey.withOpacity(0.5)
                          : null,
                      colorBlendMode:
                          _isThumbsUpHovered ? BlendMode.modulate : null,
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.center,
                    ),
                  ),
                ),
                InkWell(
                  onTap: () {
                    showFeedbackDialog();
                  },
                  onHover: (value) {
                    setState(() {
                      _isThumbsDownHovered = value;
                    });
                  },
                  child: Tooltip(
                    message: "Provide your feedback on the generated answer",
                    child: new Image(
                      image: new AssetImage("assets/images/thumbs_down1.png"),
                      width: 20,
                      height: 20,
                      color: _isThumbsDownHovered
                          ? Colors.grey.withOpacity(0.5)
                          : null,
                      colorBlendMode:
                          _isThumbsDownHovered ? BlendMode.modulate : null,
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.center,
                    ),
                  ),
                ),
                InkWell(
                  onTap: () {
                    print("Bot: copy : onTap : START");
                    print('Bot : customMessageBuilder() : copy : onTap: () : START');
                    copyGraphToClipBoard(customMessage.metadata!['imageId'],
                        customMessage.metadata!['textSummary']);
                  },
                  onHover: (value) {
                    setState(() {
                      _isCopyHovered = value;
                    });
                  },
                  child: Tooltip(
                    message: "Copy the answer",
                    child: new Image(
                      image: new AssetImage("assets/images/copy1.png"),
                      width: 20,
                      height: 20,
                      color:
                          _isCopyHovered ? Colors.grey.withOpacity(0.5) : null,
                      colorBlendMode:
                          _isCopyHovered ? BlendMode.modulate : null,
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.center,
                    ),
                  ),
                ),
              ],
            ),
          ),
        )
        //customMessage.metadata!['graph'],
      ],
    ));
  }

  Widget getGoogleGraph(dynamic dataViz) {
    print(" bot: getGoogleGraph() : START");
    Container container;

    if (dataViz!["chart_div"]! != null) {
      print(
          'bot: getGoogleGraph() : dataViz!["chart_div"]! = ${dataViz!["chart_div"]!}');

      String htmlPre = """<html>
                          <head>
                            <!--Load the AJAX API-->
                            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                            <script type="text/javascript"> """;
      String htmlPost = """</script>
                          </head>
                        
                          <body>
                            <!--Div that will hold the pie chart-->
                            <div id="chart_div"></div>
                          </body>
                        </html>""";

      container =  Container(
        child: InAppWebView(
          initialData: InAppWebViewInitialData(
              data: htmlPre + "\n" + dataViz!["chart_div"]!.replaceAll('width: 600,','width: 1200,').replaceAll('height: 300,', 'height: 600,') + htmlPost + "\n"),
          onWebViewCreated: (controller) {
            webViewController = controller;
          },
        ),
      );

      isGraphKeyAdded = true;
      graphContainer = container;

      return container;
    } else {
      return Text("No Chart",
          style: TextStyle(
              fontSize: 16,
              color: Colors.indigoAccent,
              fontWeight: FontWeight.bold));
    }
  }

  Widget getGoogleTable(dynamic dataViz) {
    print("bot: getGoogleTable() : START");
    if (dataViz!["chart_div_1"]! != null) {
      print(
          'bot: getGoogleTable() : dataViz!["chart_div_1"]! = ${dataViz!["chart_div_1"]!}');
      String htmlPre = """<html>
                          <head>
                            <!--Load the AJAX API-->
                            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                            <script type="text/javascript"> """;
      String htmlPost = """</script>
                          </head>
                        
                          <body>
                            <!--Div that will hold the pie chart-->
                            <div id="chart_div_1"></div>
                          </body>
                        </html>""";

      return Container(
        child: InAppWebView(
          initialData: InAppWebViewInitialData(
              data:
                  htmlPre + "\n" + dataViz!["chart_div_1"]!.replaceAll('width: 600,','width: 1200,').replaceAll('height: 300,', 'height: 600,') + htmlPost + "\n"),
          onWebViewCreated: (controller) {
            webViewController = controller;
          },
        ),
      );
    } else
      return Text("No data",
          style: TextStyle(
              fontSize: 16,
              color: Colors.indigoAccent,
              fontWeight: FontWeight.bold));
  }

  Future<Uint8List> _generateImage(Widget widget) async {
    print('Bot : _generateImage() : START');

    //Uint8List capturedImage = await screenshotController.captureFromWidget(widget); => not supported in Flutter Web for now
    Uint8List? capturedImage =  await webViewController!.takeScreenshot();

    print('Bot : _generateImage() : capturedImage != null)');
    _graphsImagesMap[imageId!] = capturedImage!;
    //ShowCapturedWidget(context, capturedImage!);

    return capturedImage;
  }


  void showFeedbackDialog() {
    showDialog<void>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("Please rate this answer"),
          content: ConstrainedBox(
            constraints: BoxConstraints(maxHeight: 260.0),
            child: Container(
              //width: screenSize!.width / 2,
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: Column(children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      ElevatedButton(
                        child: Text("Good answer",
                            style: TextStyle(color: Colors.white)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          elevation: 0,
                        ),
                        onPressed: () {},
                      ),
                      SizedBox(width: 30),
                      ElevatedButton(
                        child: Text("Partial answer",
                            style: TextStyle(color: Colors.white)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange,
                          elevation: 0,
                        ),
                        onPressed: () {},
                      ),
                      SizedBox(width: 30),
                      ElevatedButton(
                        child: Text("Incorrect answer",
                            style: TextStyle(color: Colors.white)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          elevation: 0,
                        ),
                        onPressed: () {},
                      ),
                    ],
                  ),
                  SizedBox(height: 50),
                  TextField(
                    decoration: InputDecoration(
                      border: OutlineInputBorder(),
                      labelText:
                          'Please provide additionnal feedback (optional)',
                    ),
                    maxLines: null,
                    minLines: 5,
                  ),
                ]),
              ),
            ),
          ),
          //Text(DicInfoExtractedMap.toString(),),
          actions: <Widget>[
            TextButton(
              style: TextButton.styleFrom(
                textStyle: Theme.of(context).textTheme.labelLarge,
              ),
              child: const Text('Submit'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }

  Future<void> copyGraphToClipBoard(String imageKey, String summaryText) async {
    print('Bot : copyGraphToClipBoard() : START');
    print('Bot : copyGraphToClipBoard() : imageKey = $imageKey');
    print('Bot : copyGraphToClipBoard() : summaryText = $summaryText');

    //For now, the copy button only copies text. Copy of images/widgets is supported, so I'm commenting out the copy of image until
    //the flutter_inappwebview package used to render Google Charts is implementing InAppWebViewController.takeScreenshot() on Flutter Web.
    if(false) {
    //if (imageKey != "no_image") {
      print('Bot : copyGraphToClipBoard() : imageKey != "no_image"');
      print('Bot : copyGraphToClipBoard() : _graphsImagesMap.length = ${_graphsImagesMap.length}');
      Uint8List imgBytes = _graphsImagesMap[imageKey!]!;

      if (imgBytes != null) {
        print('Bot : copyGraphToClipBoard() : imgBytes != null');
        final base64Image = base64Encode(imgBytes);

        try {
          js.context.callMethod('copyBase64ImageToClipboard', [base64Image]);

        } catch (e) {
          print('Bot : copyGraphToClipBoard() : EXCEPTION :  e = $e');
        }
      }
    } else if (summaryText != null || summaryText.length > 0) {
      print('Bot : copyGraphToClipBoard() : summaryText != null || summaryText.length > 0');
      await Clipboard.setData(ClipboardData(text: summaryText));
    } else {
      print('Bot : copyGraphToClipBoard() : else');
      await Clipboard.setData(ClipboardData(text: "No data available."));
    }
  }

  Future<List<Object>?> getChatResponseNew(String msg, String mime, String id,
      {types.User? user}) async {
    List<String>? reqResp = [];
    List<Object> RespList = [];
    Uri urlGenerateSQL;
    Uri urlRunQuery;
    String generatedSQLText = "";
    String userQuestion = "";
    int statusCodeRunQuery = 0;
    String jsonResponseRunQuery = "";

    print('Bot : getChatResponseNew() : START ');

    urlGenerateSQL =
        Uri.parse('${TextToDocParameter.endpoint_opendataqnq}/generate_sql');

    print('Bot : getChatResponseNew() : urlGenerateSQL = ' +
        urlGenerateSQL.host +
        urlGenerateSQL.path);

    print('Bot : getChatResponseNew() : mime = ' + mime);

    Map<String, String>? _headers = {
      "Content-Type": "$mime",
    };

    print(
        'Bot : getChatResponseNew() : BEFORE prepending main question : msg = ' +
            msg);
    if (mainQuestionsFollowUpQuestions.containsKey(msg)) {
      msg = mainQuestionsFollowUpQuestions[msg];
    }

    print(
        'Bot : getChatResponseNew() : AFTER prepending main question : msg = ' +
            msg);

    userQuestion = msg;
    print('Bot : getChatResponseNew() : userQuestion = ' + userQuestion);

    String _body1 = '''{
    "session_id" :"${TextToDocParameter.sessionId}",
    "user_id":"${TextToDocParameter.userID}",
    "user_question":"${userQuestion}",
    "user_grouping":"${TextToDocParameter.currentUserGrouping}"
    }''';

    print('Bot : getChatResponseNew() : _body1 = ' + _body1);
    final stopwatchGenerateSQL = Stopwatch()..start();

    final _response =
        await http.post(urlGenerateSQL, headers: _headers, body: _body1);

    stopwatchGenerateSQL.stop();

    responsePalMBody = _response.body.replaceAll(
        RegExp(r'(\\u003cb|\\u003e|\\u003c|\\u003e|(\/n)|(\\r))'), '');

    print('Bot : getChatResponseNew() : responsePalMBody = $responsePalMBody');

    var error = pickFromJson(responsePalMBody!, 'Error').asStringOrNull();

    print('Bot : getChatResponseNew() : error = $error');
    print(
        'Bot : getChatResponseNew() : _response.statusCode = ${_response.statusCode}');

    if (_response.statusCode == 200 &&
        responsePalMBody!.toLowerCase().contains("select") &&
        (error!.length == 0 ?? false)) {
      print(
          'Bot : getChatResponseNew() : _response.statusCode == 200 && (error!.length == 0 ?? false )');

      TextToDocParameter.sessionId =
          pickFromJson(responsePalMBody!, 'SessionID').asStringOrNull()!;

      print(
          'Bot : getChatResponseNew() : _response.statusCode == 200 && (error!.length == 0 ?? false ) : TextToDocParameter.sessionId = ${TextToDocParameter.sessionId}');

      reqResp.add(_body1);
      reqResp.add(responsePalMBody);

      print('Bot : getChatResponseNew() : /generate_sql : reqResp[0] = ' +
          reqResp[0]);
      print('Bot : getChatResponseNew() : /generate_sql : reqResp[1] = ' +
          reqResp[1]);

      //get the generated SQL query
      generatedSQLText = extractContentGenerateSQL(responsePalMBody);

      //Update stepper state to generate_sql
      BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded(
          status: StepperStatus.generate_sql,
          message: "SQL request generated.",
          stateStepper: StepState.complete,
          isActiveStepper: true,
          debugInfo: StepperExpertInfo(
              uri: urlGenerateSQL.host + urlGenerateSQL.path,
              body: _body1,
              header: jsonEncode(_headers),
              response: responsePalMBody,
              generatedSQLText: generatedSQLText,
              statusCode: _response.statusCode,
              stepDuration: stopwatchGenerateSQL.elapsed.inMilliseconds,
              answerList: [generatedSQLText]));
      print(
          "main: getChatResponseNew() : After BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded() : generate_sql");
      print(
          "main: getChatResponseNew() : generate_sql : generatedSQLText = $generatedSQLText");

      urlRunQuery =
          Uri.parse('${TextToDocParameter.endpoint_opendataqnq}/run_query');

      String _body2 = '''{
      "user_question": "${userQuestion}",
      "user_grouping": "${TextToDocParameter.currentUserGrouping}",
    "generated_sql": "${generatedSQLText}",
    "session_id" : "${TextToDocParameter.sessionId}"
    }''';

      //send the request to get the results in tabular format
      var stopwatchRunQuery = Stopwatch()..start();
      final _responseTabResults =
          await http.post(urlRunQuery, headers: _headers, body: _body2);
      stopwatchRunQuery.stop();

      statusCodeRunQuery = _responseTabResults.statusCode;
      jsonResponseRunQuery = _responseTabResults.body;

      print('Bot : getChatResponseNew() : tabular results: urlRunQuery = ' +
          urlRunQuery.toString());

      print(
          'Bot : getChatResponseNew() : tabular results : _body2 = ' + _body2);
      print(
          'Bot : getChatResponseNew() : tabular results: _responseTabResults.body = ' +
              jsonResponseRunQuery);

      if (TextToDocParameter.anonymized_data) {
        print(
            'Bot : getChatResponseNew() : tabular results: TextToDocParameter.anonymized_data = ${TextToDocParameter.anonymized_data}');
        jsonResponseRunQuery = anonymizedData(jsonResponseRunQuery!);
      }

      //return extractContent(_responseTabResults.body, id, user: user!);
      return extractContentResultsOpenDataQnA(
          jsonResponseRunQuery: jsonResponseRunQuery,
          userQuestion: userQuestion,
          generatedSQLText: generatedSQLText,
          urlRunQuery: urlRunQuery,
          bodyRunQuery: _body2,
          headersRunQuery: _headers,
          statusCodeRunQuery: statusCodeRunQuery,
          elapsedTimeRunQuery: stopwatchRunQuery.elapsed.inMilliseconds);
    } else {
      //Update stepper state to generate_sql
      BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded(
          status: StepperStatus.generate_sql,
          message: "SQL request generated in",
          stateStepper: StepState.complete,
          isActiveStepper: true,
          debugInfo: StepperExpertInfo(
              uri: urlGenerateSQL.host + urlGenerateSQL.path,
              body: _body1,
              header: jsonEncode(_headers),
              response: responsePalMBody,
              generatedSQLText:
                  "An error occurred, no SQL request has been generated.",
              statusCode: _response.statusCode,
              stepDuration: stopwatchGenerateSQL.elapsed.inMilliseconds,
              answerList: [
                "An error occurred, no SQL request has been generated."
              ]));
      print(
          'Bot : getChatResponseNew() : tabular results : _response.statusCode = ${_response.statusCode} and error attribute is set');
      RespList.add("");
      RespList.add(true);
      RespList.add("");
      RespList.add(
          "The request did not return meaningful information. It could be because the question has not been formulated properly or some context is missing.");

      return RespList;
    }
  }

  String extractContentGenerateSQL(String jsonResponse) {
    print("bot() : extractContentGenerateSQL() : START");
    print("bot() : extractContentGenerateSQL() : jsonResponse = $jsonResponse");

    String generatedSQLText = "";
    var error = pickFromJson(jsonResponse, 'Error');
    var generatedSQLTmp =
        pickFromJson(jsonResponse, 'GeneratedSQL').asStringOrNull();
    var responseCode = pickFromJson(jsonResponse, 'ResponseCode');

    print(
        "bot() : extractContentGenerateSQL() : generatedSQLTmp = ${generatedSQLTmp}");

    generatedSQLText = generatedSQLTmp!
        .replaceAll('\n', ' ')
        .replaceAll('"', '\\"'); //generates an exception if null => fix it

    print(
        "bot() : extractContentGenerateSQL() : generatedSQLText = ${generatedSQLText}; ");

    return generatedSQLText!;
  }

  Future<List<Object>> extractContentResultsOpenDataQnA(
      {String? jsonResponseRunQuery,
      String? userQuestion,
      String? generatedSQLText,
      Uri? urlRunQuery,
      String? bodyRunQuery,
      Map<String, String>? headersRunQuery,
      int? statusCodeRunQuery,
      int? elapsedTimeRunQuery}) async {
    //String generatedSQLText = "";
    List<Object> RespList = [];
    bool isText = true;
    dynamic googleChartVizRes;
    String? naturalResponseText = "";

    String textSummary =
        "The request did not return meaningful information. It could be because the question has not been formulated properly or some context is missing.";
    String? knownDB = "";
    String? error = "";

    error = pickFromJson(jsonResponseRunQuery!, 'Error').asStringOrNull();
    knownDB = pickFromJson(jsonResponseRunQuery!, 'KnownDB').asStringOrNull();
    var responseCode = pickFromJson(jsonResponseRunQuery!, 'ResponseCode');
    naturalResponseText =
        pickFromJson(jsonResponseRunQuery!, 'NaturalResponse').asStringOrNull();

    print(
        "bot() : extractContentResultsOpenDataQnA() : knownDB.length = ${knownDB!.length}; ");
    print(
        "bot() : extractContentResultsOpenDataQnA() : knownDB = ${knownDB}; ");

    print(
        "bot() : extractContentResultsOpenDataQnA() : bodyRunQuery = ${bodyRunQuery}; ");

    //Update stepper state to run_query
    BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded(
        status: StepperStatus.run_query,
        message: "Tabular data retrieved in",
        stateStepper: StepState.complete,
        isActiveStepper: true,
        debugInfo: StepperExpertInfo(
            uri: urlRunQuery!.host + urlRunQuery!.path,
            body: bodyRunQuery,
            header: jsonEncode(headersRunQuery!),
            response: jsonResponseRunQuery
                .replaceAll("\"[", "[")
                .replaceAll("]\"", "]")
                .replaceAll("\\\"", "\""),
            knownDB: knownDB,
            statusCode: statusCodeRunQuery,
            stepDuration: elapsedTimeRunQuery,
            answerList: [knownDB]));
    print(
        "main: extractContentResultsOpenDataQnA() : After BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded() : run_query");

    try {
      if (knownDB != "[]" && error!.length == 0 ?? false) {
        print("bot() : extractContentResults() : VALID ANSWER");
        var knowDBJson = jsonDecode(knownDB!);
        //Check if it is worth displaying data. If just one row is returned, no use.
        //if (true) {
        if ((knowDBJson!.length <= 1 && (knowDBJson![0] as Map).length <= 1) ||
            (knowDBJson![0] as Map).length > 2) {
          print(
              "bot() : extractContentResultsOpenDataQnA() : knowDBJson!.length <= 1 and MAP has at most 1 element");
          isText = true;
          //Get graph description in case we want to display a graph
          googleChartVizRes = await getDataVisualization(
              userQuestion!, knownDB!, generatedSQLText!);

          print(
              "bot() : extractContentResultsOpenDataQnA() : googleChartVizRes = ${googleChartVizRes}");
        } else {
          print(
              "bot() : extractContentResultsOpenDataQnA() : knowDBJson!.length > 1 or MAP has at least 1 element");
          isText = false;
          //Get graph description in case we want to display a graph
          googleChartVizRes = await getDataVisualization(
              userQuestion!, knownDB!, generatedSQLText!);

          print(
              "bot() : extractContentResultsOpenDataQnA() : googleChartVizRes = ${googleChartVizRes}");
        }

        print(
            "bot() : extractContentResultsOpenDataQnA() : isText = ${isText}; ");
        //get ML summarize
        //textSummary = await getTextSummary(userQuestion!, knownDB!);

        RespList.add(knownDB!);
        RespList.add(isText);
        RespList.add(googleChartVizRes!);
        RespList.add(naturalResponseText!.trim());
      } else {
        print("bot() : extractContentResultsOpenDataQnA() : UNVALID ANSWER");
        RespList.add("");
        RespList.add(true);
        RespList.add({"chart_div": "empty", "chart_div_1": "empty"});
        RespList.add(
            "The request did not return meaningful information. It could be because the question has not been formulated properly or some context is missing.");
      }
    } catch (e) {
      print("bot() : extractContentResultsOpenDataQnA() : EXCEPTION : $e");
    } finally {
      print("bot() : extractContentResultsOpenDataQnA() : FINALLY CLAUSE ");
      RespList.add(knownDB!);
      RespList.add(isText);
      RespList.add(googleChartVizRes!);
      RespList.add(naturalResponseText!);
      return RespList;
    }
  }

  Future<dynamic> getDataVisualization(
      String question, String tabularAnswer, String generatedSQLText) async {
    dynamic generatedChartjsMap;

    //Create the header
    Map<String, String>? _headers = {
      "Content-Type": "application/json",
    };

    String tmpReplace = tabularAnswer.replaceAll('"', '\\"');
    print('Bot : getDataVisualization() :  tnpReplace = ' + tmpReplace);

    //Create the body
    String _body = '''{
        "user_question": "$question",
        "sql_generated": "${generatedSQLText}",
        "sql_results": "${tmpReplace}",
        "session_id" : "${TextToDocParameter.sessionId}"
      }''';

    print('Bot : getDataVisualization() :  _body = ' + _body);

    try {
      var stopwatchGetDataVisulization = Stopwatch()..start();

      print('Bot: getDataVisualization() : BEFORE HttpRequest');
      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/generate_viz',
          method: "POST",
          sendData: _body);
      print('Bot: getDataVisualization() : AFTER HttpRequest');
      stopwatchGetDataVisulization.stop();

      print('Bot : getDataVisualization() : response = ' + response.toString());

      var jsonData = jsonDecode(response);

      if (jsonData != null) {
        print('Bot: getDataVisualization() : jsonData = $jsonData');

        generatedChartjsMap = jsonData["GeneratedChartjs"];

        print(
            'Bot: getDataVisualization() : generatedChartjsMap = $generatedChartjsMap');

        if(TextToDocParameter.anonymized_data) {
          //update generatedChartjsMap
          mapAnonymisationGraph.forEach((key, value) {
            print(
                'Bot : getDataVisualization() : update jsonData : key =  $key, value = $value');
            generatedChartjsMap['chart_div'] =
                generatedChartjsMap['chart_div'].replaceAll(key, value);
          });
        }

        //Update stepper state to get_graph_description
        BlocProvider.of<UpdateStepperCubit>(context)
            .updateStepperStatusUploaded(
                status: StepperStatus.get_graph_description,
                message: "Graph generated",
                stateStepper: StepState.complete,
                isActiveStepper: true,
                debugInfo: StepperExpertInfo(
                  uri:
                      "${TextToDocParameter.endpoint_opendataqnq}/generate_viz",
                  body: _body
                      .replaceAll("\"[", "[")
                      .replaceAll("]\"", "]")
                      .replaceAll("\\\"", "\""),
                  header:
                      '''{"Header not accessible": "CORS headers are not accessible as they are sent directly by the web browser"}''',
                  response: response
                      .replaceAll("\"[", "[")
                      .replaceAll("]\"", "]")
                      .replaceAll("\\\"", "\""),
                  statusCode: 0,
                  stepDuration:
                      stopwatchGetDataVisulization.elapsed.inMilliseconds,
                ));

        print(
            "Bot: getDataVisualization() : After BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded() : get Google Charts");
      } else {
        print('Bot: getDataVisualization() : jsonData is null');
      }
    } catch (e) {
      generatedChartjsMap = {"chart_div": "empty", "chart_div_1": "empty"};
      print('Bot: getDataVisualization() : EXCEPTION : error = $e');
    } finally {
      return generatedChartjsMap!;
    }
  }

  List<String> setBubbleColor(String text, {types.User? user}) {
    String tmp = "";
    String userType = "";
    const String datastoreGenerated = "ap :";
    const String nMatchLLMGenerated = "nh :";
    int startIndex = 0;
    List<String> rep = [];

    print('Bot : setBubbleColor() : text = ' + text);

    if (user != null) if (_user.id == user!.id) userType = "user";

    if (text.contains(datastoreGenerated)) {
      startIndex =
          text.indexOf(datastoreGenerated) + datastoreGenerated.length + 1;
      colorBubble = "datastoreData";
    } else if (text.contains(nMatchLLMGenerated)) {
      startIndex =
          text.indexOf(nMatchLLMGenerated) + datastoreGenerated.length + 1;
      colorBubble = "noMatchLLM";
    } else if (userType == "user") {
      colorBubble = "user";
    } else {
      colorBubble = "regularDF";
    }

    tmp = text.substring(startIndex);

    print('Bot : setBubbleColor() : startIndex = ' + startIndex.toString());
    print('Bot : setBubbleColor() : tmp = ' + tmp);
    print('Bot : setBubbleColor() : colorBubble = ' + colorBubble);

    rep.add(tmp);
    rep.add(colorBubble);
    return rep;
  }

  int countOccurences(String mainString, String search) {
    int lInx = 0;
    int count = 0;
    while (lInx != -1) {
      lInx = mainString.indexOf(search, lInx);
      if (lInx != -1) {
        count++;
        lInx += search.length;
      }
    }
    return count;
  }

  Future<void> _dialogExtension(BuildContext context, String extension) {
    return showDialog<void>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text("Format d'image non supporté",
              style: TextStyle(
                  fontWeight: FontWeight.normal,
                  fontSize: 22.0,
                  color: Colors.blue)),
          content: Text(
            "Le format d'image $extension n'est pas supporté.\n" +
                "Choisissez une image du type :\ngif, tiff, tif, jpg, jpeg, png, bmp, webp",
          ),
          actions: <Widget>[
            TextButton(
              style: TextButton.styleFrom(
                textStyle: Theme.of(context).textTheme.labelLarge,
              ),
              child: const Text('Ok'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }

  String displayDateTime() {
    String? dateTimeS;

    final now = DateTime.now();
    dateTimeS = DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
    return dateTimeS!;
  }

  List<types.Message> get messages {
    return _messages;
  }

  Map<String, Uint8List> get graphsImages {
    return _graphsImagesMap;
  }

  Map<String, PaginatedDataTable> get tableKeysMap {
    return tableKeyMap;
  }

  Widget avatarBuilder(types.User user) {
    bool isUserAvatar = user.id == '82091010-a484-4a89-ae75-a22bf8d6f3ab';

    return CircleAvatar(
      backgroundColor: Colors.green,
      backgroundImage:
          isUserAvatar ? NetworkImage(TextToDocParameter.picture) : null,
      radius: 16,
      child: !isUserAvatar
          ? Text(
              "TA",
            )
          : null,
    );
  }

  String anonymizedData(String responseRunQuery) {
    String anonymizedData = "";
    Random random = new Random();
    mapAnonymisationGraph.clear();

    print("Bot : anonymizedData() : START");
    print("Bot : anonymizedData() : responseRunQuery = ${responseRunQuery}");

    var responseRunQueryJson = jsonDecode(responseRunQuery);
    print(
        "Bot : anonymizedData() : responseRunQueryJson = ${responseRunQueryJson}");

    var knownDB = jsonDecode(responseRunQueryJson["KnownDB"]);
    String naturalResponse = responseRunQueryJson["NaturalResponse"];

    print("Bot : anonymizedData() : knownDB = ${knownDB}");
    print("Bot : anonymizedData() : naturalResponse = ${naturalResponse}");

    for (int i = 0; i < knownDB.length; i++) {
      var entry = knownDB[i];
      print("Bot : anonymizedData() : for :  i = $i : entry = ${entry}");

      entry.forEach((key, value) {
        print('Bot : anonymizedData() : key = $key : value =  $value');

        try {
          if (value is double) {
            print(
                'Bot : anonymizedData() : i = $i : value =  $value is of type double');
            double randomNumber = random.nextDouble() * value;
            int truncatedInt = (randomNumber * 100).toInt();
            randomNumber = truncatedInt / 100;
            print(
                'Bot : anonymizedData() : i = $i : randomNumber =  $randomNumber');
            entry[key] = randomNumber;

            NumberFormat formatter = NumberFormat("#,##0", "en_US"); // Adjust locale if needed
            String formattedNumber = formatter.format(value);

            mapAnonymisationGraph[formattedNumber] = formatter.format(randomNumber);//randomNumber.toString();
          }
          if (value is String) {
            print(
                'Bot : anonymizedData() : i = $i : value =  $value is of type String');

            String randomString = generateRandomString(value.toString().length);
            print(
                'Bot : anonymizedData() : i = $i : randomString =  $randomString');
            entry[key] = randomString;

            mapAnonymisationGraph[value.toString()] = randomString;
          }
        } catch (e) {
          print('Bot : anonymizedData() : PARSING EXCEPTION =  $e');
        }
      });
    }
    responseRunQueryJson["KnownDB"] = jsonEncode(knownDB);

    //update NaturalResponse
    mapAnonymisationGraph.forEach((key, value) {
      print(
          'Bot : anonymizedData() : update NaturalResponse : key =  $key, value = $value');
      naturalResponse = naturalResponse.replaceAll(key,value);
    });

    print("Bot : anonymizedData() : END : knownDB = ${knownDB}");
    print("Bot : anonymizedData() : END : naturalResponse = ${naturalResponse}");

    responseRunQueryJson["NaturalResponse"] = naturalResponse;

    print(
        "Bot : anonymizedData() : END : responseRunQueryJson = ${responseRunQueryJson}");
    return jsonEncode(responseRunQueryJson);
  }


  String generateRandomString(int length) {
    const _chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890';
    Random _rnd = Random();

    return String.fromCharCodes(Iterable.generate(
    length, (_) => _chars.codeUnitAt(_rnd.nextInt(_chars.length))));
  }


  Future<void> _updateUserGroupingInSessionLogs() async {
    int count = 0;
    print(
        "Bot: _updateUserGroupingInSessionLogs() : START");

    //get all the documents corresponding to the user_id of the current user
    try {
      var querySnapshot = await widget.db!
          .collection("${TextToDocParameter.firestore_history_collection}")
          .where("user_id", isEqualTo: TextToDocParameter.userID)
          .orderBy('timestamp', descending: true)
          .limit(1)
          .get();

      print(
          "Bot: _updateUserGroupingInSessionLogs() : Add user_grouping : querySnapshot.docs.length = ${querySnapshot.docs.length}");
      print(
          "Bot: _updateUserGroupingInSessionLogs() : Add user_grouping : querySnapshot = ${querySnapshot}");

      //update all these documents with the user_grouping scenario_name
      if(TextToDocParameter.currentScenarioName.isEmpty)
        TextToDocParameter.currentScenarioName = "Scenario";

      for (var docSnapshot in querySnapshot.docs) {
        print(
            'Bot: _updateUserGroupingInSessionLogs() : Add user_grouping : TextToDocParameter.currentUserGrouping = ${TextToDocParameter.currentUserGrouping}');
        print(
            'Bot: _updateUserGroupingInSessionLogs() : Add user_grouping : TextToDocParameter.currentScenarioName = ${TextToDocParameter.currentScenarioName}');

        print(
            'Bot: _updateUserGroupingInSessionLogs() : Add user_grouping : ${docSnapshot.id} => ${docSnapshot.data()}');
        widget.db!.collection("${TextToDocParameter.firestore_history_collection}").doc('${docSnapshot.id}').set(
            {"user_grouping": "${TextToDocParameter.currentUserGrouping}", "scenario_name": "${TextToDocParameter.currentScenarioName}"},
            SetOptions(merge: true));
        count++;
      }
    } catch (e) {
      print(
          'Bot: _updateUserGroupingInSessionLogs() : Add user_grouping : EXCEPTION : $e');
    }
    var snackBar = SnackBar(
      content:
      Text('Updated $count questions on ${TextToDocParameter.firestore_database_id} collection'),
      duration: Duration(seconds: 3),
    );
    ScaffoldMessenger.of(context).showSnackBar(snackBar);
  }

  PaginatedDataTable? createPaginatedTable(String data) {
    print("bot() : createPaginatedTable() : START");
    print("bot() : createPaginatedTable() : data = $data");
    List<DataColumn> dataColumnList = <DataColumn>[];

    List<dynamic> dataList = jsonDecode(data!);

    print("bot() : createPaginatedTable() : dataList = $dataList");
    print("bot() : createPaginatedTable() : dataList.length = ${dataList.length}");

    //get headers of columns
    var entry = dataList.first;
    print("bot() : createPaginatedTable() : entry = ${entry}");
    print("bot() : createPaginatedTable() : entry.length = ${entry.length}");
    print("bot() : createPaginatedTable() : entry['tconst'] = ${entry['tconst']}");
    print("bot() : createPaginatedTable() : entry['original_title'] = ${entry['original_title']}");
    print("bot() : createPaginatedTable() : entry['average_rating'] = ${entry['average_rating']}");
    print("bot() : createPaginatedTable() : entry['title_type'] = ${entry['title_type']}");

    for (var element in (entry as Map<String, dynamic>).entries) {
      print('bot() : createPaginatedTable() : Key: ${element.key}, Value: ${element.value}');
      dataColumnList.add(DataColumn(label: Text(element.key.toString(), style: TextStyle(fontWeight: FontWeight.bold, color : Colors.white))));
    }

    if (dataList.length != 0) {
      print("bot() : createPaginatedTable() : dataList.length != 0}");

        var rowsList = dataList.map((data) {
          List<DataCell> dataCellsList = <DataCell>[];

          for (var element in (data as Map<String, dynamic>).entries) {
            print('bot() : createPaginatedTable() : Key: ${element.key}, Value: ${element.value}');
            DataCell cell = DataCell(Text(element.value.toString()));
            dataCellsList.add(cell);
          }
          return DataRow(cells: dataCellsList);
        }).toList();

        return PaginatedDataTable(
          //header: Text('Results'),
          headingRowColor: WidgetStateProperty.all(Colors.blue),
          rowsPerPage: 3, // Customize as needed
          columns: dataColumnList,
          source: OpenDataQnASource(rowsList as List<DataRow>),
        );
    }
    else
      return null;
  }

}

class OpenDataQnASource extends DataTableSource {
  final List<DataRow> data;

  OpenDataQnASource(this.data);

  @override
  int get rowCount => data.length;

  @override
  DataRow? getRow(int index) {

    if (index < data.length) {
      return data[index];
    } else {
      return null;
    }
  }

  @override
  bool get isRowCountApproximate => false;

  @override
  int get selectedRowCount => 0;
}

