import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../../api/provider.dart';

class ReportScreen extends ConsumerStatefulWidget {
  const ReportScreen({super.key});

  @override
  ConsumerState<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends ConsumerState<ReportScreen> {
  File? _photo;
  Position? _position;
  int _severity = 3;
  String _debrisType = 'plastic_bottle';
  bool _submitting = false;
  String? _message;

  Future<void> _pick() async {
    final picked = await ImagePicker().pickImage(
      source: ImageSource.camera,
      maxWidth: 1600,
      imageQuality: 85,
    );
    if (picked == null) return;
    Position? pos;
    try {
      LocationPermission perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm != LocationPermission.denied && perm != LocationPermission.deniedForever) {
        pos = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
        );
      }
    } catch (_) {
      // ignore; user can submit without GPS in pilot mode (we default to last position)
    }
    setState(() {
      _photo = File(picked.path);
      _position = pos;
    });
  }

  Future<void> _submit() async {
    if (_photo == null || _position == null) return;
    setState(() {
      _submitting = true;
      _message = null;
    });
    try {
      final api = ref.read(apiProvider);
      // Make sure we have a JWT — dev_token round trip for the pilot.
      if (api.bearer == null) {
        await api.devToken('mobile@tideguard.app', name: 'Mobile Pilot User');
      }
      final res = await api.submitReport(
        photo: _photo!,
        lat: _position!.latitude,
        lng: _position!.longitude,
        severity: _severity,
        debrisType: _debrisType,
      );
      setState(() {
        _message = 'Submitted! Report ${res['id']} · +${res['xp']} XP total';
        _photo = null;
        _position = null;
      });
    } catch (exc) {
      setState(() => _message = 'Failed: $exc');
    } finally {
      setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report debris')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          ElevatedButton.icon(
            onPressed: _submitting ? null : _pick,
            icon: const Icon(Icons.camera_alt),
            label: const Text('Take photo + capture GPS'),
          ),
          const SizedBox(height: 12),
          if (_photo != null) Image.file(_photo!, height: 200, fit: BoxFit.cover),
          if (_position != null)
            Text(
              'Location: ${_position!.latitude.toStringAsFixed(4)}, ${_position!.longitude.toStringAsFixed(4)}',
            ),
          const SizedBox(height: 20),
          Text('Severity: $_severity'),
          Slider(
            value: _severity.toDouble(),
            min: 1,
            max: 5,
            divisions: 4,
            onChanged: _submitting ? null : (v) => setState(() => _severity = v.toInt()),
          ),
          DropdownButton<String>(
            value: _debrisType,
            isExpanded: true,
            items: const [
              DropdownMenuItem(value: 'plastic_bottle', child: Text('Plastic bottle')),
              DropdownMenuItem(value: 'fishing_net', child: Text('Fishing net')),
              DropdownMenuItem(value: 'foam', child: Text('Foam / polystyrene')),
              DropdownMenuItem(value: 'mixed', child: Text('Mixed plastic')),
            ],
            onChanged: _submitting ? null : (v) => setState(() => _debrisType = v ?? _debrisType),
          ),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: (_photo == null || _position == null || _submitting) ? null : _submit,
            child: Text(_submitting ? 'Sending…' : 'Submit report'),
          ),
          if (_message != null) ...[
            const SizedBox(height: 12),
            Text(_message!, style: const TextStyle(color: Colors.teal)),
          ],
        ],
      ),
    );
  }
}
