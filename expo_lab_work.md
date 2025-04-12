# Laboratory Work: Building an MQTT Chat Application 🚀

## Overview 📋

In this lab, you will create a mobile chat application using Expo and MQTT protocol. The app will allow real-time messaging through a public MQTT broker.

## Prerequisites 📚

- Node.js installed (v14 or higher)
- VS Code or similar code editor
- Expo Go app installed on your mobile device

## Detailed Steps 📝

### Step 1: Initial Setup (20 points)

1. Create a new Expo project:
```bash
npx create-expo-app my-mqtt-app
cd my-mqtt-app
```

2. Install required dependencies:
```bash
npx expo install react_native_mqtt @react-native-async-storage/async-storage expo-router@^4.0.17 react-native-reanimated expo-font expo-status-bar @expo/vector-icons
```

3. Create the following directory structure:
```bash
mkdir -p app/(tabs)
mkdir -p components/mqtt
mkdir -p hooks
mkdir -p types
```

4. Update tsconfig.json with the following content:
```json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "module": "esnext",
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    ".expo/types/**/*.ts",
    "expo-env.d.ts",
    "*.ts",
    "*.tsx"
  ]
}
```

### Step 2: Create Component Files (30 points)

1. Create MQTT components:

Create file `components/mqtt/MQTTStatus.tsx`:
```typescript
import { View } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { styles } from './styles';

interface Props {
  isConnected: boolean;
}

export function MQTTStatus({ isConnected }: Props) {
  return (
    <View style={styles.statusIndicator}>
      <View style={[
        styles.statusDot,
        isConnected ? styles.statusConnected : styles.statusDisconnected
      ]} />
      <ThemedText style={styles.statusText}>
        {isConnected ? 'Connected' : 'Disconnected'}
      </ThemedText>
    </View>
  );
}
```

[Continue with other component files...]

2. Create styles file `components/mqtt/styles.ts`:
```typescript
import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  // ... [Copy the complete styles from the provided code]
});
```

### Step 3: Set Up Navigation (20 points)

1. Create file `app/_layout.tsx`:
```typescript
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function AppLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Chat',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="chatbubbles" size={size} color={color} />
          ),
        }}
      />
      // ... [Add other tab screens]
    </Tabs>
  );
}
```

### Step 4: Implement MQTT Logic (30 points)

1. Create MQTT hook `hooks/useMQTTConnection.ts`:
```typescript
import { useState, useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export function useMQTTConnection() {
  // ... [Copy the complete hook implementation]
}
```

2. Create type definitions `types/react_native_mqtt.d.ts`:
```typescript
declare module 'react_native_mqtt' {
  // ... [Copy the type definitions]
}
```

### Step 5: Testing and Debugging

1. Start the development server:
```bash
npx expo start
```

2. Open Expo Go on your device and scan the QR code

3. Test the following functionality:
   - [ ] Connection to MQTT broker
   - [ ] Sending messages
   - [ ] Receiving messages
   - [ ] Topic management
   - [ ] Settings configuration

## Common Issues and Solutions 🔧

1. If you see "window is not defined":
   - Make sure MQTT initialization is inside useEffect
   - Check dynamic imports are working

2. If connection fails:
   - Verify broker address and port
   - Check network connectivity
   - Ensure WebSocket support

## Submission Requirements 📤

1. Source Code:
   - Complete GitHub repository
   - All components implemented
   - Working MQTT connection

2. Documentation:
   - Screenshots of working app
   - Brief report explaining:
     * Implementation challenges
     * Solutions found
     * Lessons learned

3. Video Demo:
   - 2-3 minute demonstration
   - Show all main features

## Grading Rubric 📊

| Task | Points | Requirements |
|------|--------|--------------|
| Setup | 20 | Project structure, dependencies |
| Components | 30 | All UI components working |
| MQTT | 30 | Connection, messaging working |
| Navigation | 20 | Tab navigation, screens working |

## Bonus Points 🌟

- Persistent messages (+5)
- Custom broker settings (+3)
- Error handling (+2)
- UI improvements (+5)

## Resources 📚

- [Complete source code](https://github.com/yourusername/mqtt-chat-app)
- [MQTT Broker](https://www.hivemq.com/public-mqtt-broker/)
- [Expo Router Docs](https://docs.expo.dev/router/introduction/)

## Timeline ⏰

- Initial setup: 30 mins
- Component creation: 2 hours
- MQTT implementation: 2 hours
- Testing: 1 hour
- Documentation: 30 mins

## Support 💬

- Lab assistance: [Contact details]
- Office hours: [Schedule]
- Discord: [Channel link]

Remember to commit your changes frequently and test thoroughly!

Good luck! 🚀 