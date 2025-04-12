import { View, TextInput, Switch, ScrollView } from 'react-native';
import { useState } from 'react';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { styles } from '@/components/mqtt/styles';

export default function SettingsScreen() {
  const [broker, setBroker] = useState('192.168.31.61');
  const [port, setPort] = useState('8000');
  const [clientId, setClientId] = useState('');
  const [useSSL, setUseSSL] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <ThemedView style={styles.settingsContainer}>
      <ScrollView>
        <View style={styles.settingSection}>
          <ThemedText style={styles.settingTitle}>Connection Settings</ThemedText>
          
          <View style={styles.settingItem}>
            <ThemedText style={styles.settingLabel}>Broker URL</ThemedText>
            <TextInput
              style={styles.settingInput}
              value={broker}
              onChangeText={setBroker}
              placeholder="Enter broker URL"
            />
          </View>

          <View style={styles.settingItem}>
            <ThemedText style={styles.settingLabel}>Port</ThemedText>
            <TextInput
              style={styles.settingInput}
              value={port}
              onChangeText={setPort}
              keyboardType="numeric"
            />
          </View>

          <View style={styles.settingItem}>
            <ThemedText style={styles.settingLabel}>Client ID</ThemedText>
            <TextInput
              style={styles.settingInput}
              value={clientId}
              onChangeText={setClientId}
              placeholder="Leave empty for random ID"
            />
          </View>

          <View style={[styles.settingItem, styles.settingSwitch]}>
            <ThemedText style={styles.settingLabel}>Use SSL</ThemedText>
            <Switch value={useSSL} onValueChange={setUseSSL} />
          </View>
        </View>

        <View style={styles.settingSection}>
          <ThemedText style={styles.settingTitle}>Authentication</ThemedText>
          
          <View style={styles.settingItem}>
            <ThemedText style={styles.settingLabel}>Username</ThemedText>
            <TextInput
              style={styles.settingInput}
              value={username}
              onChangeText={setUsername}
              placeholder="Optional"
            />
          </View>

          <View style={styles.settingItem}>
            <ThemedText style={styles.settingLabel}>Password</ThemedText>
            <TextInput
              style={styles.settingInput}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholder="Optional"
            />
          </View>
        </View>
      </ScrollView>
    </ThemedView>
  );
} 
