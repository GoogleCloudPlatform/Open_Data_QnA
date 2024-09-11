class TextToDocParameter {
  static bool isTextTodocGlobal = false;
  static bool isAuthenticated = false;
  static bool anonymized_data = false;

  static int lastScenarioNumber = 0;
  static String lastCannedQuestion = "";
  static String sessionId = "";
  static String userID = "";
  static String currentUserGrouping = "";
  static String currentScenarioName = "";
  static String email = "";
  static String firstName = "";
  static String lastName = "";
  static String picture = "";
  static bool isLoadConfig = false;
  static bool expert_mode = false;
  static String endpoint_opendataqnq = "";
  static String firebase_app_name = "";
  static String firestore_database_id = "";
  static String firestore_history_collection = "";
  static String firestore_cfg_collection = "";
  static String imported_questions = "";
  static int questionCount = 1;
  static List<String> suggestionsList = [];
  static List<String> userGroupingList = [];

}
