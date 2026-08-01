'use client';
import { useEffect } from 'react';
import { useNotificationStore } from '@/stores/notificationStore';

export default function SSEProvider({ children }: { children: React.ReactNode }) {
  const addNotification = useNotificationStore((s) => s.addNotification);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimer: NodeJS.Timeout;

    const connect = () => {
      if (eventSource) eventSource.close();
      eventSource = new EventSource('/api/notifications');

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ping') return;
          addNotification({
            id: `${Date.now()}`,
            type: data.type || 'REPORT_PROCESSED',
            title: data.title || 'New Event',
            message: data.message || data.data || '',
            reportId: data.reportId,
            timestamp: new Date(),
            read: false,
          });
        } catch {}
      };

      eventSource.onerror = () => {
        eventSource?.close();
        reconnectTimer = setTimeout(connect, 10000);
      };
    };

    connect();

    return () => {
      eventSource?.close();
      clearTimeout(reconnectTimer);
    };
  }, [addNotification]);

  return <>{children}</>;
}
