declare module 'react_native_mqtt' {
  interface MQTTConfig {
    size?: number;
    storageBackend?: any;
    defaultExpires?: number;
    enableCache?: boolean;
    sync?: object;
  }

  export default function init(config: MQTTConfig): void;
} 