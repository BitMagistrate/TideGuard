import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tideguard/app.dart';

void main() {
  testWidgets('App boots and shows TideGuard title', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: TideGuardApp()));
    await tester.pumpAndSettle();
    expect(find.text('TideGuard'), findsWidgets);
  });
}
