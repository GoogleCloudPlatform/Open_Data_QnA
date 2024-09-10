
import 'package:flutter/material.dart';

class TabbedContainer extends StatefulWidget {
  final List<Widget> tabs;
  final List<Widget> tabViews;
  final TabController controller;
  final int initialIndex;

  const TabbedContainer({
    super.key,
    required this.tabs,
    required this.tabViews,
    required this.controller,
    required this.initialIndex
  });

  @override
  _TabbedContainerState createState() => _TabbedContainerState();
}

class _TabbedContainerState extends State<TabbedContainer>
    with SingleTickerProviderStateMixin {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    widget.controller.index = _currentIndex; // Initialize
    /*widget.controller.addListener(() {
      setState(() {
        _currentIndex = widget.controller.index;
      });
    });*/
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height : 500,
      child: Column(
        children: [
          TabBar(
            controller: widget.controller,
              indicatorSize: TabBarIndicatorSize.tab,
              tabs: widget.tabs),
          Flexible(
              fit: FlexFit.loose,
              child: TabBarView(controller: widget.controller, children: widget.tabViews)
          ),
        ],
      ),
    );
  }
}