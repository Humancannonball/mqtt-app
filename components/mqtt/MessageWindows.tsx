import { View, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ThemedText } from '@/components/ThemedText';
import { styles } from './styles';

export const MessageWindows = ({ 
  sentMessages, 
  receivedMessages 
}: { 
  sentMessages: Array<{ text: string; time: string; topic: string }>;
  receivedMessages: Array<{ text: string; time: string; topic: string }>;
}) => {
  return (
    <View style={styles.messagesSection}>
      {/* Sent Messages */}
      <View style={styles.messageWindow}>
        <ThemedText style={styles.windowTitle}>Sent Messages</ThemedText>
        <ScrollView style={styles.messagesList}>
          {sentMessages.map((msg, index) => (
            <View key={index} style={[styles.messageCard, styles.sentMessage]}>
              <ThemedText style={styles.topicName}>{msg.topic}</ThemedText>
              <ThemedText style={styles.messageText}>{msg.text}</ThemedText>
              <ThemedText style={styles.messageTime}>{msg.time}</ThemedText>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Received Messages */}
      <View style={styles.messageWindow}>
        <ThemedText style={styles.windowTitle}>Received Messages</ThemedText>
        <ScrollView style={styles.messagesList}>
          {receivedMessages.map((msg, index) => (
            <View key={index} style={[styles.messageCard, styles.receivedMessage]}>
              <ThemedText style={styles.topicName}>{msg.topic}</ThemedText>
              <ThemedText style={styles.messageText}>{msg.text}</ThemedText>
              <ThemedText style={styles.messageTime}>{msg.time}</ThemedText>
            </View>
          ))}
        </ScrollView>
      </View>
    </View>
  );
}; 