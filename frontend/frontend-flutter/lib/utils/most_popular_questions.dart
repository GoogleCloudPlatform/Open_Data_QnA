class MostPopularQ {
  int count;
  String time;
  String question;
  MostPopularQ(this.question,this.count, this.time);

  @override
  String toString() {
    return "{question = $question : count = $count : time = $time}";
  }
}