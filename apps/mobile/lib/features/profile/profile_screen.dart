import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<({Map<String, dynamic> me, List<dynamic> badges})> _load(WidgetRef ref) async {
    final api = ref.read(apiProvider);
    if (api.bearer == null) {
      await api.devToken('mobile@tideguard.app', name: 'Mobile Pilot User');
    }
    final me = await api.me();
    final badges = await api.myBadges();
    return (me: me, badges: badges);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: FutureBuilder<({Map<String, dynamic> me, List<dynamic> badges})>(
        future: _load(ref),
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Padding(
              padding: const EdgeInsets.all(24),
              child: Text('Could not load profile: ${snap.error}'),
            );
          }
          final me = snap.data!.me;
          final badges = snap.data!.badges;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(me['name']?.toString() ?? me['email']?.toString() ?? 'You',
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              Text(me['email']?.toString() ?? '',
                  style: const TextStyle(color: Colors.black54)),
              const SizedBox(height: 16),
              Text('XP: ${me['xp'] ?? 0}',
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              const Text('Badges', style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              if (badges.isEmpty)
                const Text('No badges yet — submit a report or finish a lesson.')
              else
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final b in badges)
                      Chip(
                        avatar: const Icon(Icons.emoji_events_outlined, size: 18),
                        label: Text(b['title']?.toString() ?? b['slug'].toString()),
                      ),
                  ],
                ),
              const SizedBox(height: 24),
              const Text(
                'Complete 5 lessons to unlock your TideGuard certificate.',
                style: TextStyle(color: Colors.black54),
              ),
            ],
          );
        },
      ),
    );
  }
}
