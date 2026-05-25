import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../api/client.dart';
import 'offline_forecast.dart';

/// Forecast map screen.
///
/// Audit fixes (TIDEGUARD_AUDIT.md TASK-012 / CRIT-MOB-1..2):
///   * Switched to ``flutter_map`` so the whole Black Sea is scrollable
///     instead of a single hard-coded Taiwan tile.
///   * Tile URLs use the API base from ``--dart-define=TIDEGUARD_API_URL=…``
///     (see ``api/client.dart``) — no more hard-coded ``defaultApiUrl``.
///   * Added a "P(exceedance)" toggle that swaps the raster tile URL.
class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  int _day = 0;
  bool _exceedance = false;

  static const LatLng _blackSeaCenter = LatLng(43.5, 34.5);
  static const double _blackSeaZoom = 5.5;
  static const LatLngBounds _blackSeaBounds = LatLngBounds.unsafe(
    LatLng(38.5, 25.5),
    LatLng(48.5, 43.5),
  );

  String _tileTemplate() {
    final base = defaultApiUrl;
    final bbox = '27,40,42,47';
    final layer = _exceedance ? 'exceedance' : 'forecast';
    return '$base/tiles/{z}/{x}/{y}.png?day=$_day&bbox=$bbox&layer=$layer';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Black Sea forecast')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                Text('D + $_day'),
                Expanded(
                  child: Slider(
                    value: _day.toDouble(),
                    min: 0,
                    max: 13,
                    divisions: 13,
                    onChanged: (v) => setState(() => _day = v.toInt()),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('Mean')),
                ButtonSegment(value: true, label: Text('P(exceed)')),
              ],
              selected: <bool>{_exceedance},
              onSelectionChanged: (s) => setState(() => _exceedance = s.first),
            ),
          ),
          Expanded(
            child: FlutterMap(
              options: const MapOptions(
                initialCenter: _blackSeaCenter,
                initialZoom: _blackSeaZoom,
                cameraConstraint: CameraConstraint.contain(
                  bounds: _blackSeaBounds,
                ),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'app.tideguard.mobile',
                ),
                Opacity(
                  opacity: 0.65,
                  child: TileLayer(
                    urlTemplate: _tileTemplate(),
                    userAgentPackageName: 'app.tideguard.mobile',
                    errorTileCallback: (tile, error, stack) {
                      // Offline: silently keep the OSM base.
                    },
                  ),
                ),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              'Slide for the 14-day horizon. Toggle "P(exceed)" for the '
              'ensemble uncertainty layer (TASK-003).',
              style: TextStyle(color: Colors.black54),
              textAlign: TextAlign.center,
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: TextButton.icon(
              icon: const Icon(Icons.cloud_off),
              label: const Text('Offline forecast (ONNX demo)'),
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => const OfflineForecastScreen(),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}


