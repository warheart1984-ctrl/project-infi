# AAIS Mobile App Deployment Guide

## iOS App Store Deployment

### Prerequisites

- Apple Developer Account ($99/year)
- Mac with Xcode
- App Store Connect access

### Step 1: Create App in App Store Connect

1. Go to https://appstoreconnect.apple.com
2. Click "My Apps"
3. Click "+" and select "New App"
4. Fill in app details:
   - Name: AAIS
   - Bundle ID: com.aais.mobile
   - SKU: AAIS-001
   - Platform: iOS

### Step 2: Configure Signing

```bash
# In Xcode
# 1. Open ios/AAIS.xcworkspace
# 2. Select AAIS target
# 3. Go to Signing & Capabilities
# 4. Select your team
# 5. Update Bundle Identifier
```

### Step 3: Build and Archive

```bash
# Build for release
npm run build:ios

# Or manually in Xcode
# Product > Archive
```

### Step 4: Upload to App Store

```bash
# Using Xcode
# Window > Organizer
# Select archive
# Click "Distribute App"
# Select "App Store Connect"
# Follow prompts
```

### Step 5: Submit for Review

1. Go to App Store Connect
2. Select your app
3. Click "Prepare for Submission"
4. Fill in app information
5. Click "Submit for Review"

---

## Android Google Play Deployment

### Prerequisites

- Google Play Developer Account ($25 one-time)
- Android Studio
- Google Play Console access

### Step 1: Create App in Google Play Console

1. Go to https://play.google.com/console
2. Click "Create app"
3. Fill in app details:
   - Name: AAIS
   - Default language: English
   - App type: App
   - Category: Productivity

### Step 2: Configure Signing

```bash
# Generate signing key
cd android
keytool -genkey -v -keystore aais-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias aais-key

# Add to gradle.properties
echo 'MYAPP_RELEASE_STORE_FILE=aais-release-key.jks' >> gradle.properties
echo 'MYAPP_RELEASE_KEY_ALIAS=aais-key' >> gradle.properties
echo 'MYAPP_RELEASE_STORE_PASSWORD=your-password' >> gradle.properties
echo 'MYAPP_RELEASE_KEY_PASSWORD=your-password' >> gradle.properties
```

### Step 3: Build AAB

```bash
# Build Android App Bundle
npm run build:android

# Or manually
cd android
./gradlew bundleRelease
cd ..
```

### Step 4: Upload to Google Play

1. Go to Google Play Console
2. Select your app
3. Go to "Release" > "Production"
4. Click "Create new release"
5. Upload AAB file
6. Fill in release notes
7. Click "Review release"

### Step 5: Submit for Review

1. Review app content rating
2. Review privacy policy
3. Review app permissions
4. Click "Submit release"

---

## App Store Optimization (ASO)

### iOS

- **App Name**: AAIS - AI System
- **Subtitle**: Uncensored Multi-Modal AI
- **Keywords**: AI, text generation, image analysis, machine learning
- **Description**: Full feature description
- **Screenshots**: 5-6 high-quality screenshots
- **Preview Video**: Optional demo video

### Android

- **Title**: AAIS - AI System
- **Short Description**: Uncensored Multi-Modal AI
- **Full Description**: Detailed feature list
- **Screenshots**: 4-8 high-quality screenshots
- **Feature Graphic**: 1024x500px banner
- **Icon**: 512x512px app icon

---

## Post-Launch

### Monitoring

- **iOS**: App Store Connect Analytics
- **Android**: Google Play Console Analytics

### Updates

```bash
# Update version in package.json
# Rebuild and resubmit
```

### Support

- Create support email
- Setup in-app feedback
- Monitor reviews and ratings

---

## Estimated Timeline

- **iOS**: 1-3 days for review
- **Android**: 2-4 hours for review
- **Total**: 2-7 days from submission to live

---

## Cost Estimate

- **iOS**: $99/year developer account
- **Android**: $25 one-time developer account
- **Total**: $124 first year, $99 annually

---

## Support

- App Store Connect: https://appstoreconnect.apple.com
- Google Play Console: https://play.google.com/console
- React Native Docs: https://reactnative.dev/
