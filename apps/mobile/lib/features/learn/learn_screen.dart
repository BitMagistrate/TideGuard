import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/provider.dart';

class LearnScreen extends ConsumerStatefulWidget {
  const LearnScreen({super.key});

  @override
  ConsumerState<LearnScreen> createState() => _LearnScreenState();
}

class _LearnScreenState extends ConsumerState<LearnScreen> {
  late Future<List<dynamic>> _lessons;

  @override
  void initState() {
    super.initState();
    _lessons = ref.read(apiProvider).listLessons().catchError((_) => <dynamic>[]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Learn')),
      body: FutureBuilder<List<dynamic>>(
        future: _lessons,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final lessons = snap.data ?? [];
          if (lessons.isEmpty) {
            return const Center(child: Text('No lessons available offline.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: lessons.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final l = lessons[i] as Map<String, dynamic>;
              return Card(
                child: ListTile(
                  title: Text(l['title']?.toString() ?? ''),
                  subtitle: Text(
                    '${l['lang'] ?? 'en'} · +${l['xp_reward']} XP · grade ${l['grade_band'] ?? '?'}',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/learn/${l['slug']}'),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
