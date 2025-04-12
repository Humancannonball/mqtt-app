import { Image, StyleSheet, Platform, View, Text, TextInput, Button, TouchableOpacity, ActivityIndicator, ScrollView, Alert } from 'react-native';
import { useEffect, useState, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';

import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { MQTTStatus } from '@/components/mqtt/MQTTStatus';
import { MessageWindows } from '@/components/mqtt/MessageWindows';
import { MessageInput } from '@/components/mqtt/MessageInput';
import { useMQTTConnection } from '@/hooks/useMQTTConnection';

// Declare the Paho namespace to fix TypeScript errors
declare global {
  interface Window {
    Paho: any;
  }
  var Paho: any;
}

export default function HomeScreen() {
  const {
    isConnected,
    error,
    messages,
    receivedMessages,
    messageToSend,
    setMessageToSend,
    sendMessage,
    isLoading,
    selectedTopic,
    setSelectedTopic,
    subscribedTopics,
    clearMessages,
    clearReceivedMessages,
  } = useMQTTConnection();

  const handleClearAll = () => {
    Alert.alert(
      'Clear Messages',
      'Are you sure you want to clear all messages?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear All', 
          onPress: () => {
            clearMessages();
            clearReceivedMessages();
          },
          style: 'destructive'
        },
      ]
    );
  };

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#2C3E50', dark: '#1A1A1A' }}
      headerImage={
        <View style={styles.headerContainer}>
          <View style={styles.headerContent}>
            <ThemedText type="title" style={styles.headerTitle}>MQTT App</ThemedText>
            <View style={styles.headerActions}>
              <TouchableOpacity 
                style={styles.clearButton}
                onPress={handleClearAll}
              >
                <Ionicons name="trash-outline" size={24} color="#FF3B30" />
              </TouchableOpacity>
              <View style={styles.statusWrapper}>
                <MQTTStatus isConnected={isConnected} />
              </View>
            </View>
          </View>
        </View>
      }>
      <ThemedView style={styles.mainContainer}>
        {error && (
          <View style={styles.errorContainer}>
            <View style={styles.errorIconContainer}>
              <Ionicons name="warning" size={20} color="#FFF" />
            </View>
            <ThemedText style={styles.errorText}>{error}</ThemedText>
            <TouchableOpacity style={styles.dismissError}>
              <Ionicons name="close-circle" size={20} color="#FF3B30" />
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Ionicons name="arrow-up-circle" size={24} color="#4A90E2" />
            <ThemedText style={styles.statNumber}>{messages.length}</ThemedText>
            <ThemedText style={styles.statLabel}>Sent</ThemedText>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="arrow-down-circle" size={24} color="#34C759" />
            <ThemedText style={styles.statNumber}>{receivedMessages.length}</ThemedText>
            <ThemedText style={styles.statLabel}>Received</ThemedText>
          </View>
        </View>

        <View style={styles.contentWrapper}>
          <MessageWindows
            sentMessages={messages}
            receivedMessages={receivedMessages}
          />

          <MessageInput
            messageToSend={messageToSend}
            setMessageToSend={setMessageToSend}
            sendMessage={sendMessage}
            isConnected={isConnected}
            isLoading={isLoading}
            style={{ marginTop: 16 }}
          />
        </View>
      </ThemedView>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  headerContainer: {
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    justifyContent: 'flex-end',
    paddingBottom: 20,
  },
  headerContent: {
    alignItems: 'center',
    padding: 20,
  },
  headerTitle: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 16,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 4,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginTop: 12,
  },
  clearButton: {
    backgroundColor: 'rgba(255, 59, 48, 0.1)',
    padding: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 59, 48, 0.2)',
  },
  statusWrapper: {
    marginTop: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 20,
    padding: 8,
    paddingHorizontal: 16,
  },
  mqttLogo: {
    width: 90,
    height: 90,
    resizeMode: 'contain',
    tintColor: '#FFFFFF',
  },
  mainContainer: {
    flex: 1,
    padding: 16,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
    marginTop: -24,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
    marginTop: 10,
    gap: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
    color: '#2C3E50',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  contentWrapper: {
    flex: 1,
    gap: 16,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FF3B30',
    shadowColor: '#FF3B30',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  errorIconContainer: {
    backgroundColor: '#FF3B30',
    borderRadius: 20,
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: '#FF3B30',
    marginLeft: 12,
    flex: 1,
    fontSize: 14,
  },
  dismissError: {
    padding: 4,
  },
  messagesSection: {
    flex: 1,
    flexDirection: 'row',
    gap: 12,
  },
  messageWindow: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  windowTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    color: '#1A2C42',
  },
  messagesList: {
    flex: 1,
  },
  receivedMessage: {
    borderLeftWidth: 4,
    borderLeftColor: '#34C759',
    backgroundColor: '#F8F9FA',
  },
  sentMessage: {
    borderLeftWidth: 4,
    borderLeftColor: '#4A90E2',
    backgroundColor: '#F8F9FA',
  },
  emptyState: {
    textAlign: 'center',
    color: '#8E8E93',
    marginTop: 32,
    fontStyle: 'italic',
  },
  messageCard: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  messageText: {
    fontSize: 16,
    marginBottom: 8,
    color: '#1A2C42',
    lineHeight: 22,
  },
  messageTime: {
    fontSize: 12,
    color: '#8E8E93',
    alignSelf: 'flex-end',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    paddingHorizontal: 16,
    paddingVertical: 8,
    fontSize: 16,
    color: '#1A2C42',
    lineHeight: 22,
  },
  sendButton: {
    backgroundColor: '#4A90E2',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 12,
    shadowColor: '#4A90E2',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  sendButtonDisabled: {
    backgroundColor: '#C7C7CC',
    shadowOpacity: 0,
  },
});
