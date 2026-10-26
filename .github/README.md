# PersonalGram APK builds

The `Build PersonalGram APK` workflow builds a signed release APK on pushes to
`master`, or manually from **Actions → Build PersonalGram APK → Run workflow**.
Download the APK from the run's **Artifacts** section. Manual runs can choose
ARM64 (the default) or a universal APK covering all four upstream architectures.
Firebase configuration is not required.

Configure these repository secrets under **Settings → Secrets and variables →
Actions → Secrets**:

| Secret | Value |
| --- | --- |
| `TELEGRAM_API_ID` | Your Telegram application API ID |
| `TELEGRAM_API_HASH` | Your Telegram application API hash |
| `ANDROID_KEYSTORE_BASE64` | Base64 encoding of your private signing keystore |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Signing key alias, e.g. `personalgram` |
| `ANDROID_KEY_PASSWORD` | Signing key password; same as the store password for PKCS12 |

Create and back up a private key once:

```bash
mkdir -p "$HOME/.android"
keytool -genkeypair -keystore "$HOME/.android/personalgram.keystore" \
  -storetype PKCS12 -alias personalgram -keyalg RSA -keysize 3072 -validity 10000
base64 -w 0 "$HOME/.android/personalgram.keystore" |
  gh secret set ANDROID_KEYSTORE_BASE64 --repo replydev/Telegram
gh secret set ANDROID_KEY_ALIAS --repo replydev/Telegram --body personalgram
gh secret set ANDROID_KEYSTORE_PASSWORD --repo replydev/Telegram
gh secret set ANDROID_KEY_PASSWORD --repo replydev/Telegram
```

The password commands prompt for their values. Keep the same signing key and
application ID for future updates.

Optional repository **Variables** are `APP_NAME` (default `PersonalGram`) and
`APP_PACKAGE` (default `org.personalgram.messenger`). Credentials and branding
are injected into the disposable runner checkout; they are not committed.
The workflow adds its run number to the upstream version code for installable
updates, verifies the APK signature, and uploads only the APK for 14 days.
