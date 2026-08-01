export type SSECallback = (event: { type: string; data: any }) => void;

export function connectSSE(url: string, onEvent: SSECallback, onError?: (err: any) => void) {
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      onEvent(parsed);
    } catch {
      onEvent({ type: 'message', data: event.data });
    }
  };

  eventSource.onerror = (err) => {
    console.error('SSE error:', err);
    onError?.(err);
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}
