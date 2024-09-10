import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import '../utils/TextToDocParameter.dart';

late String firstName;
late String lastName;
late String userID;

class Disclaimer extends StatefulWidget {
  late final FirebaseAuth auth;

  Disclaimer(this.auth, {super.key});

  @override
  State<Disclaimer> createState() => DisclaimerState();
}

class DisclaimerState extends State<Disclaimer> {
  bool isChecked = false;
  bool isButtonClicked = false;

  Color _buttonColor = Colors.blueAccent;

  @override
  Widget build(BuildContext context) {
    Size screenSize = MediaQuery.sizeOf(context);

    return Material(
      child: !isButtonClicked
          ? Container(
              //height: screenSize.height,
              color: Colors.black,
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(left: 35.0, right: 35.0, top: 35.0, bottom: 35.0),
                      child: Text('Google Cloud | Applied AI Engineering',
                          style: TextStyle(fontSize: 20, color: Colors.white)),
                    ),
                    Padding(
                      padding: const EdgeInsets.only(left: 95.0, top: 0),
                      child: Container(
                          width: screenSize!.width / 2,
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            mainAxisAlignment: MainAxisAlignment.start,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Open Data QnA',
                                  style: TextStyle(
                                      fontSize: 70,
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold)),
                              Padding(
                                padding: const EdgeInsets.only(top: 5),
                                child: Text('Demo',
                                    style: TextStyle(
                                        fontSize: 40, color: Colors.white)),
                              ),
                              Padding(
                                padding: const EdgeInsets.only(top: 15.0),
                                child: Text(
                                    'User Journey | Architecture Diagram | GCP Console Demo',
                                    style: TextStyle(
                                        fontSize: 23, color: Colors.white)),
                              ),
                              Padding(
                                  padding: const EdgeInsets.only(top: 15.0),
                                  child: Divider()),
                              Text(
                                  'This is a functioning solution demo for CEs/FSRs to present to prospects to demonstrate the capabilities of Google Cloud AI products.\n\n'
                                  'It is not an officially supported Google Cloud product or service and is provided without any guarantees of performance or maintenance. Because of the tool\'s limited and experimental nature, we may need to make modifications to, including potentially taking down, the tool on short, or no, notice.\n\n'
                                  'You may provide feedback and suggestions about this tool to Google, and Google and its Affiliates may use any feedback or suggestions provided without restriction and without obligation to you.\n\n'
                                  'Your use of the tool must always comply with our Terms of Service (including the Acceptable Use Policy), or the offline variant of the terms that govern your use of the Google Cloud Platform Services.\n\n'
                                  'During your use of the tool, information is provided for informational purposes only. The data inputed are dummy data.\n\n',
                                  maxLines: null,
                                  style: TextStyle(
                                      fontSize: 18,
                                      color: Colors.white,
                                      height: 1.2)),
                              CheckboxListTile(
                                title: Text(
                                    "By checking this box, you accept and agree to the above terms and conditions of this tool.",
                                    style: TextStyle(
                                        fontSize: 18, color: Colors.white)),
                                value: isChecked,
                                onChanged: (bool? newValue) {
                                  setState(() {
                                    isChecked = newValue!;
                                  });
                                },
                                controlAffinity:
                                    ListTileControlAffinity.leading,
                                checkColor: Colors.white,
                                activeColor: Colors.purple,
                                tileColor: Colors.white,
                                contentPadding: EdgeInsets.zero,
                              ),
                              Padding(
                                padding: const EdgeInsets.only(top: 15.0, bottom: 15.0),
                                child: ElevatedButton(
                                  onPressed: () {
                                    setState(() {
                                      isButtonClicked = true;
                                    });
                                  },
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: isChecked
                                        ? Colors.blue
                                        : Colors.blueAccent,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius
                                          .zero, // Ensures sharp corners
                                    ),
                                  ),
                                  child: Text('Accept and Agree',
                                      style: TextStyle(
                                          color: isChecked
                                              ? Colors.white
                                              : Colors.grey,
                                          fontSize: 18)),
                                ),
                              )
                            ],
                          )),
                    ),
                  ],
                ),
              ),
            )
          :
          /*Container(
            //height: screenSize.height,
              color: Colors.black,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.all(35.0),
                    child: Text('Google Cloud | Applied AI Engineering',
                        style: TextStyle(fontSize: 20, color: Colors.white)),
                  ),
                  Padding(
                    padding: const EdgeInsets.only(left: 95.0, top: 50),
                    child: Container(
                        width: screenSize!.width / 2,
                        child: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            mainAxisAlignment: MainAxisAlignment.start,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Open Data QnA',
                                  style: TextStyle(
                                      fontSize: 70,
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold)),
                              Padding(
                                padding: const EdgeInsets.only(top: 5),
                                child: Text('Demo',
                                    style: TextStyle(
                                        fontSize: 40, color: Colors.white)),
                              ),
                              Padding(
                                padding: const EdgeInsets.only(top: 15.0),
                                child: Text(
                                    'User Journey | Architecture Diagram | GCP Console Demo',
                                    style: TextStyle(
                                        fontSize: 23, color: Colors.white)),
                              ),
                              Padding(
                                  padding: const EdgeInsets.only(top: 15.0),
                                  child: Divider()),
                              Text(
                                  'This is a functioning solution demo for CEs/FSRs to present to prospects to demonstrate the capabilities of Google Cloud AI products.\n\n'
                                  'It is not an officially supported Google Cloud product or service and is provided without any guarantees of performance or maintenance. Because of the tool\'s limited and experimental nature, we may need to make modifications to, including potentially taking down, the tool on short, or no, notice.\n\n'
                                  'You may provide feedback and suggestions about this tool to Google, and Google and its Affiliates may use any feedback or suggestions provided without restriction and without obligation to you.\n\n'
                                  'Your use of the tool must always comply with our Terms of Service (including the Acceptable Use Policy), or the offline variant of the terms that govern your use of the Google Cloud Platform Services.\n\n'
                                  'During your use of the tool, information is provided for informational purposes only. The data inputed are dummy data.\n\n',
                                  maxLines: null,
                                  style: TextStyle(
                                      fontSize: 18,
                                      color: Colors.white,
                                      height: 1.2)),
                              CheckboxListTile(
                                title: Text(
                                    "By checking this box, you accept and agree to the above terms and conditions of this tool.",
                                    style: TextStyle(
                                        fontSize: 18, color: Colors.white)),
                                value: isChecked,
                                onChanged: (bool? newValue) {
                                  setState(() {
                                    isChecked = newValue!;
                                  });
                                },
                                controlAffinity: ListTileControlAffinity.leading,
                                checkColor: Colors.white,
                                activeColor: Colors.purple,
                                tileColor: Colors.white,
                                contentPadding: EdgeInsets.zero,
                              ),
                              Padding(
                                padding: const EdgeInsets.only(top: 15.0),
                                child: ElevatedButton(
                                  onPressed: () {
                                    setState(() {
                                      isButtonClicked = true;
                                    });
                                  },
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: isChecked
                                        ? Colors.blue
                                        : Colors.blueAccent,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius
                                          .zero, // Ensures sharp corners
                                    ),
                                  ),
                                  child: Text('Accept and Agree',
                                      style: TextStyle(
                                          color: isChecked
                                              ? Colors.white
                                              : Colors.grey,
                                          fontSize: 18)),
                                ),
                              )
                            ],
                          ),
                        )),
                  ),
                ],
              ),
            )*/
          Container(
              color: Colors.black,
              child: Center(
                child: Container(
                  //width: screenSize.width / 3,
                  height: screenSize.height / 6,
                  decoration: BoxDecoration(
                    // Background color
                    color: Colors.white,
                    borderRadius:
                        BorderRadius.circular(20.0), // 10-pixel rounded corners
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 15.0),
                        child: ElevatedButton(
                          onPressed: () {
                            firebaseAuthentication();
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Color(0xFFeeecec),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero,
                            ),
                            side: BorderSide(
                              width: 1.0,
                              color: Colors.black,
                            ),
                          ),
                          child: Row(
                            // Use a Row to arrange the icon and text
                            mainAxisSize: MainAxisSize
                                .min, // Make the Row as small as its children
                            children: [
                              Image.asset(
                                'assets/images/google_icon.png',
                                width: 25,
                                height: 25,
                                fit: BoxFit.scaleDown,
                              ), // Replace with your image path
                              SizedBox(
                                  width:
                                      8), // Add some spacing between the icon and text
                              Text('Sign in with Google',
                                  style: TextStyle(
                                      color: Colors.black, fontSize: 14))
                            ],
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(
                            right: 40.0, left: 40.0, top: 20, bottom: 30),
                        child: Text('To use this demo, you have to sign in',
                            style:
                                TextStyle(color: Colors.black, fontSize: 16)),
                      ),
                    ],
                  ),
                ),
              ),
            ),
    );
  }

  Future<UserCredential> signInWithGoogle() async {
    print('Disclaimer: signInWithGoogle() : START');
    // Create a new provider
    GoogleAuthProvider googleProvider = GoogleAuthProvider();

    googleProvider
        .addScope('https://www.googleapis.com/auth/contacts.readonly');
    googleProvider.setCustomParameters({'login_hint': 'user@example.com'});

    // Once signed in, return the UserCredential
    //return await FirebaseAuth.instance.signInWithPopup(googleProvider);
    return await widget.auth.signInWithPopup(googleProvider);
  }

  Future<String?> firebaseAuthentication() async {
    print('Disclaimer: firebaseAuthentication() : START');
    print('Disclaimer: firebaseAuthentication() : auth= ${widget.auth}');
    String? res = null;
    try {
      final credential = await signInWithGoogle();

      print('Disclaimer: firebaseAuthentication() : credential = $credential');
      final user = credential.user;

      print('Disclaimer: firebaseAuthentication() : user.uid = ${user!.uid}.');

      print(
          'Disclaimer: firebaseAuthentication() : credential.additionalUserInfo.profile["given_name"] = ${credential.additionalUserInfo!.profile!["given_name"]}');
      print(
          'Disclaimer: firebaseAuthentication() : credential.additionalUserInfo.profile["family_name"] = ${credential.additionalUserInfo!.profile!["family_name"]}');

      TextToDocParameter.firstName =
          credential.additionalUserInfo!.profile!["given_name"];
      TextToDocParameter.lastName =
          credential.additionalUserInfo!.profile!["family_name"];
      TextToDocParameter.email =
          credential.additionalUserInfo!.profile!["email"];
      TextToDocParameter.userID = credential.user!.uid;
      TextToDocParameter.picture =
          credential.additionalUserInfo!.profile!["picture"];

      print(
          'Disclaimer: firebaseAuthentication() : TextToDocParameter.userID = ${TextToDocParameter.userID}');

      TextToDocParameter.isAuthenticated = true;
      print(
          "Disclaimer: firebaseAuthentication() : TextToDocParameter.isAuthenticated = ${TextToDocParameter.isAuthenticated}");

      print('Disclaimer: firebaseAuthentication() : user?.uid = ${user?.uid}');
      print(
          'Disclaimer: firebaseAuthentication() : email = ${TextToDocParameter.email}');
      print(
          'Disclaimer: firebaseAuthentication() : picture = ${TextToDocParameter.picture}');

      Navigator.of(context).pushReplacementNamed('/landingPage');
    } on FirebaseAuthException catch (e) {
      if (e.code == 'user-not-found') {
        print('Disclaimer: firebaseAuthentication() : User does not exists');
        res = 'User does not exists';
        return res;
      } else if (e.code == 'wrong-password') {
        print('Disclaimer: firebaseAuthentication() : Password does not match');
        res = 'Password does not match';
        return res;
      } else {
        print('Disclaimer: firebaseAuthentication() : ${e.code}');
        print('Disclaimer: firebaseAuthentication() : ${e.message}');
        res = e.message;
        return res;
      }
    }
  }
}
