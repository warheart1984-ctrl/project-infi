# AAIS Mobile App - React Native

## Setup Instructions

### Prerequisites

- Node.js 14+ and npm/yarn
- Xcode 12+ (for iOS)
- Android Studio (for Android)
- React Native CLI

### Installation

```bash
# Install dependencies
cd mobile
npm install

# Install pods (iOS)
cd ios
pod install
cd ..
```

### Development

#### iOS

```bash
# Start Metro bundler
npm start

# In another terminal, run iOS
npm run ios
```

#### Android

```bash
# Start Metro bundler
npm start

# In another terminal, run Android
npm run android
```

### Build for Production

#### iOS

```bash
# Build for iOS
npm run build:ios

# Archive for App Store
cd ios
xcodebuild -workspace AAIS.xcworkspace -scheme AAIS -configuration Release -archivePath AAIS.xcarchive archive
cd ..
```

#### Android

```bash
# Build APK
npm run build:android

# Build AAB (for Google Play)
cd android
./gradlew bundleRelease
cd ..
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
├── ios/                     # iOS native code
├── android/                 # Android native code
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

- **react-native**: Core framework
- **react-navigation**: Navigation
- **axios**: HTTP client
- **zustand**: State management
- **react-native-vector-icons**: Icons
- **react-native-image-picker**: Image selection
- **react-native-camera**: Camera access
- **react-native-keychain**: Secure storage

## API Configuration

Update the API URL in screens:

```typescript
const API_URL = 'http://your-api-url';
```

## Testing

```bash
# Run tests
npm test

# Run linting
npm run lint
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

### Pod Issues (iOS)

```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
```

### Gradle Issues (Android)

```bash
cd android
./gradlew clean
cd ..
```

## Support

- React Native Docs: https://reactnative.dev/
- React Navigation: https://reactnavigation.org/
- Expo: https://expo.dev/
