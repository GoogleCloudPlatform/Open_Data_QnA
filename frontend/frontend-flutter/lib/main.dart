import 'dart:ui' as ui;
import 'package:file_picker/file_picker.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:simple_gradient_text/simple_gradient_text.dart';
import 'package:ttmd/screens/bot.dart';
import 'package:ttmd/screens/disclaimer.dart';
import 'package:ttmd/screens/settings.dart' as ts;
import 'package:ttmd/services/display_stepper/display_stepper_cubit.dart';
import 'package:ttmd/services/display_stepper/display_stepper_state.dart';
import 'package:ttmd/services/first_question/first_question_cubit.dart';
import 'package:ttmd/services/first_question/first_question_state.dart';
import 'package:ttmd/services/load_question/load_question_cubit.dart';
import 'dart:async';
import 'dart:convert';
import 'package:easy_sidemenu/easy_sidemenu.dart';
import 'package:expandable_tree_menu/expandable_tree_menu.dart';
import 'package:ttmd/services/load_question/load_question_state.dart';
import 'package:intl/intl.dart';
import 'package:badges/badges.dart' as badges;
import 'package:ttmd/services/new_suggestions/new_suggestion_cubit.dart';
import 'package:ttmd/services/new_suggestions/new_suggestion_state.dart';
import 'package:ttmd/services/update_expert_mode/update_expert_mode_cubit.dart';
import 'package:ttmd/services/update_popular_questions/update_popular_questions_cubit.dart';
import 'package:ttmd/services/update_popular_questions/update_popular_questions_state.dart';
import 'package:ttmd/services/update_stepper/update_stepper_cubit.dart';
import 'package:ttmd/services/update_stepper/update_stepper_state.dart';
import 'package:ttmd/utils/TextToDocParameter.dart';
import 'package:ttmd/utils/most_popular_questions.dart';
import 'package:ttmd/utils/pdf_viewer.dart';
import 'package:ttmd/utils/stepper_expert_info.dart';
import 'package:expansion_tile_card/expansion_tile_card.dart';
import 'package:flutter/services.dart';
import 'package:flutter_json_viewer/flutter_json_viewer.dart';
import 'dart:html' as html;
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:csv/csv.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/rendering.dart';

late final FirebaseApp app;
late final FirebaseAuth auth;
late User currentUser;
late String LastName;
late String userID;
late FirebaseFirestore db;
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

Map<String, Widget Function(BuildContext)> myRoutes = {
  '/landingPage': (context) => ContentTtmd(title: 'Open data QnA'),
  //'/pdfViewer': (context) => PdfViewer(),
  '/settings': (context) => ts.Settings(db),
};

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  /*app = await Firebase.initializeApp(
    name: 'opendataqna',
    options: DefaultFirebaseOptions.web, // currentPlatform,
  );*/
  app = await Firebase.initializeApp(options: DefaultFirebaseOptions.web);

  auth = FirebaseAuth.instanceFor(app: app);

  /*db = await FirebaseFirestore.instanceFor(
      app: app, databaseId: 'opendataqna-session-logs');*/
  db = await FirebaseFirestore.instanceFor(app: app);


  print('Main: main() : auth = $auth');
  print('Main: main() : db = $db');
  print('Main: main() : db.databaseId = ${db.databaseId}');

  //FirebaseAuth.instance
  auth.authStateChanges().listen((User? user) {
    if (user != null) {
      print("Main : user.uid = ${user.uid}");
      currentUser = user;
    }
  });

  runApp(ttmd());
}

class ttmd extends StatelessWidget {
  ttmd({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (context) => LoadQuestionCubit(),
        ),
        BlocProvider(
          create: (context) => FirstQuestionCubit(),
        ),
        BlocProvider(
          create: (context) => UpdatePopularQuestionsCubit(),
        ),
        BlocProvider(
          create: (context) => UpdateStepperCubit(),
        ),
        BlocProvider(
          create: (context) => NewSuggestionCubit(),
        ),
        BlocProvider(
          create: (context) => DisplayStepperCubit(),
        ),
        BlocProvider(
          create: (context) => UpdateExpertModeCubit(),
        ),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        //navigatorKey: navigatorKey,
        title: 'Open data QnA',
        theme: ThemeData(
            appBarTheme: AppBarTheme(
              backgroundColor: Colors.white,
            ),
            checkboxTheme: CheckboxThemeData(
                fillColor: WidgetStateProperty.resolveWith((states) {
              if (!states.contains(WidgetState.selected)) {
                return Colors.white;
              }
              return Colors.green;
            }), checkColor: WidgetStateProperty.resolveWith((states) {
              if (states.contains(WidgetState.selected)) {
                return Colors.red;
              }
              return null;
            }))),
        onGenerateRoute: (settings) {
          print('Main: ttmd : build() : onGenerateRoute : START');
          if (settings.name == '/landingPage' &&
              !TextToDocParameter.isAuthenticated) {
            print(
                'Main: ttmd : build() : onGenerateRoute : attempting to access /landingPage without authentication');
            return MaterialPageRoute(
              //builder: (context) => LoginScreen(),
              builder: (context) => Disclaimer(auth),
            );
          } else if (settings.name == '/pdfViewer' &&
              !TextToDocParameter.isAuthenticated) {
            print(
                'Main: ttmd : build() : onGenerateRoute : attempting to access /pdfViewer without authentication');
            return MaterialPageRoute(
              //builder: (context) => LoginScreen(),
              builder: (context) => Disclaimer(auth),
            );
          } else if (settings.name == '/settings' &&
              !TextToDocParameter.isAuthenticated) {
            print(
                'Main: ttmd : build() : onGenerateRoute : attempting to access /settings without authentication');
            return MaterialPageRoute(
              //builder: (context) => LoginScreen(),
              builder: (context) => Disclaimer(auth),
            );
          } else {
            print(
                'Main: ttmd : build() : onGenerateRoute : attempting to access ${settings.name!} with proper authentication');
            if (settings.name == '/pdfViewer') {
              final args = settings.arguments as Map;

              return MaterialPageRoute(
                builder: (context) {
                  return PdfViewer(bytes: args["bytes"]);
                },
              );
            } else {
              return MaterialPageRoute(
                builder: myRoutes[settings.name!]!,
              );
            }
          } // Let the default routing handle other routes
        },
        initialRoute: '/',
        home: Disclaimer(auth),
      ),
    );
  }
}

class ContentTtmd extends StatefulWidget {
  const ContentTtmd({super.key, required this.title});

  final String title;

  @override
  State<ContentTtmd> createState() => _ContentTtmdState();
}

class _ContentTtmdState extends State<ContentTtmd> {
  late GlobalKey<BotState> _botKey;
  int _selectedIndex = 0;
  int _selectedIndexNavRail = 0;
  PageController pageController = PageController();
  SideMenuController sideMenu = SideMenuController();
  SideMenuExpansionItem? historySideMenuExpansionItem;
  List<SideMenuItem>? childrenHistorySideMenuItem;
  Map<String, MostPopularQ>? mostPopularQuestionsMap = {};
  int currentStep = 0;
  List<StepperExpertInfo> stepperExpertInfoList = <StepperExpertInfo>[];
  bool isFirstQuestionStatus = true;
  List<TreeNode<dynamic>> nodes = [];
  final List<String> _destinations = [
    'New Chat',
    'History',
    'Most popular questions',
    'Summary Extract',
    //'Help',
    'Settings'
  ];
  bool _isExpanded = false;
  bool _isQuestionExpanded = false;
  Size? screenSize;
  bool _isFirstQuestionNotAskedYet = true;
  TextEditingController textEditingController = TextEditingController();
  Bot? bot;
  double overallProcessingTime = 0;
  bool useExpertMode = false;
  bool isTextToDoC = false;
  bool isTextToDoC1 = false;
  bool light = true;
  Container? suggestionContainer;
  List<TreeNode<String>> importedQuestionTreeNodeList = [
    TreeNode("No questions available")
  ];
  InAppWebViewController? webViewController;
  //late FirebaseFirestore db;
  List<String> userGroupingList = <String>[];
  String selectedValue = "";
  final ValueNotifier<bool> updateSelection = ValueNotifier(false);
  final ValueNotifier<bool> importedQuestionNotifier = ValueNotifier(false);
  final ValueNotifier<String?> selectedValueNotifier =
      ValueNotifier<String?>(null);
  //final TextEditingController _dropdownController = TextEditingController();

  List<TreeNode<String>> CreateNodesMostPopularQuestion(
      List<MostPopularQ> mostPopularQuestionsList) {
    List<TreeNode<String>> nodes = [];

    for (int i = 0; i < mostPopularQuestionsList.length; i++) {
      if (mostPopularQuestionsList[i].question.length != 0)
        nodes.add(TreeNode<String>(mostPopularQuestionsList[i].time +
            "|||" +
            mostPopularQuestionsList[i].question +
            "|||" +
            mostPopularQuestionsList[i].count.toString()));
    }

    return nodes;
  }

  void _addData(String data, bool isHistory) {
    List<MostPopularQ>? mostPopularQuestionsList = <MostPopularQ>[];
    int lenghtTmp = 0;
    String timeString = "";

    timeString = displayDateTime();

    if (data.length == 0) return;
    print("Main: _addData : BEFORE ADD : nodes.length = ${nodes.length}");
    print("Main: _addData : BEFORE ADD : data = ${data}");
    print("Main: _addData : BEFORE ADD : nodes = ${nodes}");
    if (isHistory)
      nodes.add(TreeNode(timeString + "|||" + data)); //displayDateTime()
    else
      nodes.add(TreeNode(data));

    //add questions to mostPopularQuestionsMap
    if (mostPopularQuestionsMap!.containsKey(data)) {
      print('Main: _addData : mostPopularQuestionsMap contains $data');
      print(
          'Main: _addData : mostPopularQuestionsMap : BEFORE INCREMENT : (mostPopularQuestionsMap![data] as MostPopularQ).count =  ${(mostPopularQuestionsMap![data] as MostPopularQ).count}');
      mostPopularQuestionsMap![data]!.count =
          mostPopularQuestionsMap![data]!.count + 1;
      mostPopularQuestionsMap![data]!.time = timeString;
      print(
          'Main: _addData : mostPopularQuestionsMap : AFTER INCREMENT : (mostPopularQuestionsMap![data] as MostPopularQ).count =  ${(mostPopularQuestionsMap![data] as MostPopularQ).count}');
    } else {
      print('Main: _addData : mostPopularQuestionsMap does not contain $data');
      mostPopularQuestionsMap![data] = MostPopularQ(data, 1, timeString);
    }

    var sortedByValueMap = Map.fromEntries(
        mostPopularQuestionsMap!.entries.toList()
          ..sort((e1, e2) => e2.value.count.compareTo(e1.value.count)));

    print(
        'Main: _addData : sortedByValueMap.length = ${sortedByValueMap.length}');
    print('Main: _addData : sortedByValueMap = $sortedByValueMap');

    int countEntries = 0;

    for (var entry in sortedByValueMap.entries) {
      mostPopularQuestionsList!.add(entry.value);
      if (countEntries == 2 || countEntries == sortedByValueMap.length - 1)
        break;
      countEntries++;
    }

    //countEntries = 0;

    print(
        "Main: _addData : BEFORE FILLING : mostPopularQuestionsList.length = ${mostPopularQuestionsList.length}");
    print(
        "Main: _addData : BEFORE FILLING : mostPopularQuestionsList = ${mostPopularQuestionsList}");

    lenghtTmp = mostPopularQuestionsList.length;

    //Fill mostPopularQuestionsList with dummy entries if there are not 3 most popular questions
    for (int i = 0; i <= (2 - lenghtTmp); i++) {
      mostPopularQuestionsList!.add(MostPopularQ("", 0, ""));
    }

    print(
        "Main: _addData : AFTER FILLING : mostPopularQuestionsList.length = ${mostPopularQuestionsList.length}");
    print(
        "Main: _addData : AFTER FILLING : mostPopularQuestionsList = ${mostPopularQuestionsList}");

    //Update the 3 most popular questions
    BlocProvider.of<UpdatePopularQuestionsCubit>(context)
        .updateMostPopularQuestions(
            mostPopularQuestionsList: mostPopularQuestionsList!,
            time: timeString);

    print("Main: _addData :  AFTER  : nodes.length = ${nodes.length}");
    print("Main: _addData :  AFTER  : nodes = ${nodes}");
  }

  void _nodeSelected(context, nodeValue) {
    int scenarioNumber = 0;
    String questionTmp = "";
    print('Main : _nodeSelected() : START');
    print(
        'Main : _nodeSelected() : nodeValue.toString() = ${nodeValue.toString()}');

    questionTmp = nodeValue.toString().split(":")[0];
    print('Main : _nodeSelected() : questionTmp = $questionTmp');

    if (questionTmp.length <= 2) {
      //we don't expect to have more than 99 questions, so 2 digits are enough
      scenarioNumber = int.parse(questionTmp);
      print(
          'Main : _nodeSelected() : questionTmp.length <=2 : scenarioNumber = $scenarioNumber');
    }

    if (nodeValue.toString().contains(":")) {
      print('Main : _nodeSelected() : nodeValue.toString().contains(":")');

      //scenario#:question:genre:user_grouping  in the future, may add a 5th element : main_question

      print(
          'Main : _nodeSelected() : nodeValue.toString().contains(":") : nodeValue.toString().split(":")[2] = ${nodeValue.toString().split(":")[2]}');

      textEditingController.text = nodeValue.toString().split(":")[1];
      BlocProvider.of<NewSuggestionCubit>(context).generateNewSuggestions(
          int.parse(nodeValue.toString().split(":")[0]),
          textEditingController.text,
          isACannedQuestion: false,
          userGrouping: nodeValue.toString().split(":")[3]);
      print(
          "Main: _nodeSelected() : textEditingController.text = = ${textEditingController.text}");

      //setting on the UI the current user_grouping based on the question clicked assuming next question is for the same user_grouping
      selectedValueNotifier.value = nodeValue.toString().split(":")[3];
      TextToDocParameter.currentUserGrouping =
          nodeValue.toString().split(":")[3];
      TextToDocParameter.currentScenarioName =
          nodeValue.toString().split(":")[2];
    } else
      return; //textEditingController.text = nodeValue.toString();
  }

  void _nodeSelected1(context, nodeValue) {
    var val = nodeValue.toString().split("|||");
    textEditingController.text = val[1];
    /*final route =
    MaterialPageRoute(builder: (context) => DetailPage(value: nodeValue));
    Navigator.of(context).push(route);*/
  }

  /// Build the Node widget at a specific node in the tree
  Widget _nodeBuilder(context, nodeValue) {
    return Card(
        margin: EdgeInsets.symmetric(vertical: 1),
        child: Padding(
          padding: const EdgeInsets.all(8.0),
          child: Text(nodeValue.toString()),
        ));
  }

  Widget _nodeBuilder2(context, nodeValue) {
    String? badgeCount;
    String scenarioTitle = "";
    String question = "";
    List<String> tmpList = [];

    print("Main : _nodeBuilder2() : START");
    print("Main : _nodeBuilder2() : nodeValue = $nodeValue");

    if (nodeValue.toString().contains(":")) {
      //question#: question
      tmpList = nodeValue.toString().split(":");
      scenarioTitle = tmpList[2]; //"Scenario " + tmpList[0];
      question = tmpList[1];
    } else if (nodeValue.toString().contains(" - ")) {
      //Scenario x - user_grouping -#of questions
      tmpList = nodeValue.toString().split(" - ");
      badgeCount = tmpList[2];
      question = tmpList[0] + ' - ' + tmpList[1];
    }

    bool isScenario = nodeValue.toString().contains("Scenario");

    print("Main : _nodeBuilder2() : scenarioTitle = $scenarioTitle");
    print("Main : _nodeBuilder2() : question = $question");

    return Card(
        margin: EdgeInsets.symmetric(vertical: 1),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            ListTile(
              leading: Padding(
                padding: const EdgeInsets.only(right: 9.0),
                child: !isScenario
                    ? CircleAvatar(
                        backgroundColor: Colors.green,
                        radius: 12,
                        child: Text("Q${TextToDocParameter.questionCount++}",
                            style: TextStyle(color: Colors.white, fontSize: 9)))
                    : badges.Badge(
                        badgeContent: Text(badgeCount!),
                        child: Icon(Icons.account_tree_sharp),
                      ),
              ),
              title: !isScenario
                  ? Text(scenarioTitle,
                      style: TextStyle(fontSize: 9, color: Colors.indigoAccent))
                  : null,
              subtitle: !isScenario
                  ? Text(question)
                  : Text("  " + question,
                      style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ));
  }

  Widget _nodeBuilder1(context, nodeValue) {
    var val = nodeValue.toString().split("|||");
    return Card(
        margin: EdgeInsets.symmetric(vertical: 1),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            ListTile(
              leading: Padding(
                padding: const EdgeInsets.only(right: 10.0),
                child: CircleAvatar(
                    backgroundColor: Colors.green,
                    radius: 12,
                    child: Icon(Icons.question_mark,
                        size: 10, color: Colors.white)),
              ),
              title: Text(val[0],
                  style: TextStyle(fontSize: 8, color: Colors.indigoAccent)),
              subtitle: Text(val[1]),
            ),
          ],
        ));
  }

  Widget _nodeBuilder3(context, nodeValue) {
    var val = nodeValue.toString().split("|||");
    //val[0]  => timestamp
    //val[1]  => question
    //val[2]  => Count

    return Card(
        margin: EdgeInsets.symmetric(vertical: 1),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            ListTile(
              leading: Padding(
                padding: const EdgeInsets.only(right: 20.0),
                child: /*2,
                    child: Icon(Icons.question_mark,
                        size: 10, color: Colors.white))*/
                    badges.Badge(
                  badgeContent: Text(val[2]),
                  child: Icon(Icons.question_mark),
                ),
              ),
              title: Text(val[0],
                  style: TextStyle(fontSize: 8, color: Colors.indigoAccent)),
              subtitle: Text(val[1]),
            ),
          ],
        ));
  }

  FutureBuilder<List<List<dynamic>>?> _createSideMenu() {
    print('Main : _createSideMenu() : START');
    TextToDocParameter.questionCount = 1;
    return FutureBuilder(
      future: loadQuestionsFromFirestore(),
      builder: (context, snapshot) {
        return SideMenu(
          controller: sideMenu,
          style: SideMenuStyle(
            // showTooltip: false,
            displayMode: SideMenuDisplayMode.open,
            showHamburger: true,
            hoverColor: Colors.blue[100],
            selectedHoverColor: Colors.blue[100],
            selectedColor: Colors.lightBlue,
            selectedTitleTextStyle: const TextStyle(color: Colors.black),
            selectedIconColor: Colors.white,
          ),
          title: Column(
            children: [
              ConstrainedBox(
                constraints: const BoxConstraints(
                  maxHeight: 100,
                  maxWidth: 250,
                ),
                child: Image.asset(
                  'assets/images/ttmd_logo1.png', //'assets/images/drawer_header1.png',
                ),
              ),
              const Divider(
                indent: 8.0,
                endIndent: 8.0,
              ),
            ],
          ),
          footer: Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxHeight: 80,
              ),
              child: Container(
                color: const Color.fromARGB(
                    255, 240, 240, 240), // Colors.grey.withOpacity(1),////
                child: Column(
                  children: [
                    const Divider(
                      indent: 8.0,
                      endIndent: 8.0,
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      mainAxisSize: MainAxisSize.max,
                      children: [
                        CircleAvatar(
                          backgroundImage:
                              //const AssetImage('assets/images/john_smith.jpeg'),
                              NetworkImage(TextToDocParameter.picture),
                          radius: 30,
                        ),
                        Text("${TextToDocParameter.email}",
                            style: TextStyle(
                                color: Colors.blueAccent, fontSize: 12.0),
                            textAlign: TextAlign.end),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
          items: [
            SideMenuItem(
              title: 'Open data QnA',
              onTap: (index, _) {
                //sideMenu.changePage(index);
              },
              icon: const Icon(Icons.home),
              tooltipContent: "Open data QnA",
            ),
            SideMenuItem(
              title: 'New chat',
              onTap: (index, _) {
                TextToDocParameter.sessionId = "";
                print(
                    "Main: _createSideMenu() : New chat :  : TextToDocParameter.sessionId = ${TextToDocParameter.sessionId}");
              },
              icon: const Icon(Icons.restart_alt_outlined),
            ),
            if (snapshot.hasData) //if (TextToDocParameter.expert_mode)
              SideMenuExpansionItem(
                title: "Imported questions",
                icon: const Icon(Icons.manage_history_outlined),
                children: [
                  SideMenuItem(
                    builder: (context, displayMode) {
                      return ExpandableTree(
                        nodes: importedQuestionTreeNodeList,
                        nodeBuilder: _nodeBuilder2,
                        onSelect: (node) => _nodeSelected(context, node),
                      );
                    },
                    onTap: (index, _) {
                      //sideMenu.changePage(index);
                    },
                  )
                ],
              ),
            SideMenuExpansionItem(
              title: "History",
              icon: const Icon(Icons.manage_history_outlined),
              children: [
                SideMenuItem(
                  builder: (context, displayMode) {
                    return BlocBuilder<LoadQuestionCubit, LoadQuestionState>(
                      builder: (context, state) {
                        print(
                            "Main: _createSideMenu() : BlocBuilder<LoadQuestionCubit, LoadQuestionState> : state = $state");
                        print(
                            "Main: _createSideMenu() : BlocBuilder<LoadQuestionCubit, LoadQuestionState> : state.question = ${state.question}");
                        print(
                            "Main: _createSideMenu() : BlocBuilder<LoadQuestionCubit, LoadQuestionState> : state.time = ${state.time}");
                        _addData(state.question!, true);
                        return ExpandableTree(
                          nodes: nodes,
                          nodeBuilder: _nodeBuilder1,
                          onSelect: (node) => _nodeSelected1(context, node),
                        );
                      },
                    );
                  },
                  onTap: (index, _) {
                    //sideMenu.changePage(index);
                  },
                )
              ],
            ),
            SideMenuExpansionItem(
              title: "Most popular questions",
              icon: const Icon(Icons.manage_history_outlined),
              children: [
                SideMenuItem(
                  builder: (context, displayMode) {
                    return BlocBuilder<UpdatePopularQuestionsCubit,
                        UpdatePopularQuestionsState>(
                      builder: (context, state) {
                        print(
                            "Main: _createSideMenu() : Most popular questions : BlocBuilder<UpdatePopularQuestionsCubit,UpdatePopularQuestionsState> : state.status = ${state.status}");
                        print(
                            "Main: _createSideMenu() : Most popular questions : BlocBuilder<UpdatePopularQuestionsCubit,UpdatePopularQuestionsState> : state.mostPopularQuestionsList = ${state.mostPopularQuestionsList}");

                        //_addData(state.question!, true);
                        List<TreeNode<String>> nodesMostPopularQuestions =
                            CreateNodesMostPopularQuestion(
                                state.mostPopularQuestionsList!);

                        return ExpandableTree(
                          nodes: nodesMostPopularQuestions,
                          nodeBuilder: _nodeBuilder3,
                          onSelect: (node) => _nodeSelected1(context, node),
                        );
                      },
                    );
                  },
                  onTap: (index, _) {
                    //sideMenu.changePage(index);
                  },
                )
              ],
            ),
            SideMenuItem(
              title: 'Import',
              onTap: (index, _) async {
                var questionList = await importQuestions();

                if (questionList.length == 0) {
                  print(
                      "Main: _createSideMenu() : SideMenuItem : Import : onTap() : questionList is empty");
                  return;
                }

                //sort the list of list based on the name of the database :
                //grouping, scenario, question
                //Remove the header
                questionList.removeAt(0);
                questionList.sort((a, b) => a.first.compareTo(b.first));

                //Save questions into
                SaveImportedQuestionsToFirestore(questionList);

                for (var entry in questionList)
                  print(
                      "Main: _createSideMenu() : SideMenuItem : Import : onTap() : sorted questionList = ${entry[0]}, ${entry[2]}");

                setState(() {
                  importedQuestionTreeNodeList =
                      createQuestionList(questionList);
                  //print("Main: _createSideMenu() : SideMenuItem : Import : setState() : importedQuestionTreeNodeList = ${importedQuestionTreeNodeList}");
                });

                const snackBar = SnackBar(
                  content: Text('Importing questions.'),
                  duration: Duration(seconds: 3),
                );
                ScaffoldMessenger.of(context).showSnackBar(snackBar);
              },
              icon: const Icon(Icons.file_upload_outlined),
            ),
            /* //Commented out because the export of the answers (images and tables) to a pdf is not implemented yet
            SideMenuItem(
              title: 'Export',
              onTap: (index, _) {
                _createPDF();

                const snackBar = SnackBar(
                  content: Text('Exporting data to a pdf file.'),
                  duration: Duration(seconds: 5),
                );
                ScaffoldMessenger.of(context).showSnackBar(snackBar);
              },
              icon: const Icon(Icons.import_export_outlined),
            ),*/
            /*SideMenuItem(
              // do not delete
              title: 'Clear Firestore history',
              onTap: (index, _) async {
                int count = 0;
                //get all the documents corresponding to the user id
                try {
                  var querySnapshot = await db
                      .collection("session_logs")
                      .where("user_id", isEqualTo: TextToDocParameter.userID)
                      .get();

                  print(
                      "Main: _createSideMenu() : Clear Firestore history : querySnapshot.docs.length = ${querySnapshot.docs.length}");
                  print(
                      "Main: _createSideMenu() : Clear Firestore history : querySnapshot = ${querySnapshot}");

                  //delete all these documents
                  //await db.collection("session_logs").doc('FLoOKBwvVJ8mXkzu06He').delete();

                  for (var docSnapshot in querySnapshot.docs) {
                    print(
                        'Main: _createSideMenu() : Clear Firestore history : ${docSnapshot.id} => ${docSnapshot.data()}');
                    print(
                        'Main: _createSideMenu() : Clear Firestore history : docSnapshot.reference ${docSnapshot.reference}');
                    db
                        .collection("session_logs")
                        .doc('${docSnapshot.id}')
                        .delete();
                    count++;
                  }
                } catch (e) {
                  print(
                      'Main: _createSideMenu() : Clear Firestore history : EXCEPTION : $e');
                }
                var snackBar = SnackBar(
                  content: Text('Deleted $count questions from Firestore'),
                  duration: Duration(seconds: 3),
                );
                ScaffoldMessenger.of(context).showSnackBar(snackBar);
              },
              icon: const Icon(Icons.auto_delete_outlined),
            ),*/
            SideMenuItem(
              title: 'Settings',
              onTap: (index, _) async {
                await Navigator.pushNamed(context, '/settings',
                    arguments: {"dummy": ""});
                print(
                    "Main : createSideMenu() : TextToDocParameter.expert_mode = ${TextToDocParameter.expert_mode}");
                setState(() {
                  //useExpertMode = ts.Settings.isExpert;
                  //useExpertMode = TextToDocParameter.expert_mode;
                  TextToDocParameter.expert_mode;
                });

                //GalleryScreen
              },
              icon: const Icon(Icons.settings),
            ),
          ],
        );
      },
    )!;
  }

  @override
  void initState() {
    super.initState();
    setup();
  }

  Future<void> setup() async {
    _botKey = GlobalKey();

    bot =
        Bot(key: _botKey, textEditingController: textEditingController, db: db);

    //Initialize stepper states
    BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded(
        status: StepperStatus.initial,
        message: "Please enter a question.",
        stateStepper: StepState.disabled,
        isActiveStepper: false);
    print(
        "main: setup() : After BlocProvider.of<UpdateStepperCubit>(context).updateStepperStatusUploaded() : stepper initialized");
  }

  Future<void> initializeFirestore() async {
    await loadCfgFromFirestore();
    //await loadQuestionsFromFirestore();
  }

  Future<List<List<dynamic>>?> loadQuestionsFromFirestore() async {
    print('Main: loadQuestionsFromFirestore() : START');
    List<List<dynamic>>? questionList = [];

    print(
        'Main: loadQuestionsFromFirestore() : TextToDocParameter.imported_questions = ${TextToDocParameter.imported_questions}');
    print(
        'Main: loadQuestionsFromFirestore() : TextToDocParameter.userID = ${TextToDocParameter.userID}');

    try {
      var querySnapshot = await db!
          .collection("imported_questions")
          .where("user_id", isEqualTo: TextToDocParameter.userID)
          .orderBy('scenario', descending: false)
          .orderBy('order')
          .get();

      for (var docSnapshot in querySnapshot.docs) {
        final data = docSnapshot.data() as Map<String, dynamic>;
        print(
            'Main: loadQuestionsFromFirestore() : data["user_grouping"] = ${data["user_grouping"]} : data["scenario"] = ${data["scenario"]} : data["question"] = ${data["question"]}');
        questionList.add([
          data["user_grouping"],
          data["scenario"],
          data["question"],
          data["main_question"]
        ]);
      }

      print(
          'Main: loadQuestionsFromFirestore() : questionList.length = ${questionList.length}');
      print(
          'Main: loadQuestionsFromFirestore() : questionList = ${questionList}');

      //create the questionList from Firestore
      if (questionList.length == 0)
        questionList = null;
      else
        importedQuestionTreeNodeList = createQuestionList(questionList);

      /*BlocProvider.of<UpdateExpertModeCubit>(context)
          .updateExpertMode(TextToDocParameter.expert_mode);*/
    } catch (e) {
      print('Main: loadQuestionsFromFirestore() : EXCEPTION : e = $e');
    } finally {
      return questionList;
    }
  }

  Future<void> loadCfgFromFirestore() async {
    /*db = await FirebaseFirestore.instanceFor(
        app: app, databaseId: 'opendataqna-session-logs');*/

    print("main: loadCfgFromFirestore() : db = $db");

    if (TextToDocParameter.userID.isEmpty) {
      print(
          "main: loadCfgFromFirestore() : TextToDocParameter.userID is empty = ${TextToDocParameter.userID}");
      WidgetsBinding.instance.addPostFrameCallback((_) {
        noCfgStoredinFirestore();
      });
      return;
    }

    try {
      print(
          "main: loadCfgFromFirestore() : TextToDocParameter.userID = ${TextToDocParameter.userID}");

      DocumentSnapshot doc = await db!
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
            "main: loadCfgFromFirestore() : TextToDocParameter.anonymized_data = ${TextToDocParameter.anonymized_data}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.expert_mode = ${TextToDocParameter.expert_mode}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.firestore_database_id = ${TextToDocParameter.firestore_database_id}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.endpoint_opendataqnq = ${TextToDocParameter.endpoint_opendataqnq}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.firebase_app_name = ${TextToDocParameter.firebase_app_name}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.firestore_history_collection = ${TextToDocParameter.firestore_history_collection}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.firestore_cfg_collection = ${TextToDocParameter.firestore_cfg_collection}");
        print(
            "main: loadCfgFromFirestore() : TextToDocParameter.imported_questions = ${TextToDocParameter.imported_questions}");

        BlocProvider.of<DisplayStepperCubit>(context)
            .displayStepper(TextToDocParameter.expert_mode);
      } else {
        print("main: loadCfgFromFirestore() : doc == null");
        WidgetsBinding.instance.addPostFrameCallback((_) {
          noCfgStoredinFirestore();
        });
      }
    } catch (e) {
      print("main: loadCfgFromFirestore() : EXCEPTION ON FIRESTORE : e = $e");
      WidgetsBinding.instance.addPostFrameCallback((_) {
        noCfgStoredinFirestore();
      });
    }
  }

  Future<List<String>> _getUserGrouping() async {
    print('Main : _getUserGrouping() : START');
    List<String> resp = [];

    await initializeFirestore();

    print('Main : _getUserGrouping() : bot = $bot');

    Map<String, String>? _headers = {
      "Content-Type": "application/json",
      //"Authorization": " Bearer ${client!.credentials.accessToken.toString()}",
    };

    try {
      print(
          'Main : _getUserGrouping() : url = ${TextToDocParameter.endpoint_opendataqnq}/available_databases');

      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/available_databases',
          method: "GET");

      print('Main : _getUserGrouping() : response = ' + response.toString());

      final jsonData = jsonDecode(response);

      if (jsonData != null) {
        print('Main : _getUserGrouping() : jsonData = $jsonData');

        /* Expected response :
        {
          "Error": "",
          "KnownDB": "[{\"table_schema\":\"imdb-postgres\"},{\"table_schema\":\"retail-postgres\"}]",
          "ResponseCode": 200
        }*/

        var knownSqlMap = jsonDecode(jsonData['KnownDB']);

        print('Main : _getUserGrouping() : knownSqlMap = ${knownSqlMap}');

        print(
            'Main : _getUserGrouping() : knownSqlMap[0] = ${knownSqlMap[0].toString()}');

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
      print('Main : _getUserGrouping() : EXCEPTION = $e');
      throw Exception('Failed to get earning calls question suggestions: $e');
    } finally {
      print('Main : _getUserGrouping() : resp = $resp');
      return resp;
    }
  }

  Future<List<Map<String, dynamic>>> _getQuestions() async {
    var questionList = await _getLastQuestions();
    print("Main : _getQuestions() : questionList = $questionList");
    return questionList;
  }

  @override
  Widget build(BuildContext context) {
    debugPaintSizeEnabled = false;
    screenSize = MediaQuery.of(context).size;
    bool _isEarningCalls1Hovered = false;
    bool _isEarningCalls2Hovered = false;
    bool _isBookingAnalysisHovered = false;
    bool _isFunelAnalysisHovered = false;

    print("Main : build() : START");
    print("Main : build() : TuserGroupingList = ${userGroupingList}");
    print(
        "Main : build() : TextToDocParameter.currentUserGrouping = ${TextToDocParameter.currentUserGrouping}");

    return Scaffold(
      appBar: AppBar(
        title: Image.asset('assets/images/cymbal_logo.png', scale: 2),
        centerTitle: false,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 100),
            child: Container(
              width: 320,
              child: FutureBuilder(
                future: _getUserGrouping(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return Padding(
                      padding: const EdgeInsets.only(right: 135.0, left: 135.0),
                      child: Container(
                          width: 50,
                          height: 50,
                          child: /*Text('TEST')*/ CircularProgressIndicator()),
                    ); // Loading indicator
                  } else if (snapshot.hasError) {
                    return Text('-Error-: ${snapshot.error}');
                    // Error handling
                  } else {
                    if (snapshot.data!.isNotEmpty) {
                      TextToDocParameter.currentUserGrouping =
                          snapshot.data![0];
                      TextToDocParameter.userGroupingList = snapshot.data!;
                      selectedValueNotifier.value = snapshot.data!.first;
                      print(
                          "main: build() : TextToDocParameter.currentUserGrouping = ${TextToDocParameter.currentUserGrouping}");
                      print("main: build() : selectedValue = ${selectedValue}");
                    }
                    return ValueListenableBuilder<String?>(
                        valueListenable: selectedValueNotifier,
                        builder: (context, value, child) {
                          return Container(
                            width: 300,
                            child: Row(
                              children: [
                                Text("User Grouping:   ",
                                    style: TextStyle(
                                        fontSize: 13.0, color: Colors.black)),
                                Expanded(
                                  child: DropdownButton<String>(
                                    value: value,
                                    //icon: const Icon(Icons.arrow_downward),
                                    elevation: 16,
                                    style: const TextStyle(
                                        fontSize: 13.0,
                                        color: Colors.deepPurple),
                                    onChanged: (String? value) {
                                      selectedValueNotifier.value = value!;
                                      TextToDocParameter.currentUserGrouping =
                                          value!;
                                      print(
                                          'Main: build() : DropdownButton : onChanged() : TextToDocParameter.currentUserGrouping => ${TextToDocParameter.currentUserGrouping}');
                                    },
                                    items: snapshot.data!
                                        .map<DropdownMenuItem<String>>(
                                            (String value) {
                                      return DropdownMenuItem<String>(
                                        value: value,
                                        child: Text(value),
                                      );
                                    }).toList(),
                                  ),
                                ),
                              ],
                            ),
                          );
                        });
                  }
                },
              ),
            ),
          ),
        ],
        leading: Text(""),
      ),
      body: Row(
        mainAxisSize: MainAxisSize.max,
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          _createSideMenu()!,
          const VerticalDivider(
            width: 0,
          ),
          Expanded(
            child: Stack(
              children: [
                Container(
                  padding: EdgeInsets.only(left: 100, right: 100),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    //mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      BlocBuilder<DisplayStepperCubit, DisplayStepperState>(
                        builder: (context, state) {
                          print(
                              "Main: build() : BlocBuilder<DisplayStepperCubit, DisplayStepperState> : START");
                          if (state.status ==
                              displayStepperStatus.display_stepper) {
                            print(
                                "Main: build() : BlocBuilder<DisplayStepperCubit, DisplayStepperState> : state =${state.status}");
                            return Flexible(
                                fit: FlexFit.loose,
                                child: Padding(
                                  padding: const EdgeInsets.only(bottom: 5),
                                  child: _buildStepper(),
                                ),
                                flex: 2);
                          } else if (state.status ==
                              displayStepperStatus.remove_stepper) {
                            print(
                                "Main: build() : BlocBuilder<DisplayStepperCubit, DisplayStepperState> : state =${state.status}");
                            return Text("");
                          } else {
                            print(
                                "Main: build() : BlocBuilder<DisplayStepperCubit, DisplayStepperState> : ERROR : state =$state");
                            return Text("Unable to load user_grouping");
                          }
                        },
                      ),
                      bot!,
                      BlocBuilder<NewSuggestionCubit, NewSuggestionState>(
                        builder: (context, state) {
                          if (state.status == NewSuggestionStateStatus.loaded) {
                            print(
                                "Main: build() : BlocBuilder<NewSuggestionCubit, NewSuggestionState> : START : state =$state");
                            return makeSuggestions(
                                state.suggestionList!, state.scenarioNumber!);
                          } else {
                            return makeSuggestions(["x:", "x:", "x:"], 0);
                          }
                        },
                      ),
                      //const Spacer(flex: 1,),
                    ],
                  ),
                ),
                BlocBuilder<FirstQuestionCubit, FirstQuestionState>(
                  builder: (context, state) {
                    print(
                        "Main : build() : BlocBuilder<FirstQuestionCubit, FirstQuestionState> : START");
                    if (state.status ==
                        firstQuestionStatus.display_welcome_message) {
                      print(
                          "Main : build() : BlocBuilder<FirstQuestionCubit, FirstQuestionState> : state.status == firstQuestionStatus.display_welcome_message");
                      return Positioned(
                        //top: 0,
                        //left: 200, //200,
                        child: Column(
                            mainAxisAlignment: MainAxisAlignment.start,
                          children: [
                            Container(height: 100),
                            Image.asset(
                              //UNCOMMENT
                              "assets/images/gemini.png"!,
                              height: 90,
                              width: 90,
                              fit: BoxFit.cover,
                            ),
                            Padding(
                              padding: const EdgeInsets.only(bottom: 50),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.center,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text(
                                          "Hello ${TextToDocParameter.firstName} ! ",
                                          style: TextStyle(
                                              fontSize: 40.0,
                                              fontWeight: FontWeight.bold)),
                                      GradientText(
                                        'How can I help you today ?',
                                        style: TextStyle(
                                            fontSize: 40.0,
                                            fontWeight: FontWeight.bold),
                                        colors: [
                                          Colors.blue,
                                          Colors.red,
                                          Colors.teal,
                                        ],
                                      ),
                                    ],
                                  ),
                                  const Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Text(
                                            'Learn more by selecting a card below\n',
                                            style: TextStyle(
                                                fontSize: 30.0,
                                                fontWeight: FontWeight.normal,
                                                color: Colors.black))
                                      ])
                                ],
                              ),
                            ),
                            FutureBuilder(
                                future: _getQuestions(),
                                builder: (context, snapshot) {
                                  if (snapshot.connectionState ==
                                      ConnectionState.waiting) {
                                    return CircularProgressIndicator(); // Loading indicator
                                  } else if (snapshot.hasError) {
                                    return Text('*Error*: ${snapshot.error}');
                                    // Error handling
                                  } else {
                                    return Container(
                                      width: screenSize!.width / 1.5,
                                      child: Column(
                                        children: [
                                          Row(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.center,
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceEvenly,
                                            children: [
                                              if (snapshot.data!.length >= 1)
                                                createCardsSuggestion(
                                                    title: snapshot.data![0]
                                                            ['scenario_name'] ??
                                                        "Error - No title",
                                                    text: snapshot.data![0]
                                                            ['user_question'] ??
                                                        "Error - No question",
                                                    scenarioNumber: 2,
                                                    isHovered:
                                                        _isEarningCalls1Hovered,
                                                    imagePath:
                                                        "assets/images/last_questions.png",
                                                    timeStamp: snapshot.data![0]
                                                            ['timestamp'] ??
                                                        "Error - No timestamp",
                                                userGrouping: snapshot.data![0]
                                                ['user_grouping']),
                                              if (snapshot.data!.length >= 2)
                                                createCardsSuggestion(
                                                    title: snapshot.data![1]
                                                            ['scenario_name'] ??
                                                        "Error - No title",
                                                    text: snapshot.data![1]
                                                            ['user_question'] ??
                                                        "Error - No question",
                                                    scenarioNumber: 2,
                                                    isHovered:
                                                        _isEarningCalls1Hovered,
                                                    imagePath:
                                                        "assets/images/last_questions.png",
                                                    timeStamp: snapshot.data![1]
                                                            ['timestamp'] ??
                                                        "Error - No timestamp",
                                                    userGrouping: snapshot.data![0]
                                                    ['user_grouping']),
                                            ],
                                          ),
                                          Row(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.center,
                                              mainAxisAlignment:
                                                  MainAxisAlignment.spaceEvenly,
                                              children: [
                                                if (snapshot.data!.length >= 3)
                                                  createCardsSuggestion(
                                                      title: snapshot.data![2][
                                                              'scenario_name'] ??
                                                          "Error - No title",
                                                      text: snapshot.data![2][
                                                              'user_question'] ??
                                                          "Error - No question",
                                                      scenarioNumber: 2,
                                                      isHovered:
                                                          _isEarningCalls1Hovered,
                                                      imagePath:
                                                          "assets/images/last_questions.png",
                                                      timeStamp: snapshot
                                                                  .data![2]
                                                              ['timestamp'] ??
                                                          "Error - No timestamp",
                                                      userGrouping: snapshot.data![0]
                                                      ['user_grouping']),
                                                if (snapshot.data!.length >= 4)
                                                  createCardsSuggestion(
                                                      title: snapshot.data![3][
                                                              'scenario_name'] ??
                                                          "Error - No title",
                                                      text: snapshot.data![3][
                                                              'user_question'] ??
                                                          "Error - No question",
                                                      scenarioNumber: 2,
                                                      isHovered:
                                                          _isEarningCalls1Hovered,
                                                      imagePath:
                                                          "assets/images/last_questions.png",
                                                      timeStamp: snapshot
                                                                  .data![3]
                                                              ['timestamp'] ??
                                                          "Error - No timestamp",
                                                      userGrouping: snapshot.data![0]
                                                      ['user_grouping']),
                                              ])
                                        ],
                                      ),
                                    );
                                  }
                                }), //UNCOMMENT
                          ],
                        ), //UNCOMMENT
                      );
                    } else {
                      print(
                          "Main : build() : BlocBuilder<FirstQuestionCubit, FirstQuestionState> : state.status != firstQuestionStatus.display_welcome_message");
                      isFirstQuestionStatus = false;
                      return Text("");
                    }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
      // This trailing comma makes auto-formatting nicer for build methods.
    );
  }

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  Future<List<int>> _createPDF() async {
    //Method not called because the export menu has been commented out.
    //This will remain commented out until it is possible to screenshot web views
    List<int> bytes = [];

    return bytes;
  }

  String displayDateTime() {
    String? dateTimeS;

    final now = DateTime.now();
    dateTimeS = DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
    return dateTimeS!;
  }

  Widget createCards(
      {required String? imagePath,
      required String? title,
      required String subTitle,
      required String text,
      required int badgeCount}) {
    return Expanded(
      child: Container(
        width: screenSize!.width / 3.5,
        //height: screenSize!.height / 6,
        child: Card(
          elevation: 10,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          // Define how the card's content should be clipped
          clipBehavior: Clip.antiAliasWithSaveLayer,
          // Define the child widget of the card
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              // Add padding around the row widget
              Padding(
                padding: const EdgeInsets.all(10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    // Add an image widget to display an image
                    Image.asset(
                      imagePath!,
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    // Add some spacing between the image and the text
                    Container(width: 20),
                    // Add an expanded widget to take up the remaining horizontal space
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          // Add some spacing between the top of the card and the title
                          Container(height: 5),
                          // Add a title widget
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                title!,
                                style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF37474F)),
                              ),
                              badges.Badge(
                                position: badges.BadgePosition.topEnd(
                                    top: -10, end: -12),
                                showBadge: true,
                                ignorePointer: false,
                                onTap: () {},
                                badgeContent: Text(
                                    badgeCount < 10
                                        ? "  " + badgeCount.toString()
                                        : badgeCount.toString(),
                                    style: TextStyle(
                                        fontSize: 15,
                                        color: Colors
                                            .white)), //Icon(Icons.check, color: Colors.white, size: 14),
                                badgeAnimation: badges.BadgeAnimation.rotation(
                                  animationDuration: Duration(seconds: 1),
                                  colorChangeAnimationDuration:
                                      Duration(seconds: 1),
                                  loopAnimation: false,
                                  curve: Curves.fastOutSlowIn,
                                  colorChangeAnimationCurve: Curves.easeInCubic,
                                ),
                                badgeStyle: badges.BadgeStyle(
                                  shape: badges.BadgeShape.instagram,
                                  badgeColor: Colors.red,
                                  //padding: EdgeInsets.all(5),
                                  borderRadius: BorderRadius.circular(4),
                                  borderSide:
                                      BorderSide(color: Colors.white, width: 2),
                                  elevation: 2,
                                ),
                                //child: Text('Badge'),
                              ),
                            ],
                          ),
                          // Add some spacing between the title and the subtitle
                          Container(height: 5),
                          // Add a subtitle widget
                          Text(
                            subTitle!,
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium!
                                .copyWith(
                                  color: Colors.grey[500],
                                ),
                          ),
                          // Add some spacing between the subtitle and the text
                          Container(height: 10),
                          // Add a text widget to display some text
                          Text(
                            text.length <= 35
                                ? text!
                                : text!.substring(0, 35) + ' ...',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium!
                                .copyWith(
                                  color: Colors.grey[700],
                                ),
                            maxLines: 1,
                          ),
                          Row(children: [
                            Spacer(),
                            TextButton(
                              style: TextButton.styleFrom(
                                foregroundColor: Colors.transparent,
                              ),
                              child: const Text(
                                "LOAD",
                                style: TextStyle(color: Color(0xFFFF4081)),
                              ),
                              onPressed: () {
                                print(
                                    'Bot() : build() : TextButton : onPressed() : START : text = $text');
                                //BlocProvider.of<LoadQuestionCubit>(context).loadQuestionToChat("test");
                                //setState(() {
                                textEditingController.text = text;
                                _isFirstQuestionNotAskedYet = false;
                                //});
                              },
                            ),
                          ])
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Padding makeSuggestions(
      List<String> listRandomQuestions, int scenarioNumber) {
    print("Main: makeSuggestions() : START");
    TextToDocParameter.lastScenarioNumber = scenarioNumber;

    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Container(
          width: screenSize!.width,
          //height: screenSize!.height / 20,
          color: Colors.white,
          child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                if (listRandomQuestions.length >= 1 &&
                    listRandomQuestions[0] != "x:")
                  Expanded(
                    child: ConstrainedBox(
                      constraints: BoxConstraints(
                        minWidth: 100.0, // Set minimum width
                        maxWidth: 400.0, // Set maximum width
                      ),
                      child: InkWell(
                        onTap: () {
                          //textEditingController.text = "Can you provide the Top 10 pace platinum accounts with booking value and YOY growth %?";
                          textEditingController.text =
                              listRandomQuestions[0].split(":")[1];
                          _isFirstQuestionNotAskedYet = false;
                          BlocProvider.of<NewSuggestionCubit>(context)
                              .generateNewSuggestions(
                                  scenarioNumber, textEditingController.text,
                                  isACannedQuestion: false);
                          print(
                              "Main: makeSuggestions() : textEditingController.text = = ${textEditingController.text}");
                        },
                        child: Card(
                          elevation: 5,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(5.0),
                            child: Row(
                              children: [
                                Image.asset(
                                  "assets/images/suggestions.png",
                                  height: 20,
                                  width: 20,
                                  fit: BoxFit.cover,
                                ),
                                Flexible(
                                  child: Text(
                                      //' Can you provide the Top 10 pace platinum accounts with booking value and YOY growth %? ',
                                      listRandomQuestions[0].split(":")[1],
                                      style: TextStyle(
                                        decoration: TextDecoration.underline,
                                        fontSize: 15,
                                      ),
                                      softWrap: true,
                                      overflow: TextOverflow.ellipsis,
                                      maxLines: 2),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                //Container(width: 10),
                if (listRandomQuestions.length >= 2 &&
                    listRandomQuestions[1] != "x:")
                  Expanded(
                    child: ConstrainedBox(
                      constraints: BoxConstraints(
                        minWidth: 100.0, // Set minimum width
                        maxWidth: 400.0, // Set maximum width
                      ),
                      child: InkWell(
                        onTap: () {
                          textEditingController.text =
                              listRandomQuestions[1].split(":")[1];
                          _isFirstQuestionNotAskedYet = false;
                          BlocProvider.of<NewSuggestionCubit>(context)
                              .generateNewSuggestions(
                                  scenarioNumber, textEditingController.text,
                                  isACannedQuestion: false);
                          print(
                              "Main: makeSuggestions() : textEditingController.text = = ${textEditingController.text}");
                        },
                        child: Card(
                          elevation: 5,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(5.0),
                            child: Row(
                              children: [
                                Image.asset(
                                  "assets/images/suggestions.png",
                                  height: 20,
                                  width: 20,
                                  fit: BoxFit.cover,
                                ),
                                Flexible(
                                  child: Text(
                                      listRandomQuestions[1].split(":")[1],
                                      style: TextStyle(
                                        decoration: TextDecoration.underline,
                                        fontSize: 15,
                                      ),
                                      softWrap: true,
                                      overflow: TextOverflow.ellipsis,
                                      maxLines: 2),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                //Container(width: 10),
                if (listRandomQuestions.length >= 3 &&
                    listRandomQuestions[2] != "x:")
                  Expanded(
                    child: ConstrainedBox(
                      constraints: BoxConstraints(
                        minWidth: 100.0, // Set minimum width
                        maxWidth: 400.0, // Set maximum width
                      ),
                      child: InkWell(
                        onTap: () {
                          textEditingController.text =
                              listRandomQuestions[2].split(":")[1];
                          _isFirstQuestionNotAskedYet = false;
                          BlocProvider.of<NewSuggestionCubit>(context)
                              .generateNewSuggestions(
                                  scenarioNumber, textEditingController.text,
                                  isACannedQuestion: false);
                          print(
                              "Main: makeSuggestions() : textEditingController.text = = ${textEditingController.text}");
                        },
                        child: Card(
                          elevation: 5,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(5.0),
                            child: Row(
                              children: [
                                Image.asset(
                                  "assets/images/suggestions.png",
                                  height: 20,
                                  width: 20,
                                  fit: BoxFit.cover,
                                ),
                                Flexible(
                                  child: Text(
                                      //' Can you add CM sold margin to above list? ',
                                      listRandomQuestions[2].split(":")[1],
                                      style: TextStyle(
                                        decoration: TextDecoration.underline,
                                        fontSize: 15,
                                      ),
                                      softWrap: true,
                                      overflow: TextOverflow.ellipsis,
                                      maxLines: 2),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
              ])),
    );
  }

  Widget createCardsSuggestion(
      {required String? title,
      required String text,
      required int scenarioNumber,
      required bool isHovered,
      required String imagePath,
      required String timeStamp,
      required String userGrouping}) {
    print('Main : createCardsSuggestion() : START');
    print('Main : createCardsSuggestion() : START : text = $text');
    print('Main : createCardsSuggestion() : START : title = $title');
    print('Main : createCardsSuggestion() : START : userGrouping = $userGrouping');
    return Expanded(
      child: InkWell(
        onTap: () {
          print(
              'Main : createCardsSuggestion() : TextButton : onPressed() : START : text = $text');

          textEditingController.text = text;
          _isFirstQuestionNotAskedYet = false;
          //Use the user_grouping associated to the question
          //selectedValueNotifier.value = title;
          selectedValueNotifier.value = userGrouping;

          //Setting the current user_grouping value
          TextToDocParameter.currentUserGrouping = userGrouping;

          BlocProvider.of<NewSuggestionCubit>(context).generateNewSuggestions(
              scenarioNumber, text,
              isACannedQuestion: false,
          userGrouping: userGrouping);
        },
        onHover: (value) {

        },
        child: Container(
          width: screenSize!.width / 2.5,
          height: screenSize!.height / 6,
          child: Card(
            color: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            // Define how the card's content should be clipped
            clipBehavior: Clip.antiAliasWithSaveLayer,
            // Define the child widget of the card
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.start,
                mainAxisSize: MainAxisSize.max,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Image.asset(
                    imagePath!,
                    height: 50,
                    width: 50,
                    fit: BoxFit.cover,
                  ),
                  Container(width: 20),
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      //mainAxisSize: MainAxisSize.max,
                      children: <Widget>[
                        // Add some spacing between the top of the card and the title
                        Container(height: 5),
                        // Add a title widget
                        Flexible(
                          //flex: 1,
                          child: Container(
                            color: isHovered ? Colors.blueGrey : null,
                            child: Text(
                              title!,
                              style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF37474F)),
                            ),
                          ),
                        ),
                        // Add some spacing between the title and the subtitle
                        Container(height: 5),
                        // Add some spacing between the subtitle and the text
                        // Add a text widget to display some text
                        Flexible(
                          //flex: 6,
                          child: Container(
                            color: isHovered ? Colors.blueGrey : null,
                            child: Text(
                              text,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium!
                                  .copyWith(
                                    color: Colors.grey[700],
                                  ),
                              maxLines: 6,
                              softWrap: true,
                              overflow: TextOverflow.visible,
                            ),
                          ),
                        ),
                        Container(height: 10),
                        Flexible(
                          //flex: 6,
                          child: Container(
                            padding: EdgeInsets.only(top: 5),
                            color: isHovered ? Colors.blueGrey : null,
                            child: Text(
                              'Question typed on the ' + timeStamp,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall!
                                  .copyWith(
                                    color: Colors.blueAccent,
                                  ),
                              maxLines: 6,
                              softWrap: true,
                              overflow: TextOverflow.visible,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _createDebugInfoCard(Widget leading, String title, String subtitle,
      String imageTrailingPath, Widget info, String infoText) {
    final ButtonStyle flatButtonStyle = TextButton.styleFrom(
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(4.0)),
      ),
    );
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12.0),
      child: ExpansionTileCard(
        //key: cardA,
        initiallyExpanded: true,
        leading: leading,
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          mainAxisSize: MainAxisSize.max,
          children: [
            Flexible(
              flex: 5,
              child: Text(title, style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            Flexible(
                flex: 1,
                child: Image.asset(width: 75, height: 75, imageTrailingPath))
          ],
        ),
        subtitle: Text(subtitle, style: TextStyle(fontSize: 12)),
        children: <Widget>[
          const Divider(
            thickness: 1.0,
            height: 1.0,
          ),
          Align(
            alignment: Alignment.centerLeft,
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16.0,
                vertical: 8.0,
              ),
              child: info,
            ),
          ),
          ButtonBar(
            alignment: MainAxisAlignment.spaceBetween,
            buttonHeight: 52.0,
            buttonMinWidth: 90.0,
            children: <Widget>[
              TextButton(
                style: flatButtonStyle,
                onPressed: () async {
                  await Clipboard.setData(ClipboardData(text: infoText));
                },
                child: const Column(
                  children: <Widget>[
                    Icon(Icons.copy),
                    Padding(
                      padding: EdgeInsets.symmetric(vertical: 2.0),
                    ),
                    Text('Copy'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Container _buildStepper() {
    final canCancel = currentStep > 0;
    final canContinue = currentStep < 3;
    StepState? stateStepperUploaded;
    bool? isActiveUploaded;
    StepState? stateStepperExtracted;
    bool? isActiveExtracted;
    StepState? stateStepperCompared;
    bool? isActiveCompared;
    StepState? stateStepperCommitted;
    bool? isActiveCommitted;

    StepState? stateStepperEnterQuestion;
    bool? isActiveEnterQuestion;
    String? messageStepperEnterQuestion = "";
    StepState? stateStepperGenerateSQL;
    bool? isActiveGenerateSQL;
    String? messageStepperGenerateSQL = "";
    StepState? stateStepperRunQuery;
    bool? isActiveRunQuery;
    String? messageStepperRunQuery = "";
    StepState? stateStepperGetGraphDescription;
    bool? isActiveGetGraphDescription;
    String? messageStepperGraphDescription = "";
    StepState? stateStepperGetTextSummary;
    bool? isActiveGetTextSummary;
    String? messageStepperGetTextSummary = "";

    String? message = "";

    void setStepsStates(UpdateStepperState state) {
      print('Main : _buildStepper() : setStepsStates() : Start');
      print(
          'Main : _buildStepper() : setStepsStates() : status = ${state.status}');
      print('Main : _buildStepper() : currentStep : $currentStep');
      switch (state.status) {
        case StepperStatus.initial:
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.initial');
          currentStep = 0;
          stateStepperEnterQuestion = StepState.disabled;
          isActiveEnterQuestion = false;
          stateStepperGenerateSQL = StepState.disabled;
          isActiveGenerateSQL = false;
          stateStepperRunQuery = StepState.disabled;
          isActiveRunQuery = false;
          stateStepperGetGraphDescription = StepState.disabled;
          isActiveGetGraphDescription = false;
          stateStepperGetTextSummary = StepState.disabled;
          isActiveGetTextSummary = false;
          message = state.message;
          break;
        case StepperStatus.enter_question:
          stepperExpertInfoList.clear();
          currentStep = 0;
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.enter_question');
          stateStepperEnterQuestion = StepState.complete;
          isActiveEnterQuestion = true;
          stateStepperGenerateSQL = StepState.disabled;
          isActiveGenerateSQL = false;
          stateStepperRunQuery = StepState.disabled;
          isActiveRunQuery = false;
          stateStepperGetGraphDescription = StepState.disabled;
          isActiveGetGraphDescription = false;
          stateStepperGetTextSummary = StepState.disabled;
          isActiveGetTextSummary = false;
          messageStepperEnterQuestion = "Question entered in 0 s";
          overallProcessingTime = 0;
          stepperExpertInfoList.add(StepperExpertInfo());
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.enter_question : stepperExpertInfoList.length = ${stepperExpertInfoList.length}');
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.enter_question : stepperExpertInfoList = ${stepperExpertInfoList}');
          break;
        case StepperStatus.generate_sql:
          currentStep = 1;
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.generate_sql');
          stateStepperEnterQuestion = StepState.complete;
          isActiveEnterQuestion = true;
          stateStepperGenerateSQL = StepState.complete;
          isActiveGenerateSQL = true;
          stateStepperRunQuery = StepState.disabled;
          isActiveRunQuery = false;
          stateStepperGetGraphDescription = StepState.disabled;
          isActiveGetGraphDescription = false;
          stateStepperGetTextSummary = StepState.disabled;
          isActiveGetTextSummary = false;
          messageStepperGenerateSQL = state.message! +
              " " +
              ((state.debugInfo.stepDuration!.toDouble()) / 1000).toString() +
              " s";
          overallProcessingTime = overallProcessingTime +
              (state.debugInfo.stepDuration!.toDouble()) / 1000;
          stepperExpertInfoList.add(state.debugInfo);
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.generate_sql : stepperExpertInfoList.length = ${stepperExpertInfoList.length}');
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.generate_sql : stepperExpertInfoList = ${stepperExpertInfoList}');
          break;
        case StepperStatus.run_query:
          currentStep = 2;
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.run_query');
          stateStepperEnterQuestion = StepState.complete;
          isActiveEnterQuestion = true;
          stateStepperGenerateSQL = StepState.complete;
          isActiveGenerateSQL = true;
          stateStepperRunQuery = StepState.complete;
          isActiveRunQuery = true;
          stateStepperGetGraphDescription = StepState.disabled;
          isActiveGetGraphDescription = false;
          stateStepperGetTextSummary = StepState.disabled;
          isActiveGetTextSummary = false;
          messageStepperRunQuery = state.message! +
              " " +
              ((state.debugInfo.stepDuration!.toDouble()) / 1000).toString() +
              " s";
          overallProcessingTime = overallProcessingTime +
              (state.debugInfo.stepDuration!.toDouble()) / 1000;
          stepperExpertInfoList.add(state.debugInfo);
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.run_query : stepperExpertInfoList.length = ${stepperExpertInfoList.length}');
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.run_query : stepperExpertInfoList = ${stepperExpertInfoList}');
          break;
        case StepperStatus.get_graph_description:
          currentStep = 3;
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.get_graph_description');
          stateStepperEnterQuestion = StepState.complete;
          isActiveEnterQuestion = true;
          stateStepperGenerateSQL = StepState.complete;
          isActiveGenerateSQL = true;
          stateStepperRunQuery = StepState.complete;
          isActiveRunQuery = true;
          stateStepperGetGraphDescription = StepState.complete;
          isActiveGetGraphDescription = true;
          stateStepperGetTextSummary = StepState.disabled;
          isActiveGetTextSummary = false;
          messageStepperGraphDescription = state.message! +
              " " +
              ((state.debugInfo.stepDuration!.toDouble()) / 1000).toString() +
              " s";
          overallProcessingTime = overallProcessingTime +
              (state.debugInfo.stepDuration!.toDouble()) / 1000;
          stepperExpertInfoList.add(state.debugInfo);
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.get_graph_description : stepperExpertInfoList.length = ${stepperExpertInfoList.length}');
          print(
              'Main : _buildStepper() : setStepsStates() : Switch: StepperStatus.get_graph_description : stepperExpertInfoList = ${stepperExpertInfoList}');
          break;
        default:
          currentStep = 0;
          stateStepperUploaded = StepState.disabled;
          isActiveUploaded = false;
          stateStepperExtracted = StepState.disabled;
          isActiveExtracted = false;
          stateStepperCompared = StepState.disabled;
          isActiveCompared = false;
          stateStepperCommitted = StepState.disabled;
          isActiveCommitted = false;
          message = state.message;
      }
    }

    Future<void> _dialogRequestGenerated(
        BuildContext context, StepperExpertInfo debugInfo, String title) {
      print(
          "Main: _dialogRequestGenerated() : title = $title : debugInfo.response = ${debugInfo.response}");
      return showDialog<void>(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: Text(title),
            content: SingleChildScrollView(
              child: Container(
                  width: screenSize!.width / 2,
                  child: Column(
                    children: [
                      _createDebugInfoCard(
                          Icon(Icons.link),
                          'URI POST',
                          'URI used in this step.',
                          'assets/images/https.png',
                          Text(
                            debugInfo.uri!,
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium!
                                .copyWith(fontSize: 16),
                          ),
                          debugInfo.uri!),
                      _createDebugInfoCard(
                          //FaIcon(icon),
                          Icon(Icons.https),
                          'HTTPS Body',
                          'Json body of the request',
                          'assets/images/json.png',
                          Container(
                              child: JsonViewer(jsonDecode(debugInfo.body!))),
                          debugInfo.body!),
                      _createDebugInfoCard(
                          //FaIcon(icon),
                          Icon(Icons.https),
                          'HTTPS Headers',
                          'Headers sent in the HTTPS request.',
                          'assets/images/https_header.png',
                          Container(
                              child: JsonViewer(jsonDecode(debugInfo.header!))),
                          debugInfo.header!),
                      _createDebugInfoCard(
                          FaIcon(FontAwesomeIcons.reply),
                          'HTTPS Response',
                          'HTTPS body of the response',
                          'assets/images/json.png',
                          (!debugInfo.response!.contains('syntax error') && !debugInfo.response!.contains('SyntaxError') ) ?
                          Container(
                              child:
                                  JsonViewer(jsonDecode(debugInfo.response!..replaceAll('"', '\\"')))) : Container(child: Text(debugInfo.response!)),
                          debugInfo.response!),
                      _createDebugInfoCard(
                          FaIcon(FontAwesomeIcons.code),
                          'Status Code',
                          'HTTPS answer status code',
                          'assets/images/status_code.png',
                          Text(
                            debugInfo.statusCode!.toString(),
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium!
                                .copyWith(fontSize: 16),
                          ),
                          debugInfo.statusCode!.toString()),
                      _createDebugInfoCard(
                          Icon(Icons.timer),
                          'Processing Time',
                          'Step duration in seconds',
                          'assets/images/elapsed_time.png',
                          Text(
                            (debugInfo.stepDuration!.toDouble() / 1000)
                                    .toString() +
                                " s",
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium!
                                .copyWith(fontSize: 16),
                          ),
                          (debugInfo.stepDuration!.toDouble() / 1000)
                                  .toString() +
                              " s"),
                      //Text("SQL request\n: ${debugInfo.generatedSQLText}"),
                    ],
                  )),
            ), //Text(DicInfoExtractedMap.toString(),),
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

    return Container(
      child: BlocBuilder<UpdateStepperCubit, UpdateStepperState>(
        builder: (context, state) {
          setStepsStates(state);
          return Stepper(
            controlsBuilder: (BuildContext context, ControlsDetails controls) {
              return Container(); //to remove the continue and cancel buttons
            },
            type: StepperType.horizontal,
            currentStep: currentStep,
            onStepTapped: (int index) {
              String title = "";
              print(
                  'HomePage() : build() : Stepper : onStepTapped() : index = $index');
              switch (index) {
                case 0:
                  title = "";
                  break;
                case 1:
                  title = "SQL Request Generation";
                  break;
                case 2:
                  title = "Data Retrieval";
                  break;
                case 3:
                  title = "Graph Description Retrieval";
                  break;
                default:
                  title = "";
                  break;
              }

              print(
                  'HomePage() : build() : END : Stepper : onStepTapped() : index = $index');
              print(
                  'HomePage() : build() : END : Stepper : onStepTapped() : TextToDocParameter.isTextTodocGlobal = ${TextToDocParameter.isTextTodocGlobal}');
              print(
                  'HomePage() : build() : END : Stepper : onStepTapped() : stepperExpertInfoList.length = ${stepperExpertInfoList.length}');

              //temporary knob to dispaly info about TextToDoc request/answer
              if (TextToDocParameter.isTextTodocGlobal &&
                  index == 3 &&
                  stepperExpertInfoList.length == 2) {
                print(
                    'HomePage() : build() : END : Stepper : onStepTapped() : if(TextToDocParameter.isTextTodocGlobal && index == 4 && stepperExpertInfoList.length == 2 ) = $index');
                stepperExpertInfoList.insert(1, StepperExpertInfo());
                stepperExpertInfoList.insert(1, StepperExpertInfo());
              }
              if (TextToDocParameter.isTextTodocGlobal && index < 3) {
                return;
              }
              //end of temporary knob

              _dialogRequestGenerated(
                  context, stepperExpertInfoList[index], title);
            },
            onStepContinue: () {},
            onStepCancel: () {},
            steps: [
              Step(
                title: Text("Question Typed",
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 18.0)),
                subtitle: Text(messageStepperEnterQuestion!),
                state: stateStepperEnterQuestion!, //stateStepperUploaded!,
                isActive: isActiveEnterQuestion!, //isActiveUploaded!,
                content: LimitedBox(
                  maxWidth: screenSize!.width, //100,
                  maxHeight: 40,
                  child: Container(
                      color: Colors.black12, //CupertinoColors.systemGrey,
                      child: Center(
                          child: Padding(
                        padding: const EdgeInsets.only(right: 8, left: 8),
                        child: Text(message!,
                            style: TextStyle(
                                fontWeight: FontWeight.normal,
                                fontSize: 18.0,
                                color: stateStepperEnterQuestion! ==
                                        StepState.complete
                                    ? Colors.green
                                    : Colors.red)),
                      ))),
                ),
              ),
              Step(
                title: Text("SQL Request Generated",
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 18.0)),
                subtitle: Text(messageStepperGenerateSQL!),
                state: stateStepperGenerateSQL!, //stateStepperExtracted!,
                isActive: isActiveGenerateSQL!, //isActiveExtracted!,
                content: LimitedBox(
                  maxWidth: screenSize!.width, //100,
                  maxHeight: 40,
                  child: Container(
                      color: Colors.black12,
                      child: Center(
                        child: Padding(
                          padding: const EdgeInsets.only(right: 8, left: 8),
                          child: Text(message!,
                              style: TextStyle(
                                  fontWeight: FontWeight.normal,
                                  fontSize: 18.0,
                                  color: Colors.green)),
                        ),
                      )),
                ),
              ),
              Step(
                title: Text("Data Retrieved",
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 18.0)),
                subtitle: Text(messageStepperRunQuery!),
                state:
                    stateStepperRunQuery!, //StepState.disabled, //stateStepperCompared!,
                isActive: isActiveRunQuery!, //isActiveCompared!,
                content: LimitedBox(
                  maxWidth: screenSize!.width, //100,
                  maxHeight: 40,
                  child: Container(
                      color: Colors.black12,
                      child: Center(
                          child: Padding(
                        padding: const EdgeInsets.only(right: 8, left: 8),
                        child: Text(message!,
                            style: TextStyle(
                                fontWeight: FontWeight.normal,
                                fontSize: 18.0,
                                color: Colors.green)),
                      ))),
                ),
              ),
              Step(
                title: Text("Graph & Table Generated",
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 18.0)),
                subtitle: Text(messageStepperGraphDescription!),
                state:
                    stateStepperGetGraphDescription!, //StepState.disabled, //stateStepperCompared!,
                isActive: isActiveGetGraphDescription!, //isActiveCompared!,
                content: LimitedBox(
                  maxWidth: screenSize!.width, //100,
                  maxHeight: 40,
                  child: Container(
                      color: Colors.black12,
                      child: Center(
                          child: Padding(
                        padding: const EdgeInsets.only(right: 8, left: 8),
                        child: Text(
                            "The overall time to generate the natural language answer is ${double.parse(overallProcessingTime.toStringAsFixed(2))} s.",
                            style: TextStyle(
                                fontWeight: FontWeight.normal,
                                fontSize: 18.0,
                                color: Colors.green)),
                      ))),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<ui.Image> loadImageAsset(String assetPath) async {
    final ByteData data = await rootBundle.load(assetPath);
    final ui.Codec codec =
        await ui.instantiateImageCodec(data.buffer.asUint8List());
    final ui.FrameInfo frameInfo = await codec.getNextFrame();
    return frameInfo.image;
  }

  Future<List<int>> convertImageToListInt(String assetPath) async {
    ui.Image image = await loadImageAsset(assetPath);
    ByteData? byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    return byteData!.buffer.asUint8List();
  }

  Future<Uint8List> _loadFile(String uri) async {
    final byteData = await rootBundle.load(uri);
    final buffer = byteData.buffer;
    Uint8List bytes =
        buffer.asUint8List(byteData.offsetInBytes, byteData.lengthInBytes);
    return bytes;
  }

  Future<List<List<dynamic>>> importQuestions() async {
    print('Main: ttmd : importQuestions() : START');
    List<List<dynamic>>? rowsAsListOfValues;
    final filePickerResult = await FilePicker.platform.pickFiles(
      allowMultiple: false,
      allowedExtensions: ['csv'],
      type: FileType.custom,
      dialogTitle: "Import questions",
    );

    if (filePickerResult != null) {
      print(
          'Main: ttmd : importQuestions() : fileName = ${filePickerResult.files.single.name}');
      print(
          'Main: ttmd : importQuestions() : size = ${filePickerResult.files.single.size}');
      //print('Main: ttmd : importQuestions() : path = ${filePickerResult.files.single.path}');
      Uint8List fileBytes = filePickerResult.files.single.bytes!;

      String fileContent = utf8.decode(fileBytes);
      List<String> lines = fileContent.split('\n');
      print('Main: ttmd : importQuestions() : lines.length = ${lines.length}');

      rowsAsListOfValues = const CsvToListConverter(
              fieldDelimiter: ',', textDelimiter: '"', textEndDelimiter: '"')
          .convert(fileContent);
      print(
          'Main: ttmd : importQuestions() : rowsAsListOfValues = ${rowsAsListOfValues}');

      if (rowsAsListOfValues!.length < 2 ||
          rowsAsListOfValues[0].length > 4 ||
          (rowsAsListOfValues[0].length <= 4 &&
              (rowsAsListOfValues[0][0] != "user_grouping" ||
                  rowsAsListOfValues[0][1] != "scenario" ||
                  rowsAsListOfValues[0][2] != "question"))) {
        print(
            "Main: importQuestions() : WRONG FORMAT : rowsAsListOfValues[0] = ${rowsAsListOfValues[0]}");
        checkImportedCSVFile();
        return [[]];
      }

      for (var entry in rowsAsListOfValues) {
        if (rowsAsListOfValues[1].length == 4) {
          print(
              "Main: importQuestions() : rowsAsListOfValues = ${entry[0]}, ${entry[2]}, ${entry[3]}");
          if (rowsAsListOfValues[1].length != 4) checkImportedCSVFile();
        }
        if (rowsAsListOfValues[1].length == 3) {
          print(
              "Main: importQuestions() : rowsAsListOfValues = ${entry[0]}, ${entry[2]}");
          if (rowsAsListOfValues[1].length != 3) checkImportedCSVFile();
        }
      }
    }

    return rowsAsListOfValues!;
  }

  void checkImportedCSVFile() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Alert'),
          content: Text(
              "The imported CVS file does not have the right format or any entry.\n" +
                  "Please follow the format below (CVS comma separated):\n" +
                  "grouping,\tscenario,\tquestion\n" +
                  "grouping1,\tscenario1,\tquestion1\n\n" +
                  "For more info, please look at:\n" +
                  "https://github.com/GoogleCloudPlatform/Open_Data_QnA/blob/main/scripts/known_good_sql.csv",
              softWrap: true,
              overflow: TextOverflow.visible), //SwitchExample(),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // Close the dialog
              },
              child: Text('OK'),
            ),
          ],
        );
      },
    );
  }

  void noCfgStoredinFirestore() {
    showDialog(
      context: context, //navigatorKey.currentContext!,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Row(
            // Use a Row to align the icon and title
            children: [
              Icon(Icons.warning, color: Colors.red),
              SizedBox(width: 8), // Add some spacing
              Text('Alert'),
            ],
          ),
          content: SelectableText.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "You must first create and load a configuration file\n" +
                        "using the Settings -> Upload frontend config file option.\n" +
                        'For that, copy and paste the content below in a file\n' +
                        "that you'll name config_frontend.json:\n\n"),
                TextSpan(
                  text: "{\n",
                  style: TextStyle(color: Colors.black),
                ),
                TextSpan(
                  text: '"endpoint_opendataqnq": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '"<URI of the backend endpoint>",\n',
                  style: TextStyle(color: Colors.green),
                ),
                TextSpan(
                  text: '"firestore_database_id": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '"opendataqna-session-logs",\n',
                  style: TextStyle(color: Colors.green),
                ),
                TextSpan(
                  text: '"firestore_history_collection": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '"session_logs",\n',
                  style: TextStyle(color: Colors.green),
                ),
                TextSpan(
                  text: '"firestore_cfg_collection": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '"front_end_flutter_cfg",\n',
                  style: TextStyle(color: Colors.green),
                ),
                TextSpan(
                  text: '"expert_mode": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '<true|false>,\n',
                  style: TextStyle(color: Colors.red),
                ),
                TextSpan(
                  text: '"anonymized_data": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '<true|false>,\n',
                  style: TextStyle(color: Colors.red),
                ),
                TextSpan(
                  text: '"firebase_app_name": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '"opendataqna"\n',
                  style: TextStyle(color: Colors.green),
                ),
                TextSpan(
                  text: '"imported_questions": ',
                  style: TextStyle(color: Colors.blueAccent),
                ),
                TextSpan(
                  text: '"imported_questions"\n',
                  style: TextStyle(color: Colors.green),
                ),
                TextSpan(
                  text: '}',
                  style: TextStyle(color: Colors.black),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // Close the dialog
              },
              child: Text('OK'),
            ),
          ],
        );
      },
    );
  }

  List<TreeNode<String>> createQuestionList(List<List<dynamic>> questionList) {
    List<TreeNode<String>> finalNodeList = [];
    List<TreeNode<String>>? nodeList = [];
    List<TreeNode<String>>? nodeEmbeddedList;
    String scenario_nameCurrent = "";
    int count = 1;
    int countQuestions = 0;
    bool isNewScenario = true;
    String nodeTmp = "";

    print("Main: createQuestionList() : START");
    print(
        "Main: createQuestionList() : questionList.length = ${questionList.length}");
    print(
        "Main: createQuestionList() : questionList[0].length = ${questionList[0].length}");

    for (var entry in questionList)
      print(
          "Main: createQuestionList() : questionList = ${entry[1]}, ${entry[2]}");

    scenario_nameCurrent = (questionList[0][1] as String).trim().toLowerCase();
    nodeTmp = "";

    for (int i = 0; i < questionList.length; i++) {
      print(
          "Main: createQuestionList() : START LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent");

      if (i < questionList.length - 1) {
        print(
            "Main: createQuestionList() : START LOOP : i = $i : $i < ${questionList.length - 1}");
        //We're on the same scenario
        if (scenario_nameCurrent ==
            (questionList[i][1] as String).trim().toLowerCase()) {
          print(
              "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = questionList[i][1] as String).trim().toLowerCase() = $scenario_nameCurrent");

          //processQuestionRow(i);
          if (isNewScenario) {
            print(
                "Main: createQuestionList() : LOOP : i = $i : This is a new sceanrio : isNewScenario = $isNewScenario");
            nodeList = [];
            nodeEmbeddedList = [];

            finalNodeList.add(TreeNode<String>(
                'Scenario $count - ${questionList[i][1]} - ${getQuestionCount(questionList, scenario_nameCurrent)}',
                subNodes: nodeList!));
            isNewScenario = false;
          }
          nodeTmp = "$count:" +
              questionList[i][2] +
              ":" +
              questionList[i][1] +
              ":" +
              questionList[i][0];
          print(
              "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent : nodeTmp = $nodeTmp");

          if ((questionList[i][3] as String).trim().toLowerCase() == "y" &&
              (questionList[i + 1][3] as String).trim().toLowerCase() == "y" &&
              (questionList[i + 1][1] as String).trim().toLowerCase() ==
                  scenario_nameCurrent) {
            print(
                "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()} :  main_question${i + 1} = ${(questionList[i + 1][3] as String).trim().toLowerCase()}");

            nodeList!
                .add(TreeNode<String>(nodeTmp, subNodes: nodeEmbeddedList!));
          } else if ((questionList[i][3] as String).trim().toLowerCase() ==
                  "y" &&
              (questionList[i + 1][1] as String).trim().toLowerCase() !=
                  scenario_nameCurrent) {
            print(
                "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()} :  main_question${i + 1} = ${(questionList[i + 1][3] as String).trim().toLowerCase()} : questionList[i+1][1] = ${questionList[i + 1][1]} != scenario_nameCurrent = $scenario_nameCurrent");

            nodeList!.add(TreeNode<String>(nodeTmp));
          } else if ((questionList[i][3] as String).trim().toLowerCase() ==
                  "y" &&
              (questionList[i + 1][3] as String).trim().toLowerCase() == "n") {
            //this is a new main question
            nodeEmbeddedList = [];
            print(
                "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()} !=  main_question${i + 1} = ${(questionList[i + 1][3] as String).trim().toLowerCase()}");
            /*nodeEmbeddedList!.add(TreeNode<String>("$count:" +
                questionList[i][2] +
                ":" +
                questionList[i][1] +
                ":" +
                questionList[i][0]));
            nodeList!.add(TreeNode<String>(nodeTmp, subNodes: nodeEmbeddedList!));*/
            nodeList!
                .add(TreeNode<String>(nodeTmp, subNodes: nodeEmbeddedList!));
          } else if ((questionList[i][3] as String).trim().toLowerCase() ==
                  "n" &&
              (questionList[i + 1][3] as String).trim().toLowerCase() == "n") {
            //this is a follow-up question
            print(
                "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()} ==  main_question${i + 1} = ${(questionList[i + 1][3] as String).trim().toLowerCase()}");
            nodeEmbeddedList!.add(TreeNode<String>("$count:" +
                questionList[i][2] +
                ":" +
                questionList[i][1] +
                ":" +
                questionList[i][0]));
          } else if ((questionList[i][3] as String).trim().toLowerCase() ==
                  "n" &&
              (questionList[i + 1][3] as String).trim().toLowerCase() == "y") {
            //this is a new main question
            print(
                "Main: createQuestionList() : LOOP : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()} ==  main_question${i + 1} = ${(questionList[i + 1][3] as String).trim().toLowerCase()}");
            nodeEmbeddedList!.add(TreeNode<String>("$count:" +
                questionList[i][2] +
                ":" +
                questionList[i][1] +
                ":" +
                questionList[i][0]));
          }
        } else {
          print(
              "Main: createQuestionList() : i = $i : $scenario_nameCurrent != ${questionList[i][1]} : countQuestions = $countQuestions");
          isNewScenario = true;
          count++;

          //processQuestionRow(i);

          nodeList = [];
          nodeEmbeddedList = [];

          finalNodeList.add(TreeNode<String>(
              'Scenario $count - ${questionList[i][1]} - ${getQuestionCount(questionList, questionList[i][1])}',
              subNodes: nodeList!));
          isNewScenario = false;

          nodeTmp = "$count:" +
              questionList[i][2] +
              ":" +
              questionList[i][1] +
              ":" +
              questionList[i][0];
          print(
              "Main: createQuestionList() : i = $i : $scenario_nameCurrent != ${questionList[i][1]}  : nodeTmp = $nodeTmp");
          nodeList!.add(TreeNode<String>(nodeTmp, subNodes: nodeEmbeddedList!));
          scenario_nameCurrent =
              (questionList[i][1] as String).trim().toLowerCase();
          print(
              "Main: createQuestionList() : i = $i : new scenario_nameCurrent = $scenario_nameCurrent ");
        }
      } //end of if i < questionList.length - 1

      else if (i == questionList.length - 1) {
        print(
            "Main: createQuestionList() : LOOP : Last row : i = $i : i = ${questionList.length - 1}");
        if ((questionList[i][3] as String).trim().toLowerCase() == "y") {
          print(
              "Main: createQuestionList() : LOOP : Last row : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()}");

          //nodeList!.add(TreeNode<String>(nodeTmp, subNodes: nodeEmbeddedList!));
          nodeList!.add(TreeNode<String>("$count:" +
              questionList[i][2] +
              ":" +
              questionList[i][1] +
              ":" +
              questionList[i][0]));
        } else {
          //this is a new main question
          //nodeEmbeddedList = [];
          print(
              "Main: createQuestionList() : LOOP : Last row : i = $i : scenario_nameCurrent = $scenario_nameCurrent : main_question$i = ${(questionList[i][3] as String).trim().toLowerCase()}");
          nodeEmbeddedList!.add(TreeNode<String>("$count:" +
              questionList[i][2] +
              ":" +
              questionList[i][1] +
              ":" +
              questionList[i][0]));
        }
      }
    } //end of for

    print("Main: createQuestionList() : END : count = $count");
    return finalNodeList;
  }

  int getQuestionCount(List<List<dynamic>> questionList, String scenario) {
    int scenarioCount = 0;
    bool hit = false;

    print("Main: getQuestionCount() : START ");

    for (int i = 0; i < questionList.length; i++) {
      if (scenario.toLowerCase() ==
          (questionList[i][1] as String).trim().toLowerCase()) {
        hit = true;
        scenarioCount++;
      } else {
        if (hit) break;
      }
    }

    print("Main: getQuestionCount() : scenarioCount = $scenarioCount");
    return scenarioCount;
  }

  Future<List<Map<String, dynamic>>> _getLastQuestions() async {
    List<Map<String, dynamic>> resp = [];

    print("Main : _getLastQuestions() : START");
    print(
        'Main : _getLastQuestions() : TextToDocParameter.userID = ${TextToDocParameter.userID}');

    print('Main : _getLastQuestions() : db = ${db}');
    print('Main : _getLastQuestions() : db.app = ${db.app}');
    print('Main : _getLastQuestions() : db.databaseId = ${db.databaseId}');

    var querySnapshot = await db
        .collection("session_logs")
        .where("user_id", isEqualTo: TextToDocParameter.userID)
        .limit(4)
        .orderBy('timestamp', descending: true)
        .get();

    print(
        "Main : _getLastQuestions() : querySnapshot.docs.length = ${querySnapshot.docs.length}");
    print("Main : _getLastQuestions() : querySnapshot = ${querySnapshot}");
    for (var docSnapshot in querySnapshot.docs) {
      print(
          'Main : _getLastQuestions() : ${docSnapshot.id} => ${docSnapshot.data()}');
      resp.add({
        "user_question": "${docSnapshot.data()['user_question']}",
        "timestamp":
            "${DateTime.fromMillisecondsSinceEpoch(docSnapshot.data()['timestamp'].seconds * 1000)}",
        "user_grouping":
            "${docSnapshot.data().containsKey('user_grouping') ? docSnapshot.data()['user_grouping'] : 'no data'}",
        "scenario_name":
            "${docSnapshot.data().containsKey('scenario_name') ? docSnapshot.data()['scenario_name'] : 'no data'}"
      });
    }
    return resp;
  }

  Future<List<String>> _getLastQuestionsOld(String userGrouping) async {
    List<String> respLLMQuestion = [];
    List<String> respCannedQuestions = [];
    List<String> resp = [];
    List<String> tmpQuestions = [];
    String body = "";
    Uri url;
    String question1 = "";
    String question2 = "";
    String question3 = "";
    String question4 = "";
    String timeString = "";
    String originalQuestion = "";

    print(
        'NewSuggestionCubit : getLastQuestions() : generateNewSuggestions : START');
    print(
        'NewSuggestionCubit : getLastQuestions() : userGrouping = $userGrouping');

    timeString = displayDateTime();

    //Create the header
    Map<String, String>? _headers = {
      "Content-Type": "application/json",
      //"Authorization": " Bearer ${client!.credentials.accessToken.toString()}",
    };

    //Create the body
    body = '''{
          "user_grouping": "$userGrouping"
      }''';

    try {
      var response = await html.HttpRequest.requestCrossOrigin(
          '${TextToDocParameter.endpoint_opendataqnq}/get_known_sql',
          method: "POST",
          sendData: body);

      print('NewSuggestionCubit : getLastQuestions() : response = ' +
          response.toString());

      final jsonData = jsonDecode(response);

      if (jsonData != null) {
        print('NewSuggestionCubit: getLastQuestions() : jsonData = $jsonData');

        //KnownSQL = [{"example_user_question": "question1", "example_generated_sql": "sql1"},
        // {"example_user_question": "question2", "example_generated_sql": "sql2"},
        // ...]

        var knownSql =
            jsonData["KnownSQL"].replaceAll(RegExp(r'((\\n)|(\\r))'), '');

        var knownSqlMap = jsonDecode(knownSql);

        print(
            'NewSuggestionCubit: getLastQuestions() : knownSqlMap = ${knownSqlMap}');

        print(
            'NewSuggestionCubit: getLastQuestions() : knownSqlMap[0] = ${knownSqlMap[0].toString()}');

        for (int i = 0; i < knownSqlMap.length; i++) {
          for (var entry in knownSqlMap[i].entries) {
            print('${entry.key} : ${entry.value}');
            if (entry.key == "example_user_question")
              tmpQuestions.add(entry.value);
          }
        }

        print('Main: getLastQuestions() : tmpQuestions = ${tmpQuestions}');

        question1 = tmpQuestions[0] ?? "No suggestion for question1";
        question2 = tmpQuestions[1] ?? "No suggestion for question2";
        question3 = tmpQuestions[2] ?? "No suggestion for question3";
        question4 = tmpQuestions[3] ?? "No suggestion for question4";

        //Adding scenarioNumber + ":" to have same format as for Business KPI questions
        question1 = "2:" + question1;
        question2 = "2:" + question2;
        question3 = "2:" + question3;
        question4 = "2:" + question4;

        print('Main: getLastQuestions() : question1 = ${question1}');
        print('Main: getLastQuestions() : question2 = ${question2}');
        print('Main: getLastQuestions() : question3 = ${question3}');
        print('Main: getLastQuestions() : question4 = ${question4}');
      }
    } catch (e) {
      print(
          'Main: getLastQuestions() : Not a canned question : EXCEPTION = $e');
      throw Exception('Failed to get earning calls question suggestions: $e');
    } finally {
      resp.add(question1);
      resp.add(question2);
      resp.add(question3);
      resp.add(question4);

      print('Main: getLastQuestions() : resp = $resp');
      return resp;
    }
  }

  void SaveImportedQuestionsToFirestore(
      List<List<dynamic>> questionList) async {
    int count = 0;

    print('Main: SaveImportedQuestionsToFirestore() : START');
    print(
        'Main: SaveImportedQuestionsToFirestore() : questionList = $questionList');

    if (questionList.length > 0) {
      try {
        //Delete all former questions for that user
        var querySnapshot = await db!
            .collection("${TextToDocParameter.imported_questions}")
            .where("user_id", isEqualTo: TextToDocParameter.userID)
            .get();

        for (var docSnapshot in querySnapshot.docs) {
          db.collection("imported_questions").doc('${docSnapshot.id}').delete();
        }

        //create new questions to be stored on Firestore
        for (int i = 0; i < questionList.length; i++) {
          List list = questionList[i];

          print('Main: SaveImportedQuestionsToFirestore() : List = $List');

          Map<String, dynamic> questionMap = {};

          questionMap['user_grouping'] = list[0];
          questionMap['scenario'] = list[1];
          questionMap['question'] = list[2];
          questionMap['user_id'] = TextToDocParameter.userID;
          if (list.length == 4)
            questionMap['main_question'] = list[3];
          else
            questionMap['main_question'] = "Y";

          questionMap['order'] = count++;

          db
              .collection("imported_questions")
              .doc("question$i")
              .set(questionMap);
        }
      } catch (e) {
        print('Main: SaveImportedQuestionsToFirestore() : EXCEPTION : e = $e');
      }
    }
  }
}

class Config {
  static bool isUseFeedback = false;
  static bool isUseColorMode = false;
  static bool isUseDashboards = false;
  static bool isUseReports = false;
  static bool isExpert = false;
  static bool isUseLog = false;
  static bool isAnonymizedMode = false;
}
