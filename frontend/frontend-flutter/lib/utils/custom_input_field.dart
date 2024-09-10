import 'dart:convert';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_chat_types/flutter_chat_types.dart' as types;
import 'package:flutter_chat_ui/src/models/input_clear_mode.dart';
import 'package:flutter_chat_ui/src/models/send_button_visibility_mode.dart';
import 'package:flutter_chat_ui/src/util.dart';
import 'package:flutter_chat_ui/src/widgets/state/inherited_chat_theme.dart';
import 'package:flutter_chat_ui/src/widgets/state/inherited_l10n.dart';
import 'package:flutter_chat_ui/src/widgets/input/attachment_button.dart';
import 'package:flutter_chat_ui/src/widgets/input/input_text_field_controller.dart';
import 'package:flutter_chat_ui/src/widgets/input/send_button.dart';
import 'package:flutter_typeahead/flutter_typeahead.dart';
import 'dart:html' as html;
import '../services/new_suggestions/new_suggestion_cubit.dart';
import '../services/new_suggestions/new_suggestion_state.dart';
import 'TextToDocParameter.dart';

/// A class that represents bottom bar widget with a text field, attachment and
/// send buttons inside. By default hides send button when text field is empty.
class CustomInputField extends StatefulWidget {
  /// Creates [Input] widget.
  const CustomInputField({
    super.key,
    this.isAttachmentUploading,
    this.onAttachmentPressed,
    required this.onSendPressed,
    this.db,
    this.options = const InputOptions(),
  });

  /// Whether attachment is uploading. Will replace attachment button with a
  /// [CircularProgressIndicator]. Since we don't have libraries for
  /// managing media in dependencies we have no way of knowing if
  /// something is uploading so you need to set this manually.
  final bool? isAttachmentUploading;
  final FirebaseFirestore? db;

  /// See [AttachmentButton.onPressed].
  final VoidCallback? onAttachmentPressed;

  /// Will be called on [SendButton] tap. Has [types.PartialText] which can
  /// be transformed to [types.TextMessage] and added to the messages list.
  final void Function(types.PartialText) onSendPressed;

  /// Customisation options for the [Input].
  final InputOptions options;

  @override
  State<CustomInputField> createState() => _InputState();
}

/// [Input] widget state.
class _InputState extends State<CustomInputField> {
  List<Suggestion> suggestionsList = [];
  late final _inputFocusNode = FocusNode(
    onKeyEvent: (node, event) {
      if (event.physicalKey == PhysicalKeyboardKey.enter &&
          !HardwareKeyboard.instance.physicalKeysPressed.any(
            (el) => <PhysicalKeyboardKey>{
              PhysicalKeyboardKey.shiftLeft,
              PhysicalKeyboardKey.shiftRight,
            }.contains(el),
          )) {
        if (kIsWeb && _textController.value.isComposingRangeValid) {
          return KeyEventResult.ignored;
        }
        if (event is KeyDownEvent) {
          _handleSendPressed();
        }
        return KeyEventResult.handled;
      } else {
        return KeyEventResult.ignored;
      }
    },
  );

  bool _sendButtonVisible = false;
  late TextEditingController _textController;

  @override
  void initState() {
    super.initState();

    _textController =
        widget.options.textEditingController ?? InputTextFieldController();
    _handleSendButtonVisibilityModeChange();
  }

  void _handleSendButtonVisibilityModeChange() {
    _textController.removeListener(_handleTextControllerChange);
    if (widget.options.sendButtonVisibilityMode ==
        SendButtonVisibilityMode.hidden) {
      _sendButtonVisible = false;
    } else if (widget.options.sendButtonVisibilityMode ==
        SendButtonVisibilityMode.editing) {
      _sendButtonVisible = _textController.text.trim() != '';
      _textController.addListener(_handleTextControllerChange);
    } else {
      _sendButtonVisible = true;
    }
  }

  void _handleSendPressed() {
    print(
        "CustomInputField: build() : _inputBuilder() : TypeAheadField : _handleSendPressed()");
    final trimmedText = _textController.text.trim();
    if (trimmedText != '') {
      final partialText = types.PartialText(text: trimmedText);
      widget.onSendPressed(partialText);

      if (widget.options.inputClearMode == InputClearMode.always) {
        _textController.clear();
      }
    }
  }

  void _handleTextControllerChange() {
    if (_textController.value.isComposingRangeValid) {
      return;
    }
    setState(() {
      _sendButtonVisible = _textController.text.trim() != '';
    });
  }

  Widget _inputBuilder() {
    final query = MediaQuery.of(context);
    final buttonPadding = InheritedChatTheme.of(context)
        .theme
        .inputPadding
        .copyWith(left: 16, right: 16);
    final safeAreaInsets = isMobile
        ? EdgeInsets.fromLTRB(
            query.padding.left,
            0,
            query.padding.right,
            query.viewInsets.bottom + query.padding.bottom,
          )
        : EdgeInsets.zero;
    final textPadding = InheritedChatTheme.of(context)
        .theme
        .inputPadding
        .copyWith(left: 0, right: 0)
        .add(
          EdgeInsets.fromLTRB(
            widget.onAttachmentPressed != null ? 0 : 24,
            0,
            _sendButtonVisible ? 0 : 24,
            0,
          ),
        );

    return Focus(
      autofocus: !widget.options.autofocus,
      child: Padding(
        padding: InheritedChatTheme.of(context).theme.inputMargin,
        child: Material(
          borderRadius: InheritedChatTheme.of(context).theme.inputBorderRadius,
          color: InheritedChatTheme.of(context).theme.inputBackgroundColor,
          surfaceTintColor:
              InheritedChatTheme.of(context).theme.inputSurfaceTintColor,
          elevation: InheritedChatTheme.of(context).theme.inputElevation,
          child: Container(
            decoration: BoxDecoration(
              color: Color(0xFFF0F2F6), // Background color
            ),
            //InheritedChatTheme.of(context).theme.inputContainerDecoration,
            padding: safeAreaInsets,
            child: Row(
              textDirection: TextDirection.ltr,
              children: [
                /*if (widget.onAttachmentPressed != null)
                  AttachmentButton(
                    isLoading: widget.isAttachmentUploading ?? false,
                    onPressed: widget.onAttachmentPressed,
                    padding: buttonPadding,
                  ),*/
                Container(width: 30),
                Expanded(
                  child: Padding(
                      padding: textPadding,
                      child: FutureBuilder(
                        future: getAllquestions(),
                        builder: (context, snapshot) {
                          if(snapshot.hasData) {
                            suggestionsList = snapshot.data!;
                            print(
                                "CustomInputField: build() : _inputBuilder() : suggestionList.length = ${suggestionsList.length}");
                          }
                          return TypeAheadField<Suggestion>(
                            hideOnEmpty: true,
                            controller: _textController,
                            direction: VerticalDirection.up,
                            loadingBuilder: (context) =>
                                const Text('Loading...'),
                            onSelected: (entry) {

                              _textController.text = entry.suggestion!;
                              entry.scenarioNumber;
                              BlocProvider.of<NewSuggestionCubit>(context)
                                  .generateNewSuggestions(
                                      entry.scenarioNumber!, entry.suggestion!,
                                      isACannedQuestion: false,
                                userGrouping: entry.userGrouping
                              );
                            },
                            itemBuilder: (context, entry) {
                              print(
                                  "CustomInputField: build() : TypeAheadField : _inputBuilder():  itemBuilder: entry = $entry");
                              return ListTile(
                                title: Text(entry.suggestion!),
                              );
                            },
                            suggestionsCallback:
                                _textController.text.length <= 1
                                    ? suggestionsEmptyCallback
                                    : suggestionsCallback,
                            builder:
                                (context, _textController, inputFocusNode) {
                              print(
                                  "CustomInputField: build() : TypeAheadField : _inputBuilder():  builder: focusNode = $inputFocusNode");
                              return TextField(
                                enabled: widget.options.enabled,
                                autocorrect: widget.options.autocorrect,
                                autofocus: widget.options.autofocus,
                                enableSuggestions:
                                    widget.options.enableSuggestions,
                                controller: _textController,
                                cursorColor: InheritedChatTheme.of(context)
                                    .theme
                                    .inputTextCursorColor,
                                decoration: InputDecoration(
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(
                                        50.0), // Adjust the radius as needed
                                  ),
                                  //labelText: 'Password',
                                  filled: true,
                                  fillColor: Colors.white,
                                  suffixIcon: Visibility(
                                    visible: _sendButtonVisible,
                                    child: IconButton(
                                      onPressed: () {
                                        print(
                                            "CustomInputField: build() : _inputBuilder() : TypeAheadField : IconButton : onPressed: ()");
                                        _handleSendPressed();
                                      },
                                      icon: Icon(Icons.send),
                                    ),
                                  ),
                                ),
                                focusNode: inputFocusNode,
                                keyboardType: widget.options.keyboardType,
                                maxLines: 5,
                                minLines: 1,
                                onChanged: widget.options.onTextChanged,
                                onTap: widget.options.onTextFieldTap,
                                style: TextStyle(color: Colors.black),
                                textCapitalization:
                                    TextCapitalization.sentences,
                              );
                            },
                          );
                        },
                      )),
                ),
                Container(width: 30),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> loadCfgFromFirestore() async {
    /*db = await FirebaseFirestore.instanceFor(
        app: app, databaseId: 'opendataqna-session-logs');*/

    print("CustomInputField: loadCfgFromFirestore() : db = $widget.db");

    if (TextToDocParameter.userID.isEmpty) {
      print(
          "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.userID is empty = ${TextToDocParameter.userID}");
      return;
    }

    try {
      print(
          "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.userID = ${TextToDocParameter.userID}");

      DocumentSnapshot doc = await widget.db!
          .collection("front_end_flutter_cfg")
          .doc('${TextToDocParameter.userID}')
          .get();

      if (doc != null) {
        final data = doc.data() as Map<String, dynamic>;

        TextToDocParameter.anonymized_data = data["anonymized_data"];
        TextToDocParameter.expert_mode = data["expert_mode"];
        TextToDocParameter.endpoint_opendataqnq = data["endpoint_opendataqnq"];
        TextToDocParameter.firestore_database_id =
        data["firestore_database_id"];
        TextToDocParameter.firebase_app_name = data["firebase_app_name"];
        TextToDocParameter.firestore_history_collection =
        data["firestore_history_collection"];
        TextToDocParameter.firestore_cfg_collection =
        data["firestore_cfg_collection"];
        TextToDocParameter.imported_questions = data["imported_questions"];

        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.anonymized_data = ${TextToDocParameter.anonymized_data}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.expert_mode = ${TextToDocParameter.expert_mode}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.firestore_database_id = ${TextToDocParameter.firestore_database_id}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.endpoint_opendataqnq = ${TextToDocParameter.endpoint_opendataqnq}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.firebase_app_name = ${TextToDocParameter.firebase_app_name}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.firestore_history_collection = ${TextToDocParameter.firestore_history_collection}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.firestore_cfg_collection = ${TextToDocParameter.firestore_cfg_collection}");
        print(
            "CustomInputField: loadCfgFromFirestore() : TextToDocParameter.imported_questions = ${TextToDocParameter.imported_questions}");

      } else {
        print("CustomInputField: loadCfgFromFirestore() : doc == null");
      }
    } catch (e) {
      print("CustomInputField: loadCfgFromFirestore() : EXCEPTION ON FIRESTORE : e = $e");
      //https://www.acodeblog.com/post/2022/5/29/flutter-showdialog-without-context-using-the-navigatorkey
    }
  }

  Future<List<Suggestion>> getAllquestions() async {
    List<Suggestion> resp = [];
    List <String> userGroupingList  = [];

    print('CustomInputField: getAllquestions() : START');

    await loadCfgFromFirestore();
    userGroupingList = await _getUserGrouping();
    print('CustomInputField: getAllquestions() : userGroupingList = ${userGroupingList}');

    for (String userGrouping in userGroupingList) {
      var list = await getAllquestionsFromUserGroup(userGrouping);
      resp.addAll((list as List<String>)
          .map((question) =>
          Suggestion(
              suggestion: question, userGrouping: userGrouping!))
          .toList());

      print('CustomInputField: getAllquestions() : userGrouping = $userGrouping : resp.length = ${resp.length}');
    }

    print('CustomInputField: getAllquestions() : END : resp.length = ${resp.length}');
    return resp;
  }

  Future<List<String>> getAllquestionsFromUserGroup(String userGrouping) async {
    List<String> resp = [];
    String body = "";

    print('CustomInputField : getAllquestionsFromUserGroup()  : START');

    //Create the header
    Map<String, String>? _headers = {
      "Content-Type": "application/json",
      //"Authorization": " Bearer ${client!.credentials.accessToken.toString()}",
    };

    //Create the body
    body = '''{
          "user_grouping": "$userGrouping"
      }''';

    print('CustomInputField : getAllquestionsFromUserGroup() : body = ' + body);

    try {
      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/get_known_sql',
          method: "POST",
          sendData: body);

      print('CustomInputField : getAllquestionsFromUserGroup() : response = ' +
          response.toString());

      final jsonData = jsonDecode(response);

      if (jsonData != null) {
        print('CustomInputField: getAllquestionsFromUserGroup() : jsonData = $jsonData');

        //KnownSQL = [{"example_user_question": "question1", "example_generated_sql": "sql1"},
        // {"example_user_question": "question2", "example_generated_sql": "sql2"},
        // ...]

        var knownSql =
        jsonData["KnownSQL"].replaceAll(RegExp(r'((\\n)|(\\r))'), '');

        print('CustomInputField: getAllquestionsFromUserGroup() : knownSql = $knownSql');

        var knownSqlMap = jsonDecode(knownSql);

        for (int i = 0; i < knownSqlMap.length; i++) {
          for (var entry in knownSqlMap[i].entries) {
            print('${entry.key} : ${entry.value}');
            if (entry.key == "example_user_question") resp.add(entry.value);
          }
        }
      }
    } catch (e) {
      print('CustomInputField: getAllquestionsFromUserGroup() : EXCEPTION = $e');
      throw Exception('Failed to get questions: $e');
    } finally {
      print('CustomInputField: getAllquestionsFromUserGroup() : END : resp = ${resp}');
      return resp;
    }
  }

  Future<List<String>> _getUserGrouping() async {
    print('CustomInputField : _getUserGrouping() : START');
    List<String> resp = [];


    Map<String, String>? _headers = {
      "Content-Type": "application/json",
      //"Authorization": " Bearer ${client!.credentials.accessToken.toString()}",
    };

    try {
      print(
          'CustomInputField : _getUserGrouping() : url = ${TextToDocParameter.endpoint_opendataqnq}/available_databases');

      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/available_databases',
          method: "GET");

      print('CustomInputField : _getUserGrouping() : response = ' + response.toString());

      final jsonData = jsonDecode(response);

      if (jsonData != null) {
        print('CustomInputField : _getUserGrouping() : jsonData = $jsonData');

        /* Expected response :
        {
          "Error": "",
          "KnownDB": "[{\"table_schema\":\"imdb-postgres\"},{\"table_schema\":\"retail-postgres\"}]",
          "ResponseCode": 200
        }*/

        var knownSqlMap = jsonDecode(jsonData['KnownDB']);

        print('CustomInputField : _getUserGrouping() : knownSqlMap = ${knownSqlMap}');

        print(
            'CustomInputField : _getUserGrouping() : knownSqlMap[0] = ${knownSqlMap[0].toString()}');

        for (int i = 0; i < knownSqlMap.length; i++) {
          for (var entry in knownSqlMap[i].entries) {
            print('${entry.key} : ${entry.value}');
            if (entry.key == "table_schema") resp.add(entry.value);
          }
        }
      } else {
        resp.add("");
      }

    } catch (e) {
      print('CustomInputField : _getUserGrouping() : EXCEPTION = $e');
      throw Exception('Failed to get earning calls question suggestions: $e');
    } finally {
      print('CustomInputField : _getUserGrouping() : resp = $resp');
      return resp;
    }
  }

  @override
  void didUpdateWidget(covariant CustomInputField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.options.sendButtonVisibilityMode !=
        oldWidget.options.sendButtonVisibilityMode) {
      _handleSendButtonVisibilityModeChange();
    }
  }

  @override
  void dispose() {
    _inputFocusNode.dispose();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    print("CustomInputField: build():  START");
    return GestureDetector(
      onTap: () => _inputFocusNode.requestFocus(),
      child: _inputBuilder(),
    );
  }

  Future<List<Suggestion>> suggestionsCallback(String pattern) async =>
      Future<List<Suggestion>>.delayed(
        Duration(milliseconds: 300),
        () => suggestionsList.where((entry) {
          final nameLower = entry.suggestion!.toLowerCase();
          final patternLower = pattern.toLowerCase();//pattern.toLowerCase().split(' ').join('');
          return nameLower.contains(patternLower);
        }).toList(),
      );

  Future<List<Suggestion>> suggestionsEmptyCallback(String pattern) async =>
      Future<List<Suggestion>>.delayed(Duration(milliseconds: 300), () {
        return [];
        /*return [
          Suggestion(
              suggestion: "looking for suggestions ...", scenarioNumber: 0)
        ].where((entry) {
          final nameLower = entry.suggestion!.toLowerCase();
          final patternLower = pattern.toLowerCase().split(' ').join('');
          return nameLower.contains(patternLower);
        }).toList()*/
        ;
      });
}

@immutable
class InputOptions {
  const InputOptions({
    this.inputClearMode = InputClearMode.always,
    this.keyboardType = TextInputType.multiline,
    this.onTextChanged,
    this.onTextFieldTap,
    this.sendButtonVisibilityMode = SendButtonVisibilityMode.editing,
    this.textEditingController,
    this.autocorrect = true,
    this.autofocus = false,
    this.enableSuggestions = true,
    this.enabled = true,
  });

  /// Controls the [Input] clear behavior. Defaults to [InputClearMode.always].
  final InputClearMode inputClearMode;

  /// Controls the [Input] keyboard type. Defaults to [TextInputType.multiline].
  final TextInputType keyboardType;

  /// Will be called whenever the text inside [TextField] changes.
  final void Function(String)? onTextChanged;

  /// Will be called on [TextField] tap.
  final VoidCallback? onTextFieldTap;

  /// Controls the visibility behavior of the [SendButton] based on the
  /// [TextField] state inside the [Input] widget.
  /// Defaults to [SendButtonVisibilityMode.editing].
  final SendButtonVisibilityMode sendButtonVisibilityMode;

  /// Custom [TextEditingController]. If not provided, defaults to the
  /// [InputTextFieldController], which extends [TextEditingController] and has
  /// additional fatures like markdown support. If you want to keep additional
  /// features but still need some methods from the default [TextEditingController],
  /// you can create your own [InputTextFieldController] (imported from this lib)
  /// and pass it here.
  final TextEditingController? textEditingController;

  /// Controls the [TextInput] autocorrect behavior. Defaults to [true].
  final bool autocorrect;

  /// Whether [TextInput] should have focus. Defaults to [false].
  final bool autofocus;

  /// Controls the [TextInput] enableSuggestions behavior. Defaults to [true].
  final bool enableSuggestions;

  /// Controls the [TextInput] enabled behavior. Defaults to [true].
  final bool enabled;
}

class Suggestion {
  final String suggestion;
  final String userGrouping;
  final int? scenarioNumber;

  Suggestion({
    required this.suggestion,
    required this.userGrouping,
    this.scenarioNumber = 0,
  });
}
