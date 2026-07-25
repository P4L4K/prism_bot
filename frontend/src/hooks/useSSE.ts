import { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';

export function useSSE(url: string) {
  const {
    currentBookId,
    setIsListening,
    setIsSpeaking,
    setIsThinking,
    addChatTurn,
    setLiveTranscript,
  } = useAppStore();

  useEffect(() => {
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'LISTENING_START':
            setIsListening(true);
            setLiveTranscript('');
            break;
          case 'LISTENING_STOP':
            setIsListening(false);
            break;
          case 'TRANSCRIPT':
            if (data.payload.session_id === useAppStore.getState().currentBookId) {
              setLiveTranscript(data.payload.text);
              addChatTurn({
                id: Date.now().toString() + '-user',
                role: 'user',
                text: data.payload.text,
                timestamp: new Date().toISOString(),
              });
              setIsThinking(true);
            }
            break;
          case 'RESPONSE':
            if (data.payload.session_id === useAppStore.getState().currentBookId) {
              setIsThinking(false);
              addChatTurn({
                id: Date.now().toString() + '-assistant',
                role: 'assistant',
                text: data.payload.text,
                cardData: data.payload.card_data,
                timestamp: new Date().toISOString(),
              });
              setLiveTranscript('');
            }
            break;
          case 'TTS_START':
            setIsSpeaking(true);
            break;
          case 'TTS_STOP':
            setIsSpeaking(false);
            break;
          case 'ERROR':
            addChatTurn({
              id: Date.now().toString() + '-error',
              role: 'assistant',
              text: data.payload,
              timestamp: new Date().toISOString(),
            });
            break;
          case 'HISTORY_CLEAR':
            // Could add an alert or just clear UI
            break;
          case 'connected':
            console.log('Connected to backend:', data.payload);
            break;
          default:
            console.log('Unhandled SSE:', data);
        }
      } catch (err) {
        console.error('Failed to parse SSE:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      eventSource.close();
      // Retry logic could go here
    };

    return () => {
      eventSource.close();
    };
  }, [url]);
}
