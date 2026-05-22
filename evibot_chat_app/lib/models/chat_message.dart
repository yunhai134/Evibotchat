enum ChatRole { user, assistant }

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    this.isStreaming = false,
    this.sources = const [],
    this.suggestion,
  });

  final String id;
  final ChatRole role;
  final String content;
  final bool isStreaming;
  final List<ChatSource> sources;
  final QuestionSuggestion? suggestion;

  ChatMessage copyWith({
    String? content,
    bool? isStreaming,
    List<ChatSource>? sources,
    QuestionSuggestion? suggestion,
    bool clearSuggestion = false,
  }) {
    return ChatMessage(
      id: id,
      role: role,
      content: content ?? this.content,
      isStreaming: isStreaming ?? this.isStreaming,
      sources: sources ?? this.sources,
      suggestion: clearSuggestion ? null : (suggestion ?? this.suggestion),
    );
  }
}

class ChatSource {
  const ChatSource({required this.source, required this.page});

  final String source;
  final String page;

  factory ChatSource.fromJson(Map<String, dynamic> json) {
    return ChatSource(
      source: json['source']?.toString() ?? '未知资料',
      page: json['page']?.toString() ?? '?',
    );
  }
}

class QuestionSuggestion {
  const QuestionSuggestion({
    required this.question,
    required this.score,
    this.disease = '',
  });

  final String question;
  final double score;
  final String disease;

  factory QuestionSuggestion.fromJson(Map<String, dynamic> json) {
    return QuestionSuggestion(
      question: json['question']?.toString() ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      disease: json['disease']?.toString() ?? '',
    );
  }
}
