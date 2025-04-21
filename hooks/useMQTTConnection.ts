import { useState, useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as WebBrowser from 'expo-web-browser';
import { Platform, Linking, Alert } from 'react-native';

export function useMQTTConnection() {
  const [messages, setMessages] = useState<Array<{ text: string; time: string; topic: string }>>([]);
  const [receivedMessages, setReceivedMessages] = useState<Array<{ text: string; time: string; topic: string }>>([]);
  const [messageToSend, setMessageToSend] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const clientRef = useRef<any>(null);

  const openURL = async (url: string) => {
    try {
      console.log(`Attempting to open URL: ${url}`);

      // Make sure URL has a protocol
      let formattedUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        formattedUrl = `https://${url}`;
        console.log(`Added https protocol: ${formattedUrl}`);
      }

      if (Platform.OS === 'web') {
        window.open(formattedUrl, '_blank');
        console.log(`Opened URL in browser tab: ${formattedUrl}`);
      } else {
        // Show loading indicator to user
        setIsLoading(true);

        try {
          await WebBrowser.openBrowserAsync(formattedUrl);
          console.log(`Opened URL with WebBrowser: ${formattedUrl}`);
        } catch (error) {
          console.error('WebBrowser error:', error);
          // Fallback to basic linking
          try {
            const supported = await Linking.canOpenURL(formattedUrl);
            if (supported) {
              await Linking.openURL(formattedUrl);
              console.log(`Opened URL with Linking: ${formattedUrl}`);
            } else {
              console.error(`Cannot open URL: ${formattedUrl}`);
              Alert.alert("Cannot Open Link", `Unable to open: ${formattedUrl}`);
            }
          } catch (linkError) {
            console.error('Linking error:', linkError);
            Alert.alert("Error Opening Link", "Please try again later");
          }
        } finally {
          setIsLoading(false);
        }
      }
    } catch (error) {
      console.error('Error in openURL:', error);
      setError(`Failed to open link: ${error.message}`);
      setIsLoading(false);
    }
  };

  const handleMessage = (message: any) => {
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

    // Handle special messages
    if (message.destinationName === 'expo/result') {
      const content = message.payloadString;

      // Handle URL opening commands
      if (content.startsWith('open_url:')) {
        const url = content.substring(9); // Remove 'open_url:' prefix
        console.log("Received direct URL to open:", url);
        openURL(url);
      } else {
        // Try to parse JSON responses (especially from IMDB search)
        try {
          const jsonContent = JSON.parse(content);
          console.log("Parsed JSON response:", jsonContent);

          // Check for any URL field to open (try multiple possible fields)
          const urlToOpen = jsonContent.open_url || jsonContent.url_content ||
                           jsonContent.url || jsonContent.link;

          if (urlToOpen) {
            console.log("Found URL in JSON response:", urlToOpen);
            openURL(urlToOpen);
          }

          // Add a received message for the content
          if (jsonContent.name) {
            setReceivedMessages(prev => [...prev, {
              text: `Found: ${jsonContent.name} - ${jsonContent.description || ''}`,
              time: new Date().toLocaleTimeString(),
              topic: 'IMDB Result'
            }]);
          }
        } catch (e) {
          // Not a JSON message or no URL to open, just display the message
          console.log("Not a JSON message or no URL to open");
        }
      }
    }
  };

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
          '192.168.1.105',
          8000,
          `expo-mqtt-${Math.random().toString(16).substr(2, 8)}`
        );

        client.onMessageArrived = handleMessage;

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
              // Subscribe to both the test topic and result topic
              console.log("Subscribing to expo/test");
              client.subscribe('expo/test');
              console.log("Subscribing to expo/result");
              client.subscribe('expo/result');
              console.log("Subscribing to expo/status");
              client.subscribe('expo/status');
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
          clientRef.current.unsubscribe('expo/result');
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
