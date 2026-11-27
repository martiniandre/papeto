# Papeto app (Expo)

Rules for contributors are in `AGENTS.md`. Commands: `npm install`, `npx expo start`,
`npm run typecheck && npm run lint && npm test`.

## Google sign-in needs a development build

`@react-native-google-signin/google-signin` has native code, so it does **not** work in Expo Go.
In Expo Go the Google button shows "não está disponível nesta versão" and the e-mail path keeps working.

### Google Cloud setup (owner)

1. In Google Cloud Console create an OAuth consent screen and these OAuth client ids:
   - **Web application**: its id is `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`. The backend verifies the id token against this audience, so the backend must be configured with the same id.
   - **iOS** (bundle id `app.papeto`): its id is `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`.
   - **Android** (package `app.papeto`, SHA-1 of the EAS signing keystore, see `eas credentials`): no id goes in the app; it only has to exist.
2. In `app.json`, replace `REPLACE_WITH_IOS_CLIENT_ID` in the google-signin plugin `iosUrlScheme` with the iOS client id **reversed**
   (`com.googleusercontent.apps.<id before .apps.googleusercontent.com>`).
3. Set the two variables in each profile `env` of `eas.json` (or as EAS environment variables) and in a local `.env` for `npx expo start` (see `.env.example`).

### Build

```
npm install -g eas-cli && eas login
eas build --profile development --platform android   # or ios
npx expo start --dev-client
```

Install the resulting build on the device or emulator, then start the dev server with `--dev-client`.
Changing `app.json` plugins or client ids requires a new build.
