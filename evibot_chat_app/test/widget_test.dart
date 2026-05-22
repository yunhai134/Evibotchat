import 'package:flutter_test/flutter_test.dart';

import 'package:evibot_chat_app/main.dart';

void main() {
  testWidgets('Medical RAG chat app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const EvibotApp());

    expect(find.text('医学 RAG 智能问答助手'), findsOneWidget);
    expect(find.text('基于本地医学教材知识库回答'), findsOneWidget);
    expect(find.textContaining('医学教材 RAG 问答助手'), findsOneWidget);
    expect(find.text('例如：高血压如何用药？'), findsOneWidget);
  });
}
