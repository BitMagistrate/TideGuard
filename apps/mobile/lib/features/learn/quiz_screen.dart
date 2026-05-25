import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/provider.dart';

class QuizScreen extends ConsumerStatefulWidget {
  final String slug;
  const QuizScreen({super.key, required this.slug});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  Map<String, dynamic>? _lesson;
  int _qi = 0;
  int _correct = 0;
  bool _done = false;
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final api = ref.read(apiProvider);
      final lesson = await api.getLesson(widget.slug);
      setState(() => _lesson = lesson);
    } catch (exc) {
      setState(() => _error = exc.toString());
    }
  }

  Future<void> _submit() async {
    final api = ref.read(apiProvider);
    if (api.bearer == null) {
      await api.devToken('mobile@tideguard.app', name: 'Mobile Pilot User');
    }
    final total = (_lesson!['quiz']['questions'] as List).length;
    final score = total == 0 ? 1.0 : _correct / total;
    try {
      final res = await api.recordLessonProgress(widget.slug, score);
      setState(() => _result = res);
    } catch (exc) {
      setState(() => _error = exc.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final lesson = _lesson;
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Quiz')),
        body: Padding(padding: const EdgeInsets.all(24), child: Text(_error!)),
      );
    }
    if (lesson == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Quiz')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final questions = (lesson['quiz']['questions'] as List).cast<Map<String, dynamic>>();
    if (questions.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text(lesson['title']?.toString() ?? 'Quiz')),
        body: const Center(child: Text('No quiz for this lesson.')),
      );
    }
    if (_done) {
      final total = questions.length;
      final pct = (_correct / total * 100).toStringAsFixed(0);
      return Scaffold(
        appBar: AppBar(title: Text(lesson['title']?.toString() ?? 'Quiz')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Score: $_correct / $total ($pct %)',
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              if (_result != null)
                Text(
                  '+${_result!['xp_awarded']} XP awarded · total ${_result!['xp_total']}',
                  style: const TextStyle(color: Colors.teal),
                ),
              const Spacer(),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Back to lessons'),
              ),
            ],
          ),
        ),
      );
    }
    final q = questions[_qi];
    final opts = (q['options'] as List).cast<String>();
    return Scaffold(
      appBar: AppBar(title: Text(lesson['title']?.toString() ?? 'Quiz')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Question ${_qi + 1} / ${questions.length}',
                style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 8),
            Text(q['q']?.toString() ?? '',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
            const SizedBox(height: 16),
            for (var i = 0; i < opts.length; i++)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: OutlinedButton(
                  onPressed: () async {
                    if (i == q['answer']) _correct++;
                    if (_qi + 1 >= questions.length) {
                      setState(() => _done = true);
                      await _submit();
                    } else {
                      setState(() => _qi += 1);
                    }
                  },
                  child: Align(alignment: Alignment.centerLeft, child: Text(opts[i])),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
