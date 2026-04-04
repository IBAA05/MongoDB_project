import { useEffect, useRef } from 'react';
import { toast } from 'sonner';

/**
 * Custom hook to manage WebSocket connection and display notifications.
 * Connects to the backend WebSocket and listens for broadcast messages.
 */
export const useWebSocket = (url = 'ws://localhost:8000/ws') => {
  const socketRef = useRef(null);

  useEffect(() => {
    const connect = () => {
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('Connected to notification WebSocket');
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different notification types
          switch (data.type) {
            case 'CREATE':
              toast.success(data.title || 'Created', {
                description: data.message,
              });
              break;
            case 'UPDATE':
              toast.info(data.title || 'Updated', {
                description: data.message,
              });
              break;
            case 'DELETE':
              toast.error(data.title || 'Deleted', {
                description: data.message,
              });
              break;
            default:
              toast(data.title || 'Notification', {
                description: data.message,
              });
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      socket.onclose = () => {
        console.log('WebSocket connection closed. Reconnecting in 3 seconds...');
        setTimeout(connect, 3000);
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        socket.close();
      };
    };

    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [url]);

  return socketRef.current;
};
