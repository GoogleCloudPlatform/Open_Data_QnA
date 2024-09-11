import 'dart:convert';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_settings_ui/flutter_settings_ui.dart';
import 'package:flutter/material.dart';
import '../services/display_stepper/display_stepper_cubit.dart';
import '../utils/TextToDocParameter.dart';
import 'package:flutter/services.dart';

class Settings extends StatefulWidget {
  Settings(FirebaseFirestore this.db, {Key? key}) : super(key: key);
  bool useFeedback = false;
  bool useColorMode = false;
  bool useDashboards = false;
  bool useReports = false;
  bool useExpertMode = false;
  bool useLog = false;
  bool useAnonymizedMode = false;
  static bool isLoadConfig = false;
  static bool isUseFeedback = false;
  static bool isUseColorMode = false;
  static bool isUseDashboards = false;
  static bool isUseReports = false;
  static bool isExpert = false;
  static bool isUseLog = false;
  static bool isAnonymizedMode = false;
  FirebaseFirestore db;

  @override
  State<Settings> createState() => SettingsState();
}

class SettingsState extends State<Settings> {
  @override
  Widget build(BuildContext context) {
    print("Settings : build() : START");
    print("Settings : build() : widget.db = ${widget.db}");

    return Scaffold(
      appBar: AppBar(
        title: Text('Open data QnA',
            style:
                TextStyle(fontWeight: FontWeight.bold, color: Colors.purple)),
        centerTitle: false,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            Navigator.pop(context, Settings.isExpert);
          },
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 100),
            child: IconButton(
              icon: Image.asset('assets/images/cymbal_logo.png'),
              onPressed: () {
                ;
              },
            ),
          ),
        ],
      ),
      body: SettingsList(
        sections: [
          SettingsSection(
            title: Text('General',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            tiles: [
              SettingsTile.switchTile(
                initialValue: TextToDocParameter.isLoadConfig,
                onToggle: (value) {
                  setState(() {
                    //Settings.isLoadConfig = value;
                    TextToDocParameter.isLoadConfig = value;
                    print(
                        "Settings : build() : TextToDocParameter.isLoadConfig = ${TextToDocParameter.isLoadConfig}");

                    importFrontEndCfgFile();
                  });
                },
                title: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    Image.asset(
                      'assets/images/config_frontend.png',
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    Container(width: 20),
                    Text('Upload frontend config file'),
                  ],
                ),
                description: Text("Set required app's parameters"),
              ),
              SettingsTile.switchTile(
                initialValue: widget.useFeedback,
                onToggle: (value) {
                  setState(() {
                    //useFeedback = value;
                  });
                },
                title: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    Image.asset(
                      'assets/images/feedback.png',
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    Container(width: 20),
                    Text('Feedback (not implemented yet)'),
                  ],
                ),
                description: Text('Send feedback on generated answers'),
              ),
              SettingsTile.switchTile(
                  initialValue: widget.useColorMode,
                  onToggle: (value) {
                    setState(() {
                      //useColorMode = value;
                    });
                  },
                  title: Row(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      Image.asset(
                        'assets/images/color_mode.png',
                        height: 70,
                        width: 70,
                        fit: BoxFit.cover,
                      ),
                      Container(width: 20),
                      Text('Enable dark mode (not implemented yet)'),
                    ],
                  )),
              SettingsTile.switchTile(
                  initialValue: TextToDocParameter.anonymized_data,//Settings.isAnonymizedMode,
                  onToggle: (value) {
                    setState(() {
                      //Settings.isAnonymizedMode = value;
                      TextToDocParameter.anonymized_data = value;
                      //print("Settings : build() : widget.useExpertMode = ${widget.useExpertMode}");
                      print(
                          "Settings : build() : TextToDocParameter.anonymized_data = ${TextToDocParameter.anonymized_data}");
                      updateFrontEndFlutterCfg(parameter: "anonymized_data", value: value);
                    });
                  },
                  title: Row(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      Image.asset(
                        'assets/images/anonymized.jpeg',
                        height: 70,
                        width: 70,
                        fit: BoxFit.cover,
                      ),
                      Container(width: 20),
                      Text('Enable anonymization of data'),
                    ],
                  )),
            ],
          ),
          SettingsSection(
            title: Text('Statistics',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            tiles: [
              SettingsTile.switchTile(
                initialValue: widget.useDashboards,
                onToggle: (value) {
                  setState(() {
                    //useDashboards = value;
                  });
                },
                title: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    Image.asset(
                      'assets/images/statistics.png',
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    Container(width: 20),
                    Text('Dashboards (not implemented yet)'),
                  ],
                ),
                description: Text('Get visibility on activities'),
              ),
              SettingsTile.switchTile(
                initialValue: widget.useReports,
                onToggle: (value) {
                  setState(() {
                    //useReports = value;
                  });
                },
                title: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    Image.asset(
                      'assets/images/reports.png',
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    Container(width: 20),
                    Text('Reports (not implemented yet)'),
                  ],
                ),
                description: Text('Export activity reports in pdf'),
              ),
            ],
          ),
          SettingsSection(
            title: Text('Troubleshooting',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            tiles: [
              SettingsTile.switchTile(
                initialValue: TextToDocParameter.expert_mode,//Settings.isExpert,
                onToggle: (value) {
                  setState(() {
                    //widget.useExpertMode = value;
                    //Settings.isExpert = value;
                    TextToDocParameter.expert_mode = value;
                    //Config.isExpert = value;
                    //print("Settings : build() : widget.useExpertMode = ${widget.useExpertMode}");
                    print(
                        "Settings : build() : TextToDocParameter.expert_mode = ${TextToDocParameter.expert_mode}");
                    BlocProvider.of<DisplayStepperCubit>(context).displayStepper(value);
                  });

                  updateFrontEndFlutterCfg(parameter: "expert_mode", value: value);
                },
                title: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    Image.asset(
                      'assets/images/troubleshooting.png',
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    Container(width: 20),
                    Text('Expert mode'),
                  ],
                ),
                description: Text(
                    'Get workflow details and internal technical informations'),
              ),
              SettingsTile.switchTile(
                initialValue: widget.useLog,
                onToggle: (value) {
                  setState(() {
                    //useLog = value;
                  });
                },
                title: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    Image.asset(
                      'assets/images/logs.png',
                      height: 70,
                      width: 70,
                      fit: BoxFit.cover,
                    ),
                    Container(width: 20),
                    Text('Enable logs (not implemented yet)'),
                  ],
                ),
                description: Text('Generate logs for troubleshooting'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void importFrontEndCfgFile() async {
    print('Settings: importFrontEndCfgFile() : START');
    List<List<dynamic>>? rowsAsListOfValues;
    final filePickerResult = await FilePicker.platform.pickFiles(
      allowMultiple: false,
      allowedExtensions: ['json'],
      type: FileType.custom,
      dialogTitle: "Import Frontend json Config File",
    );

    if (filePickerResult != null) {
      print(
          'Settings: importFrontEndCfgFile() : fileName = ${filePickerResult.files.single.name}');
      print(
          'Settings: importFrontEndCfgFile() : size = ${filePickerResult.files.single.size}');
      //print('Settings: importFrontEndCfgFile() : path = ${filePickerResult.files.single.path}');
      Uint8List fileBytes = filePickerResult.files.single.bytes!;

      String fileContent = utf8.decode(fileBytes);

      print('Settings: importFrontEndCfgFile() : fileContent = ${fileContent}');

      var cfg = jsonDecode(fileContent);

      print('Settings: importFrontEndCfgFile() : cfg = ${cfg}');

      if (cfg != null) {
        setState(() {
          TextToDocParameter.isLoadConfig = false;
          TextToDocParameter.anonymized_data = cfg["anonymized_data"];
          TextToDocParameter.expert_mode = cfg["expert_mode"];
          TextToDocParameter.endpoint_opendataqnq = cfg["endpoint_opendataqnq"];
          TextToDocParameter.firestore_database_id = cfg["firestore_database_id"];
          TextToDocParameter.firebase_app_name = cfg["firebase_app_name"];
          TextToDocParameter.firestore_history_collection = cfg["firestore_history_collection"];
          TextToDocParameter.firestore_cfg_collection = cfg["firestore_cfg_collection"];
          TextToDocParameter.imported_questions = cfg["imported_questions"];
        });

        if (TextToDocParameter.anonymized_data != null &&
            TextToDocParameter.expert_mode != null &&
            TextToDocParameter.endpoint_opendataqnq != null &&
            TextToDocParameter.firestore_database_id != null &&
            TextToDocParameter.firebase_app_name != null &&
            TextToDocParameter.firestore_history_collection != null &&
            TextToDocParameter.firestore_cfg_collection != null &&
            TextToDocParameter.imported_questions != null
        ) {
          print('Settings: importFrontEndCfgFile() : Trying to update front_end_flutter_cfg');
          try {
            widget.db
                .collection("${TextToDocParameter.firestore_cfg_collection}")
                .doc('${TextToDocParameter.userID}')
                .set({
              "endpoint_opendataqnq":
                  "${TextToDocParameter.endpoint_opendataqnq}",
              "firestore_database_id":
                  "${TextToDocParameter.firestore_database_id}",
              "expert_mode": TextToDocParameter.expert_mode,
              "anonymized_data": TextToDocParameter.anonymized_data,
              "firebase_app_name": "${TextToDocParameter.firebase_app_name}",
              "firestore_history_collection": "${TextToDocParameter.firestore_history_collection}",
              "firestore_cfg_collection": "${TextToDocParameter.firestore_cfg_collection}",
              "imported_questions": "${TextToDocParameter.imported_questions}"
            });

            showSuccessfulUploadMsg();

          } catch (e) {
            print('Settings: importFrontEndCfgFile() : EXCEPTION : ${e}');
            displayCfgUploadErrorMsg();
          }
        } else {
          print('Settings: importFrontEndCfgFile() : some fields if cfg are null, could not update firestore_cfg_collection');
          displayCfgUploadErrorMsg();
        }
      }
    }
  }

  void showSuccessfulUploadMsg() {
    showDialog(
      context: context,//navigatorKey.currentContext!,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Row( // Use a Row to align the icon and title
            children: [
              Icon(Icons.info, color: Colors.blueAccent),
              SizedBox(width: 8), // Add some spacing
              Text('Information'),
            ],
          ),
          content: Text('The json configuration file has been\nuploaded successfully to Firestore.'),
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

  void displayCfgUploadErrorMsg() {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Row( // Use a Row to align the icon and title
            children: [
              Icon(Icons.warning, color: Colors.red),
              SizedBox(width: 8), // Add some spacing
              Text('Alert'),
            ],
          ),
          content: SelectableText.rich(
            TextSpan(
              children: [
                TextSpan(text: "Please check you have uploaded a config_frontend.json\n" +
                    "file similar as the one below:\n\n"),
                TextSpan(text: "{\n", style: TextStyle(color: Colors.black),),
                TextSpan(text:'"endpoint_opendataqnq": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'"<URI of the backend endpoint>",\n', style: TextStyle(color: Colors.green),),
                TextSpan(text:'"firestore_database_id": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'"opendataqna-session-logs",\n', style: TextStyle(color: Colors.green),),
                TextSpan(text:'"firestore_history_collection": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'"session_logs",\n', style: TextStyle(color: Colors.green),),
                TextSpan(text:'"firestore_cfg_collection": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'"front_end_flutter_cfg",\n', style: TextStyle(color: Colors.green),),
                TextSpan(text:'"expert_mode": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'<true|false>,\n', style: TextStyle(color: Colors.red),),
                TextSpan(text:'"anonymized_data": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'<true|false>,\n', style: TextStyle(color: Colors.red),),
                TextSpan(text:'"firebase_app_name": ', style: TextStyle(color: Colors.blueAccent),),
                TextSpan(text:'"opendataqna"\n', style: TextStyle(color: Colors.green),),
                TextSpan(text:'}', style: TextStyle(color: Colors.black),),
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

  void updateFrontEndFlutterCfg({required String parameter, required bool value}) {
    print("Settings : updateFrontEndFlutterCfg() : START");
    print("Settings : updateFrontEndFlutterCfg() : widget.db = ${widget.db}");
    print("Settings : updateFrontEndFlutterCfg() : parameter = ${parameter}");
    print("Settings : updateFrontEndFlutterCfg() : value = ${value}");

    print(
        'Settings: updateFrontEndFlutterCfg() : TextToDocParameter.firestore_cfg_collection = ${TextToDocParameter.firestore_cfg_collection}');
    print(
        'Settings: updateFrontEndFlutterCfg() : TextToDocParameter.userID = ${TextToDocParameter.userID}');

    //update the document in front_end_flutter_cfg collection corresponding to the user_id to refelect the chnage of the TextToDocParameter.expert_mode parameter
    try {
      widget.db!
          .collection("${TextToDocParameter.firestore_cfg_collection}")
          .doc('${TextToDocParameter.userID}')
          .set(
          {"$parameter": value},
          SetOptions(merge: true));

      print(
          'Settings: updateFrontEndFlutterCfg() : update firestore_history_collection.expert_mode successfully:  parameter = $parameter : value = $value');

    } catch (e) {
      print(
          'Settings: updateFrontEndFlutterCfg() : update firestore_history_collection.expert_mode : EXCEPTION : $e');
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

  @override
  String toString() {
    return isExpert.toString();
  }
}
