import { View, TouchableOpacity, ScrollView, Alert, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { styles as mqttStyles } from '@/components/mqtt/styles';
import { useState } from 'react';
import { TextInput } from 'react-native';

const CustomButton = ({ 
  onPress, 
  title, 
  style, 
  textStyle 
}: { 
  onPress: () => void, 
  title: string, 
  style?: any, 
  textStyle?: any 
}) => (
  <Pressable 
    onPress={onPress}
    style={({pressed}) => [
      mqttStyles.button,
      style,
      {opacity: pressed ? 0.8 : 1}
    ]}
  >
    <ThemedText style={[mqttStyles.buttonText, textStyle]}>{title}</ThemedText>
  </Pressable>
);

const styles = StyleSheet.create({
  topicsList: {
    flex: 1,
    marginTop: 8,
  },

  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },

  addTopicForm: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },

  activeTopicItem: {
    borderLeftWidth: 4,
    borderLeftColor: '#34C759',
  },
  
  actionButton: {
    padding: 8,
    marginLeft: 8,
  },
  
  topicStatus: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  
  statusText: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#F0F0F0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
});

export default function TopicsScreen() {
  const [topics, setTopics] = useState([
    { 
      name: 'expo/test', 
      description: 'Test topic',
      isSubscribed: false,
      isPublishing: false
    },
    { 
      name: 'home/temperature', 
      description: 'Temperature sensors',
      isSubscribed: false,
      isPublishing: false
    },
    { 
      name: 'home/humidity', 
      description: 'Humidity sensors',
      isSubscribed: false,
      isPublishing: false
    },
    { 
      name: 'devices/status', 
      description: 'Device status updates',
      isSubscribed: false,
      isPublishing: false
    },
  ]);
  const [showAddTopic, setShowAddTopic] = useState(false);
  const [newTopicName, setNewTopicName] = useState('');
  const [newTopicDescription, setNewTopicDescription] = useState('');

  const handleAddTopic = () => {
    if (!newTopicName.trim()) {
      Alert.alert('Error', 'Topic name is required');
      return;
    }
    setTopics([...topics, { name: newTopicName, description: newTopicDescription, isSubscribed: false, isPublishing: false }]);
    setNewTopicName('');
    setNewTopicDescription('');
    setShowAddTopic(false);
  };

  const handleDeleteTopic = (index: number) => {
    Alert.alert(
      'Delete Topic',
      'Are you sure you want to delete this topic?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          onPress: () => {
            const newTopics = [...topics];
            newTopics.splice(index, 1);
            setTopics(newTopics);
          },
          style: 'destructive'
        },
      ]
    );
  };

  const toggleSubscription = (index: number) => {
    const newTopics = [...topics];
    newTopics[index].isSubscribed = !newTopics[index].isSubscribed;
    setTopics(newTopics);
    
    if (newTopics[index].isSubscribed) {
      // Subscribe to MQTT topic
      // You'll need to implement this using your MQTT client
      console.log(`Subscribing to ${newTopics[index].name}`);
    } else {
      // Unsubscribe from MQTT topic
      console.log(`Unsubscribing from ${newTopics[index].name}`);
    }
  };

  const togglePublishing = (index: number) => {
    const newTopics = [...topics];
    newTopics[index].isPublishing = !newTopics[index].isPublishing;
    setTopics(newTopics);
  };

  return (
    <ThemedView style={mqttStyles.container}>
      <View style={mqttStyles.header}>
        <ThemedText style={mqttStyles.headerTitle}>MQTT Topics</ThemedText>
        <TouchableOpacity 
          style={mqttStyles.addButton}
          onPress={() => setShowAddTopic(true)}
        >
          <Ionicons name="add-circle" size={28} color="#007AFF" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.topicsList}>
        {topics.map((topic, index) => (
          <TouchableOpacity 
            key={index}
            style={[mqttStyles.topicItem, topic.isSubscribed && styles.activeTopicItem]}
            activeOpacity={0.7}
          >
            <View style={mqttStyles.topicHeader}>
              <ThemedText style={mqttStyles.topicName}>{topic.name}</ThemedText>
              <View style={mqttStyles.topicActions}>
                <TouchableOpacity 
                  onPress={() => toggleSubscription(index)}
                  style={styles.actionButton}
                >
                  <Ionicons 
                    name={topic.isSubscribed ? "notifications" : "notifications-outline"} 
                    size={22} 
                    color={topic.isSubscribed ? "#34C759" : "#666"} 
                  />
                </TouchableOpacity>
                <TouchableOpacity 
                  onPress={() => togglePublishing(index)}
                  style={styles.actionButton}
                >
                  <Ionicons 
                    name={topic.isPublishing ? "radio" : "radio-outline"} 
                    size={22} 
                    color={topic.isPublishing ? "#007AFF" : "#666"} 
                  />
                </TouchableOpacity>
                <TouchableOpacity 
                  onPress={() => handleDeleteTopic(index)}
                  style={styles.actionButton}
                >
                  <Ionicons name="trash-outline" size={22} color="#FF3B30" />
                </TouchableOpacity>
              </View>
            </View>
            <ThemedText style={mqttStyles.topicDescription}>
              {topic.description}
            </ThemedText>
            <View style={styles.topicStatus}>
              {topic.isSubscribed && (
                <ThemedText style={styles.statusText}>Subscribed</ThemedText>
              )}
              {topic.isPublishing && (
                <ThemedText style={styles.statusText}>Publishing</ThemedText>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {showAddTopic && (
        <View style={styles.overlay}>
          <View style={styles.addTopicForm}>
            <TextInput
              style={mqttStyles.input}
              placeholder="Topic name"
              value={newTopicName}
              onChangeText={setNewTopicName}
              placeholderTextColor="#666"
            />
            <TextInput
              style={mqttStyles.input}
              placeholder="Description (optional)"
              value={newTopicDescription}
              onChangeText={setNewTopicDescription}
              placeholderTextColor="#666"
            />
            <View style={mqttStyles.formButtons}>
              <View style={mqttStyles.buttonContainer}>
                <CustomButton 
                  title="Cancel" 
                  onPress={() => setShowAddTopic(false)}
                  style={mqttStyles.cancelButton}
                  textStyle={mqttStyles.cancelButtonText}
                />
              </View>
              <View style={mqttStyles.buttonContainer}>
                <CustomButton 
                  title="Add Topic" 
                  onPress={handleAddTopic}
                  style={mqttStyles.addButton}
                  textStyle={mqttStyles.addButtonText}
                />
              </View>
            </View>
          </View>
        </View>
      )}
    </ThemedView>
  );
} 