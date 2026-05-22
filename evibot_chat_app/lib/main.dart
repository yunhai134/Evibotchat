import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/chat_provider.dart';
import 'screens/chat_screen.dart';

void main() {
  runApp(const EvibotApp());
}

class EvibotApp extends StatelessWidget {
  const EvibotApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF0F766E);
    return ChangeNotifierProvider(
      create: (_) => ChatProvider(),
      child: MaterialApp(
        title: '医学 RAG 智能问答助手',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: seed,
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          fontFamily: 'Microsoft YaHei',
          appBarTheme: const AppBarTheme(centerTitle: false),
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: seed,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          fontFamily: 'Microsoft YaHei',
          appBarTheme: const AppBarTheme(centerTitle: false),
        ),
        home: const ChatScreen(),
      ),
    );
  }
}
