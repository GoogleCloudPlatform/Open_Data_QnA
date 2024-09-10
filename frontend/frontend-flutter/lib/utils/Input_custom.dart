import 'package:flutter/material.dart';
import 'package:flutter_chat_ui/flutter_chat_ui.dart';
import 'package:flutter_chat_types/flutter_chat_types.dart' as types;

class InputCustom extends Input {
  final bool? isAttachmentUploading;
  final VoidCallback? onAttachmentPressed;
  final void Function(types.PartialText) onSendPressed;
  final InputOptions options;
  //TextEditingController? _textController;

  InputCustom({
    super.key,
    this.isAttachmentUploading,
    this.onAttachmentPressed,
    required this.onSendPressed,
    this.options = const InputOptions(),
  }): super(
    isAttachmentUploading: isAttachmentUploading,
    onAttachmentPressed: onAttachmentPressed,
    onSendPressed: onSendPressed,
    options: options,
  );

}