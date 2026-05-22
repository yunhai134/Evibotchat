sealed class StreamEvent {
  const StreamEvent();
}

class TokenEvent extends StreamEvent {
  const TokenEvent(this.text);

  final String text;
}

class SourcesEvent extends StreamEvent {
  const SourcesEvent(this.sources);

  final List<Map<String, dynamic>> sources;
}

class SuggestionEvent extends StreamEvent {
  const SuggestionEvent(this.suggestion);

  final Map<String, dynamic> suggestion;
}

class DoneEvent extends StreamEvent {
  const DoneEvent();
}
