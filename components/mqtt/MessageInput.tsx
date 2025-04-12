import { View, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

interface Props {
  messageToSend: string;
  setMessageToSend: (message: string) => void;
  sendMessage: () => void;
  isConnected: boolean;
  isLoading: boolean;
}

export function MessageInput({ 
  messageToSend, 
  setMessageToSend, 
  sendMessage, 
  isConnected,
  isLoading 
}: Props) {
  return (
    <View style={styles.inputWrapper}>
      <TextInput
        value={messageToSend}
        onChangeText={setMessageToSend}
        placeholder="Type a message..."
        placeholderTextColor="#666"
        style={styles.input}
        multiline
      />
      <TouchableOpacity
        style={[
          styles.sendButton,
          (!isConnected || !messageToSend) && styles.sendButtonDisabled
        ]}
        onPress={sendMessage}
        disabled={!isConnected || !messageToSend}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" size="small" />
        ) : (
          <Ionicons name="send" size={24} color="#fff" />
        )}
      </TouchableOpacity>
    </View>
  );
} 