import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/stream_event.dart';

class ApiService {
  ApiService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        baseUrl = baseUrl ?? _defaultBaseUrl;

  static const String _defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  final http.Client _client;
  final String baseUrl;

  Stream<StreamEvent> sendMessageStream(String question) async* {
    final request = http.Request('POST', Uri.parse('$baseUrl/chat/stream'));
    request.headers.addAll({
      'Accept': 'text/event-stream',
      'Content-Type': 'application/json; charset=utf-8',
    });
    request.body = jsonEncode({'question': question});

    final response = await _client.send(request);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final body = await response.stream.bytesToString();
      throw ApiException('请求失败：${response.statusCode} $body');
    }

    var eventName = 'message';
    final dataLines = <String>[];

    await for (final line in response.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter())) {
      if (line.isEmpty) {
        final data = dataLines.join('\n');
        if (data.isNotEmpty) {
          final event = _parseEvent(eventName, data);
          if (event != null) {
            yield event;
          }
        }
        eventName = 'message';
        dataLines.clear();
        continue;
      }

      if (line.startsWith('event:')) {
        eventName = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.add(line.substring(5).trimLeft());
      }
    }
  }

  StreamEvent? _parseEvent(String eventName, String data) {
    if (data == '[DONE]' || eventName == 'done') {
      return const DoneEvent();
    }
    if (eventName == 'sources') {
      final decoded = jsonDecode(data);
      if (decoded is List) {
        return SourcesEvent(decoded.cast<Map<String, dynamic>>());
      }
      return const SourcesEvent([]);
    }
    if (eventName == 'suggestion') {
      final decoded = jsonDecode(data);
      if (decoded is Map<String, dynamic>) {
        return SuggestionEvent(decoded);
      }
      return null;
    }
    return TokenEvent(data);
  }

  void dispose() => _client.close();
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}
