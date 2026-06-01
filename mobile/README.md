# AAIS Mobile App - Expo

## Setup Instructions

### Prerequisites

- Node.js 14+ and npm/yarn
- Expo CLI support through `npx expo`

### Installation

```bash
# Install dependencies
cd mobile
npm install
```

### Development

#### iOS

```bash
# Start Expo
npm start

# Or launch directly
npm run ios
```

#### Android

```bash
# Start Expo
npm start

# Or launch directly
npm run android
```

### Build for Production

For local verification:

```bash
npm run typecheck
npx expo export --platform web
```

## Project Structure

```
mobile/
├── src/
│   ├── App.tsx              # Main app component
│   ├── screens/             # Screen components
│   │   ├── DashboardScreen.tsx
│   │   ├── TextGeneratorScreen.tsx
│   │   ├── ImageAnalyzerScreen.tsx
│   │   ├── ImageGeneratorScreen.tsx
│   │   ├── HistoryScreen.tsx
│   │   ├── SettingsScreen.tsx
│   │   ├── LoginScreen.tsx
│   │   └── SplashScreen.tsx
│   ├── components/          # Reusable components
│   ├── services/            # API services
│   ├── store/               # State management
│   └── utils/               # Utilities
├── App.tsx                  # Expo root entry
├── index.ts                 # Expo registration
├── app.json                 # Expo app config
├── package.json
└── tsconfig.json
```

## Features

- ✅ Text Generation
- ✅ Image Analysis
- ✅ Image Generation
- ✅ History Tracking
- ✅ Settings
- ✅ Authentication
- ✅ Bottom Tab Navigation
- ✅ Toast Notifications
- ✅ Loading States

## Dependencies

- **expo**: Managed runtime and tooling
- **react-navigation**: Navigation
- **axios**: HTTP client
- **zustand**: State management
- **@expo/vector-icons**: Icons

## API Configuration

Update the API URL with an Expo env var when your phone/emulator cannot reach the default local host:

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.10:5000 npm start
```

## External Suggestion Admission

This mobile surface inherits the project-wide external suggestion admission
law.

Outside product or UX ideas may be discussed or compared here, but they do not
become adopted mobile behavior unless project law has filtered them and the
admitted form is documented.

## Testing

```bash
# Run TypeScript verification
npm run typecheck
```

## Deployment

### App Store (iOS)

1. Create App Store Connect account
2. Create app in App Store Connect
3. Build and archive
4. Upload to App Store Connect
5. Submit for review

### Google Play (Android)

1. Create Google Play Developer account
2. Create app in Google Play Console
3. Build AAB
4. Upload to Google Play Console
5. Submit for review

## Troubleshooting

### Metro Bundler Issues

```bash
# Clear cache
npm start -- --reset-cache
```

### Can't reach the backend

- iOS simulator can usually use `http://127.0.0.1:5000`
- Android emulator usually needs `http://10.0.2.2:5000`
- Physical devices usually need `EXPO_PUBLIC_API_URL=http://<your-lan-ip>:5000`

## Support

- React Native Docs: https://reactnative.dev/
- React Navigation: https://reactnavigation.org/
- Expo: https://expo.dev/
