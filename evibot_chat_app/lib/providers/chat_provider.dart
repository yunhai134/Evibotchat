import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import '../models/chat_message.dart';
import '../models/stream_event.dart';
import '../services/api_service.dart';

class ChatProvider extends ChangeNotifier {
  ChatProvider({ApiService? apiService}) : _apiService = apiService ?? ApiService();

  final ApiService _apiService;
  final _uuid = const Uuid();
  final List<ChatMessage> _messages = [
    ChatMessage(
      id: const Uuid().v4(),
      role: ChatRole.assistant,
      content: '你好，我是医学教材 RAG 问答助手。请提出具体医学问题，我会尽量基于本地医学知识库回答。',
    ),
  ];

  bool _isStreaming = false;
  String? _error;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isStreaming => _isStreaming;
  String? get error => _error;

  Future<void> sendMessage(String question) async {
    final trimmed = question.trim();
    if (trimmed.isEmpty || _isStreaming) return;

    _error = null;
    _isStreaming = true;
    _messages.add(ChatMessage(id: _uuid.v4(), role: ChatRole.user, content: trimmed));
    final assistantId = _uuid.v4();
    _messages.add(ChatMessage(
      id: assistantId,
      role: ChatRole.assistant,
      content: '',
      isStreaming: true,
    ));
    notifyListeners();

    try {
      await for (final event in _apiService.sendMessageStream(trimmed)) {
        switch (event) {
          case TokenEvent(:final text):
            _appendAssistantText(assistantId, text);
          case SourcesEvent(:final sources):
            _setAssistantSources(
              assistantId,
              sources.map(ChatSource.fromJson).toList(growable: false),
            );
          case SuggestionEvent(:final suggestion):
            _setAssistantSuggestion(
              assistantId,
              QuestionSuggestion.fromJson(suggestion),
            );
          case DoneEvent():
            _finishAssistantMessage(assistantId);
        }
      }
      _finishAssistantMessage(assistantId);
    } catch (exception) {
      _error = exception.toString();
      _appendAssistantText(assistantId, '\n\n请求失败：$_error');
      _finishAssistantMessage(assistantId);
    } finally {
      _isStreaming = false;
      notifyListeners();
    }
  }

  void _appendAssistantText(String id, String text) {
    final index = _messages.indexWhere((message) => message.id == id);
    if (index == -1) return;
    final message = _messages[index];
    _messages[index] = message.copyWith(content: message.content + text);
    notifyListeners();
  }

  void _setAssistantSources(String id, List<ChatSource> sources) {
    final index = _messages.indexWhere((message) => message.id == id);
    if (index == -1) return;
    _messages[index] = _messages[index].copyWith(sources: sources);
    notifyListeners();
  }

  void _setAssistantSuggestion(String id, QuestionSuggestion suggestion) {
    final index = _messages.indexWhere((message) => message.id == id);
    if (index == -1) return;
    _messages[index] = _messages[index].copyWith(suggestion: suggestion);
    notifyListeners();
  }

  void _finishAssistantMessage(String id) {
    final index = _messages.indexWhere((message) => message.id == id);
    if (index == -1) return;
    _messages[index] = _messages[index].copyWith(isStreaming: false);
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _apiService.dispose();
    super.dispose();
  }
}
