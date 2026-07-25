import { create } from 'zustand';

export interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
  cardData?: any;
}

interface AppState {
  currentView: 'chat' | 'history' | 'settings';
  setCurrentView: (view: 'chat' | 'history' | 'settings') => void;

  currentBookId: string;
  setCurrentBookId: (id: string) => void;

  isListening: boolean;
  setIsListening: (val: boolean) => void;

  isSpeaking: boolean;
  setIsSpeaking: (val: boolean) => void;

  isThinking: boolean;
  setIsThinking: (val: boolean) => void;

  chatHistory: ChatTurn[];
  setChatHistory: (history: ChatTurn[]) => void;
  addChatTurn: (turn: ChatTurn) => void;
  clearChat: () => void;

  liveTranscript: string;
  setLiveTranscript: (text: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentView: 'chat',
  setCurrentView: (view) => set({ currentView: view }),

  currentBookId: crypto.randomUUID(),
  setCurrentBookId: (id) => set({ currentBookId: id, chatHistory: [] }),

  isListening: false,
  setIsListening: (val) => set({ isListening: val }),

  isSpeaking: false,
  setIsSpeaking: (val) => set({ isSpeaking: val }),

  isThinking: false,
  setIsThinking: (val) => set({ isThinking: val }),

  chatHistory: [],
  setChatHistory: (history) => set({ chatHistory: history }),
  addChatTurn: (turn) => set((state) => ({ chatHistory: [...state.chatHistory, turn] })),
  clearChat: () => set({ chatHistory: [] }),

  liveTranscript: '',
  setLiveTranscript: (text) => set({ liveTranscript: text }),
}));
