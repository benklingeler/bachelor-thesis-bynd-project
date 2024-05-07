import { create } from 'zustand';

type Message = {
  author: 'user' | 'system';
  content: string;
};

type ChatStore = {
  messages: Message[];
  streamingMessage: string;
  addMessage: (message: Message) => void;
  setStreamingMessage: (message: string, isFinished: boolean) => void;
};

export const useChatStore = create<ChatStore>()((set, get) => ({
  messages: [],
  addMessage: (message: Message) => set({ messages: [...get().messages, message] }),
  streamingMessage: '',
  setStreamingMessage: (message: string, isFinished: boolean) => {
    if (isFinished) {
      set({ streamingMessage: '' });
      set({ messages: [...get().messages, { author: 'system', content: message }] });
    } else {
      set({ streamingMessage: message });
    }
  },
}));
