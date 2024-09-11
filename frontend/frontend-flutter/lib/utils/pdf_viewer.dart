import 'package:flutter/material.dart';
import 'package:flutter/services.dart';


//Not a usable class to display PDF files.
//I keep it though as a stub for future development

class PdfViewer extends StatefulWidget {
  final List<int> bytes;
  PdfViewer({super.key, required this.bytes});
  @override
  _PdfViewerState createState() => _PdfViewerState();
}

class _PdfViewerState extends State<PdfViewer> {

  @override
  initState() {
    print('_PdfViewerState : initState() : START');
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    print('_PdfViewerState : build() : START');

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'PDFViewer',
      theme: ThemeData(
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.white,
        ),
      ),
      home: Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: Icon(Icons.arrow_back),
            onPressed: () {
              Navigator.pop(context);
            },
          ),
          title: Text('mySummaryDoc.pdf'),
          actions: <Widget>[
            IconButton(
              icon: Icon(
                Icons.search,
                color: Colors.black,
              ),
              onPressed: () {

              },
            ),
          ],
        ),
        body: Center(
          child: Container(
              child: Text("Needs to be impemented")),
        ),
      ),
    );
  }
}
