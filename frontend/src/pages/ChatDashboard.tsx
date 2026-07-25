import { useState, useEffect } from 'react';
import { useAppStore, type ChatTurn } from '../store/useAppStore';
import { Send, Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

export const ChatDashboard = () => {
  const { currentBookId, chatHistory, setChatHistory, liveTranscript, isListening } = useAppStore();
  const [inputText, setInputText] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/api/history?limit=50&session_id=${currentBookId}`);
        const turns = res.data;
        const history: ChatTurn[] = [];
        // turns are returned newest first usually, so let's reverse them to chronological
        const chronological = turns.reverse();
        chronological.forEach((t: any) => {
          if (t.user_input) {
            history.push({ id: t.id + '-u', role: 'user', text: t.user_input, timestamp: t.timestamp });
          }
          if (t.assistant_response) {
            history.push({ id: t.id + '-a', role: 'assistant', text: t.assistant_response, timestamp: t.timestamp });
          }
        });
        setChatHistory(history);
      } catch (err) {
        console.error('Failed to load chat history', err);
      }
    };
    fetchHistory();
  }, [currentBookId]);

  const handleSend = async () => {
    if (!inputText.trim()) return;
    const textToSend = inputText.trim();
    
    // Optimistic UI update for zero lag
    useAppStore.getState().addChatTurn({
      id: Date.now().toString() + '-user',
      role: 'user',
      text: textToSend,
      timestamp: new Date().toISOString(),
    });
    
    setInputText('');
    
    try {
      await axios.post('http://localhost:8000/api/chat', { text: textToSend, session_id: currentBookId });
    } catch (e) {
      console.error(e);
    }
  };

  const handleListen = async () => {
    try {
      await axios.post('http://localhost:8000/api/listen');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[var(--color-surface)]">
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6 flex flex-col">
        {chatHistory.length === 0 && !liveTranscript && (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-text-muted)]">
            <div className="w-24 h-24 mb-6 rounded-3xl bg-[var(--color-primary-soft)] flex items-center justify-center animate-bounce">
              <span className="text-4xl">✨</span>
            </div>
            <h2 className="text-2xl font-bold text-[var(--color-text-pri)]">Hi! I'm PRISM.</h2>
            <p className="mt-2">How can I help you today?</p>
          </div>
        )}

        <AnimatePresence>
          {chatHistory.map((turn) => (
            <motion.div
              key={turn.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`flex ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`whitespace-pre-wrap max-w-[70%] p-4 rounded-2xl ${
                  turn.role === 'user' 
                    ? 'bg-[var(--color-primary)] text-white rounded-tr-sm' 
                    : 'glass-card text-[var(--color-text-pri)] rounded-tl-sm'
                }`}
              >
                {turn.text}
              </div>
            </motion.div>
          ))}
          {liveTranscript && (
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              className="flex justify-end"
            >
              <div className="max-w-[70%] p-4 rounded-2xl bg-[var(--color-primary-soft)] text-[var(--color-primary-light)] rounded-tr-sm animate-pulse">
                {liveTranscript}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <div className="p-6 bg-white/50 backdrop-blur-md border-t border-[var(--color-border-card)]">
        <div className="max-w-4xl mx-auto flex items-center gap-4 relative">
          
          <button 
            onClick={handleListen}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              isListening 
                ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30' 
                : 'bg-[var(--color-primary-soft)] text-[var(--color-primary-light)] hover:bg-[var(--color-primary)] hover:text-white'
            }`}
          >
            <Mic size={24} />
          </button>

          <div className="flex-1 relative group">
            <input 
              type="text" 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your message..."
              className="w-full pl-6 pr-14 py-4 rounded-2xl border-none bg-[var(--color-card)] text-[var(--color-text-pri)] focus:ring-2 focus:ring-[var(--color-primary)] shadow-sm text-lg transition-shadow"
            />
            <button 
              onClick={handleSend}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-[var(--color-primary)] flex items-center justify-center text-white hover:bg-[var(--color-primary-light)] shadow-md"
            >
              <Send size={18} />
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};
