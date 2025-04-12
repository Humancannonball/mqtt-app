import { useState, useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export function useMQTTConnection() {
  const [messages, setMessages] = useState<Array<{ text: string; time: string; topic: string }>>([]);
  const [receivedMessages, setReceivedMessages] = useState<Array<{ text: string; time: string; topic: string }>>([]);
  const [messageToSend, setMessageToSend] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const clientRef = useRef<any>(null);

  useEffect(() => {
    const initializeMQTT = async () => {
      try {
        const init = (await import('react_native_mqtt')).default;
        init({
          size: 10000,
          storageBackend: AsyncStorage,
          defaultExpires: 1000 * 3600 * 24,
          enableCache: true,
          sync: {}
        });

        const client = new Paho.MQTT.Client(
          '192.168.31.9',
          8000,
          `expo-mqtt-${Math.random().toString(16).substr(2, 8)}`
        );

        client.onMessageArrived = (message: any) => {
          console.log("Message arrived:", {
            payload: message.payloadString,
            topic: message.destinationName,
            qos: message.qos
          });
          
          const time = new Date().toLocaleTimeString();
          setReceivedMessages(prev => [...prev, {
            text: message.payloadString,
            time,
            topic: message.destinationName
          }]);
        };

        client.onConnectionLost = (responseObject: any) => {
          if (responseObject.errorCode !== 0) {
            console.log("Connection lost:", responseObject.errorMessage);
            setError('Lost Connection');
            setIsConnected(false);
          }
        };

        client.connect({
          onSuccess: () => {
            console.log("Connected to MQTT broker");
            try {
              console.log("Subscribing to expo/test");
              client.subscribe('expo/test', {
                qos: 0,
                onSuccess: () => console.log("Successfully subscribed to expo/test"),
                onFailure: (err: any) => console.error("Subscribe failed:", err)
              });
            } catch (err) {
              console.error("Subscribe error:", err);
            }
            setIsConnected(true);
            setError(null);
          },
          onFailure: (err: any) => {
            console.error("Connection error:", err);
            setError(`Failed to connect: ${err.errorMessage}`);
            setIsConnected(false);
          },
          useSSL: false
        });

        clientRef.current = client;
      } catch (error) {
        console.error('MQTT initialization error:', error);
        setError('Failed to initialize MQTT');
      }
    };

    initializeMQTT();

    return () => {
      if (clientRef.current?.isConnected()) {
        try {
          clientRef.current.unsubscribe('expo/test');
        } catch (err) {
          console.error("Unsubscribe error:", err);
        }
        clientRef.current.disconnect();
      }
    };
  }, []);

  const sendMessage = async () => {
    if (isConnected && messageToSend && clientRef.current) {
      setIsLoading(true);
      try {
        const mqttMessage = new Paho.MQTT.Message(messageToSend);
        mqttMessage.destinationName = 'expo/test';
        
        console.log("Sending message:", messageToSend);
        clientRef.current.send(mqttMessage);
        
        const time = new Date().toLocaleTimeString();
        setMessages(prev => [...prev, {
          text: messageToSend,
          time,
          topic: 'expo/test'
        }]);
        setMessageToSend('');
      } catch (error) {
        console.error("Send error:", error);
        setError('Failed to send message');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const clearReceivedMessages = () => {
    setReceivedMessages([]);
  };

  return {
    isConnected,
    error,
    messages,
    receivedMessages,
    messageToSend,
    setMessageToSend,
    sendMessage,
    isLoading,
    clearMessages,
    clearReceivedMessages,
  };
} 
