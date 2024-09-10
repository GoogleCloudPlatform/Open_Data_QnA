import 'package:chatview/chatview.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class BotChatView extends StatefulWidget {
  const BotChatView({Key? key}) : super(key: key);

  @override
  State<BotChatView> createState() => BotChatViewState();
}

class BotChatViewState extends State<BotChatView> {

  ChatUser? currentUser;
  ChatUser? bot;
  ChatController?  _chatController;

  @override
  void initState() {
    super.initState();

    currentUser = ChatUser(
      id: '0',
      name: 'User',
      profilePhoto: "https://raw.githubusercontent.com/SimformSolutionsPvtLtd/flutter_showcaseview/master/example/assets/simform.png",
    );

    bot = ChatUser(
      id: '1',
      name: 'Bot',
      profilePhoto: "https://raw.githubusercontent.com/SimformSolutionsPvtLtd/flutter_showcaseview/master/example/assets/simform.png",
    );

    _chatController = ChatController(
      initialMessageList: [
        Message(
          id: '0',
          message: "Hi Bot!",
          createdAt: DateTime.now(),
          sendBy: '0', // userId of who sends the message
        ),
        Message(
          id: '1',
          message: "Hi!",
          createdAt: DateTime.now(),
          sendBy: '1',
        ),
      ],
      scrollController: ScrollController(),
      chatUsers: [
        currentUser!,
        bot!,
      ],
    );

  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ChatView(
          chatBackgroundConfig: ChatBackgroundConfiguration(
            backgroundImage: "https://raw.githubusercontent.com/SimformSolutionsPvtLtd/flutter_showcaseview/master/example/assets/simform.png",//"assets/images/background.png",
            messageTimeIconColor: Colors.white,
            messageTimeTextStyle: TextStyle(color: Colors.white),
            defaultGroupSeparatorConfig: DefaultGroupSeparatorConfiguration(
              textStyle: TextStyle(
                color: Colors.white,
                fontSize: 17,
              ),
            ),
            backgroundColor: Color(0xffFCD8DC),
          ),
          currentUser: currentUser!,
          chatController: _chatController!,
          onSendTap: onSendTap,
          chatViewState: ChatViewState.hasMessages

      ),
    );
  }

  void onSendTap(String message, ReplyMessage replyMessage, MessageType messageType){
    final message = Message(
      id: '2',
      message: "How are you",
      createdAt: DateTime.now(),
      sendBy: currentUser!.id,
      replyMessage: replyMessage,
      messageType: messageType,
    );
    _chatController!.addMessage(message);
  }

}