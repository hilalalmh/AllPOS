import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/app_config.dart';
import 'providers/providers.dart';
import 'repositories/session_store.dart';
import 'screens/splash_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final sessionStore = SessionStore(prefs);
  try {
    await sessionStore.init();
  } catch (_) {
    // flutter_secure_storage tidak tersedia (mis. web HTTP atau platform
    // tanpa Keystore/Keychain): degradasi ke sesi kosong agar app tetap
    // boot ke halaman login alih-alih layar mati. Hapus user yang sempat
    // tersimpan di prefs agar tidak terlihat sudah login.
    prefs.remove('session.user');
  }
  runApp(
    ProviderScope(
      overrides: [
        sharedPrefsProvider.overrideWithValue(prefs),
        sessionStoreProvider.overrideWithValue(sessionStore),
      ],
      child: const SistemPosApp(),
    ),
  );
}

class SistemPosApp extends StatelessWidget {
  const SistemPosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const SplashScreen(),
    );
  }
}
