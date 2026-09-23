import org.gradle.api.GradleException
import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Konfigurasi signing dibaca dari android/key.properties (jangan di-commit).
// Contoh isi: storeFile, storePassword, keyAlias, keyPassword.
val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    FileInputStream(keystorePropertiesFile).use { keystoreProperties.load(it) }
}

val releaseSigningReady =
    keystorePropertiesFile.exists() &&
        keystoreProperties["storeFile"] != null &&
        keystoreProperties["keyAlias"] != null &&
        keystoreProperties["storePassword"] != null &&
        keystoreProperties["keyPassword"] != null

android {
    namespace = "com.sistempos.sistem_pos"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.sistempos.sistem_pos"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        // Uses the version code from pubspec.yaml. When using split APKs, 1000 * ABI_VERSION
        // is added automatically by Flutter. (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // You can force using the value of versionCode by specifying the `-P force-version-code-ignoring-abi=true`
        // flag during build.
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            keyAlias = keystoreProperties["keyAlias"] as String?
            keyPassword = keystoreProperties["keyPassword"] as String?
            storeFile = keystoreProperties["storeFile"]?.let { file(it) }
            storePassword = keystoreProperties["storePassword"] as String?
        }
    }

    buildTypes {
        release {
            // Jika android/key.properties tidak ada, build DEBUG tetap boleh
            // jalan (fallback ke debug), tapi pembuatan build rilis WAJIB
            // ditolak — lihat guard gradle.taskGraph di bawah.
            signingConfig =
                if (releaseSigningReady) {
                    signingConfigs.getByName("release")
                } else {
                    signingConfigs.getByName("debug")
                }
        }
    }
}

// Fail-closed: jangan pernah memproduksi APK/AAB rilis yang ke-tanda-tangani
// dengan debug keystore secara diam-diam. Dilempar saat fase eksekusi saja,
// sehingga build debug/profile tidak terganggu.
gradle.taskGraph.whenReady {
    val wantsReleasePackaging = allTasks.any { task ->
        task.name.contains("Release") &&
            (task.name.startsWith("assemble") ||
                task.name.startsWith("bundle") ||
                task.name.startsWith("package"))
    }
    if (wantsReleasePackaging && !releaseSigningReady) {
        throw GradleException(
            "Android release signing belum dikonfigurasi. " +
                "Buat android/key.properties (lihat key.properties.example) " +
                "sebelum menandatangani build rilis."
        )
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
