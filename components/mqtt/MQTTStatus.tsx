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