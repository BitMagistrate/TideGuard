import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'client.dart';

final apiProvider = Provider<TideGuardApi>((ref) => TideGuardApi());
