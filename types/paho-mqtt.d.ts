declare namespace Paho {
  namespace MQTT {
    class Client {
      constructor(
        host: string,
        port: number,
        clientId: string
      );
      connect(options: {
        onSuccess: () => void;
        onFailure: (err: any) => void;
        useSSL?: boolean;
      }): void;
      subscribe(topic: string): void;
      unsubscribe(topic: string): void;
      send(message: Message): void;
      disconnect(): void;
      isConnected(): boolean;
      onMessageArrived: (message: Message) => void;
      onConnectionLost: (responseObject: { errorCode: number; errorMessage: string }) => void;
    }

    class Message {
      constructor(payload: string);
      destinationName: string;
      payloadString: string;
    }
  }
}

declare var Paho: typeof Paho; 