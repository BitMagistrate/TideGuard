import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'features/home/home_screen.dart';
import 'features/learn/learn_screen.dart';
import 'features/learn/quiz_screen.dart';
import 'features/map/map_screen.dart';
import 'features/profile/profile_screen.dart';
import 'features/report/report_screen.dart';

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/map', builder: (_, __) => const MapScreen()),
    GoRoute(path: '/report', builder: (_, __) => const ReportScreen()),
    GoRoute(path: '/learn', builder: (_, __) => const LearnScreen()),
    GoRoute(
      path: '/learn/:slug',
      builder: (_, state) => QuizScreen(slug: state.pathParameters['slug']!),
    ),
    GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
  ],
);

class TideGuardApp extends StatelessWidget {
  const TideGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'TideGuard',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF0F766E),
        scaffoldBackgroundColor: const Color(0xFFFEFCF7),
      ),
      routerConfig: _router,
    );
  }
}
