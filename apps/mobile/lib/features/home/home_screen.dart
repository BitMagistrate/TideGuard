import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('TideGuard')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const _Hero(),
          const SizedBox(height: 24),
          _Tile(
            icon: Icons.map_outlined,
            title: 'Map',
            subtitle: 'See forecast hotspots near you',
            onTap: () => context.push('/map'),
          ),
          _Tile(
            icon: Icons.photo_camera_outlined,
            title: 'Report debris',
            subtitle: '+10 XP per approved report',
            onTap: () => context.push('/report'),
          ),
          _Tile(
            icon: Icons.menu_book_outlined,
            title: 'Learn',
            subtitle: '10 lessons + certificate',
            onTap: () => context.push('/learn'),
          ),
          _Tile(
            icon: Icons.person_outline,
            title: 'Profile',
            subtitle: 'XP, badges, certificate',
            onTap: () => context.push('/profile'),
          ),
        ],
      ),
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero();
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0F766E), Color(0xFF0369A1)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Predict, report, cleanup.',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text(
            'Be part of the citizen science network keeping our coasts clean.',
            style: TextStyle(color: Colors.white70),
          ),
        ],
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const _Tile({required this.icon, required this.title, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        leading: Icon(icon, color: const Color(0xFF0F766E)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
