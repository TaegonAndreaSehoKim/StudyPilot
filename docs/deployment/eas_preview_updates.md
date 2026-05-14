# EAS Preview Updates

StudyPilot currently uses Expo Go plus EAS Update for quick mobile-device checks. This lets an iPhone reopen the latest preview bundle from Expo's servers without keeping `npx expo start` running on the development machine.

This is a preview workflow, not an App Store release workflow.

## When To Use This

Use EAS preview updates when:

- the backend is already reachable from the phone, usually the EC2 backend URL
- the change is JavaScript or TypeScript UI/app logic
- no native dependency or native configuration change needs a new app binary
- you want to test on iPhone without a local Metro dev server

Use `npx expo start` when:

- you need live reload while coding
- you need local logs from Metro
- you are changing code repeatedly and want immediate feedback

Use an EAS build or a custom development build when:

- a native module is added
- `ios`, `android`, plugins, permissions, or other native app config changes must be tested outside Expo Go
- you need a standalone installable app

## Publish A Preview Update

From the repo root:

```powershell
cd mobile
npm run update:preview -- --message "short description"
```

The command publishes to:

```text
Branch: preview
Runtime version: 0.1.0
```

The app config uses:

- `extra.eas.projectId`
- `runtimeVersion.policy = appVersion`
- `updates.url = https://u.expo.dev/<project-id>`

The `preview` EAS build profile also has `channel = preview`.

## Test On iPhone

1. Open Expo Go on the iPhone.
2. Make sure it is signed into the same Expo account used to publish updates.
3. Reopen the StudyPilot project from the project list or recently opened items.
4. Open Settings.
5. Confirm the backend target is the EC2 URL or another reachable URL.
6. Use the App Update card to inspect update metadata when available.

Expo Go may not support manual in-app update checks in every runtime. If the Settings screen says manual update checks are unavailable, close Expo Go completely and reopen the StudyPilot project.

## Expected Backend Settings

For the EC2 MVP backend:

```text
API Base URL: http://3.23.120.213:8000
Backend Access Token: value from backend/.env on EC2
```

Do not put `OPENAI_API_KEY` in mobile settings. The mobile app only stores the backend URL and optional backend access token.

## Validation Before Publishing

Run:

```powershell
cd mobile
npm run check
```

This runs:

- TypeScript type checking
- mobile smoke checks
- Expo dependency compatibility check
- Expo web export smoke

## Troubleshooting

- If the UI looks stale, fully quit Expo Go and reopen StudyPilot.
- If the backend connection fails, open Settings and test the backend URL.
- If course creation or uploads fail but health succeeds, verify the backend access token.
- If a native config change does not appear in Expo Go, it likely needs an EAS build rather than an update.
- If the app opens a local development bundle, stop Metro and reopen the project from Expo Go's project list instead of scanning a local dev-server QR code.
