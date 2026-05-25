import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

const String defaultApiUrl =
    String.fromEnvironment('TIDEGUARD_API_URL', defaultValue: 'http://10.0.2.2:8000');

class TideGuardApi {
  final String baseUrl;
  String? bearer;

  TideGuardApi({this.baseUrl = defaultApiUrl, this.bearer});

  Uri _u(String path) => Uri.parse('$baseUrl$path');

  Map<String, String> _headers({bool json = false}) {
    final h = <String, String>{};
    if (bearer != null) h['Authorization'] = 'Bearer $bearer';
    if (json) h['Content-Type'] = 'application/json';
    return h;
  }

  Future<List<dynamic>> listLessons() async {
    final r = await http.get(_u('/education/lessons'), headers: _headers());
    if (r.statusCode != 200) {
      throw Exception('lessons failed: ${r.statusCode}');
    }
    return jsonDecode(r.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> getLesson(String slug) async {
    final r = await http.get(_u('/education/lessons/$slug'), headers: _headers());
    if (r.statusCode != 200) {
      throw Exception('lesson failed: ${r.statusCode}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> me() async {
    final r = await http.get(_u('/me'), headers: _headers());
    if (r.statusCode != 200) throw Exception('me failed: ${r.statusCode}');
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> cleanupStats() async {
    final r = await http.get(_u('/cleanups/stats'), headers: _headers());
    if (r.statusCode != 200) {
      throw Exception('stats failed: ${r.statusCode}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> myBadges() async {
    final r = await http.get(_u('/badges/mine'), headers: _headers());
    if (r.statusCode != 200) {
      throw Exception('badges failed: ${r.statusCode}');
    }
    return jsonDecode(r.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> devToken(String email, {String? name}) async {
    final r = await http.post(
      _u('/auth/dev_token'),
      headers: _headers(json: true),
      body: jsonEncode({'email': email, if (name != null) 'name': name}),
    );
    if (r.statusCode != 200) {
      throw Exception('dev_token failed: ${r.statusCode} ${r.body}');
    }
    final payload = jsonDecode(r.body) as Map<String, dynamic>;
    bearer = payload['access_token'] as String?;
    return payload;
  }

  /// Submits a citizen report with a photo. Returns the parsed JSON response.
  Future<Map<String, dynamic>> submitReport({
    required File photo,
    required double lat,
    required double lng,
    required int severity,
    String debrisType = 'plastic_bottle',
  }) async {
    final req = http.MultipartRequest('POST', _u('/reports'));
    req.headers.addAll(_headers());
    req.fields['lat'] = lat.toString();
    req.fields['lng'] = lng.toString();
    req.fields['severity'] = severity.toString();
    req.fields['debris_type'] = debrisType;
    req.files.add(await http.MultipartFile.fromPath('photo', photo.path));
    final streamed = await req.send();
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode != 200) {
      throw Exception('reports POST failed: ${streamed.statusCode} $body');
    }
    return jsonDecode(body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> recordLessonProgress(String slug, double score) async {
    final r = await http.post(
      _u('/education/progress'),
      headers: _headers(json: true),
      body: jsonEncode({'lesson_slug': slug, 'score': score}),
    );
    if (r.statusCode != 200) {
      throw Exception('progress failed: ${r.statusCode} ${r.body}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }
}
