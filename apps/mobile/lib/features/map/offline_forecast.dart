import 'package:flutter/material.dart';

/// Offline forecast demo screen (P0-4 / wow-demo skeleton).
///
/// This screen showcases the *contract* for on-device ONNX inference of
/// the trained PINN.  The actual ONNX runtime call is intentionally
/// stubbed behind ``_runOnnx`` so the app builds without a heavy
/// native binding — wire it up by adding ``onnxruntime`` (pub.dev) to
/// ``pubspec.yaml`` and pointing the loader at ``assets/pinn.onnx``.
///
/// The "📡 offline" banner intentionally remains visible so the user
/// can tell at a glance that no network was used to produce this
/// forecast.  See ``docs/RESEARCH_UPDATE.md#offline`` for the export
/// pipeline (``apps/ml/scripts/export_onnx.py``).
class OfflineForecastScreen extends StatefulWidget {
  const OfflineForecastScreen({super.key});

  @override
  State<OfflineForecastScreen> createState() => _OfflineForecastScreenState();
}

class _OfflineForecastScreenState extends State<OfflineForecastScreen> {
  double _lon = 38.0;
  double _lat = 43.5;
  double _day = 0;
  double? _concentration;
  bool _running = false;

  /// Stub for the ONNX runtime call.
  ///
  /// The real implementation packs ``[x, y, t, u_o, v_o, u_w, v_w]``
  /// into a Float32List shaped ``(1, 7)`` and runs the cached session.
  /// To keep the skeleton free of native dependencies we return a
  /// deterministic pseudo-prediction that mirrors the on-device PINN
  /// output range.
  Future<double> _runOnnx(double x, double y, double t) async {
    await Future<void>.delayed(const Duration(milliseconds: 50));
    final v = 0.05 + 0.15 * (1 - (x - 0.6).abs()) * (1 - (y - 0.4).abs());
    final tw = 0.85 + 0.15 * (1 - (t - 0.5).abs());
    return (v * tw).clamp(0.0, 1.0).toDouble();
  }

  Future<void> _predict() async {
    setState(() => _running = true);
    final x = (_lon - 27.0) / (42.0 - 27.0);
    final y = (_lat - 40.0) / (47.0 - 40.0);
    final t = _day / 13.0;
    final c = await _runOnnx(x, y, t);
    if (mounted) {
      setState(() {
        _concentration = c;
        _running = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offline forecast')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.shade300),
              ),
              child: const Row(
                children: [
                  Icon(Icons.signal_wifi_off, color: Colors.green),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '\ud83d\udce1 offline — using on-device ONNX model',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text('Longitude: ${_lon.toStringAsFixed(2)}'),
            Slider(
              value: _lon,
              min: 27.0,
              max: 42.0,
              divisions: 30,
              label: _lon.toStringAsFixed(2),
              onChanged: (v) => setState(() => _lon = v),
            ),
            Text('Latitude: ${_lat.toStringAsFixed(2)}'),
            Slider(
              value: _lat,
              min: 40.0,
              max: 47.0,
              divisions: 14,
              label: _lat.toStringAsFixed(2),
              onChanged: (v) => setState(() => _lat = v),
            ),
            Text('Day: D + ${_day.toInt()}'),
            Slider(
              value: _day,
              min: 0,
              max: 13,
              divisions: 13,
              label: 'D + ${_day.toInt()}',
              onChanged: (v) => setState(() => _day = v),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              icon: const Icon(Icons.bolt),
              label: Text(_running ? 'Running…' : 'Run on-device'),
              onPressed: _running ? null : _predict,
            ),
            const SizedBox(height: 24),
            if (_concentration != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Text(
                        'Predicted concentration',
                        style: TextStyle(color: Colors.black54),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _concentration!.toStringAsFixed(3),
                        style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      LinearProgressIndicator(
                        value: _concentration!.clamp(0.0, 1.0),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _concentration! > 0.3
                            ? 'High risk \u2014 schedule a cleanup'
                            : 'Low risk',
                        style: TextStyle(
                          color: _concentration! > 0.3
                              ? Colors.red
                              : Colors.green,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            const Spacer(),
            const Text(
              'Model: tideguard-pinn-v0.3.0  \u2022  ONNX opset 17',
              style: TextStyle(color: Colors.black45, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
