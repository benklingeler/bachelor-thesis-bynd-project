import { create } from 'zustand';

type QuickAction = {
  label: string;
  prompt: string;
};

type Message = {
  author: 'user' | 'system';
  content: string;
};

type ChatEntry =
  | {
      type: 'message';
      message: Message;
    }
  | {
      type: 'event';
      event: string;
    };

type ChatStore = {
  chatEntries: ChatEntry[];
  streamingMessage: string;
  toolCall: string;
  setToolCall: (toolCall: string) => void;
  addMessage: (message: Message) => void;
  addEvent: (event: string) => void;
  setStreamingMessage: (message: string, isFinished: boolean) => void;
  quickActions: QuickAction[];
  quickActionsLoading: boolean;
  setQuickActions: (quickActions: QuickAction[]) => void;
  setQuickActionsLoading: (loading: boolean) => void;
};

export const useChatStore = create<ChatStore>()((set, get) => ({
  chatEntries: [],
  addMessage: (message: Message) => set({ chatEntries: [...get().chatEntries, { type: 'message', message }] }),
  addEvent: (event: string) => set({ chatEntries: [...get().chatEntries, { type: 'event', event }] }),
  toolCall: '',
  setToolCall: (toolCall: string) => set({ toolCall }),
  streamingMessage: '',
  setStreamingMessage: (message: string, isFinished: boolean) => {
    set({ toolCall: '' });
    if (isFinished) {
      set({ streamingMessage: '' });
      set({
        chatEntries: [...get().chatEntries, { type: 'message', message: { author: 'system', content: message } }],
      });
    } else {
      set({ streamingMessage: message });
    }
  },
  quickActions: [],
  setQuickActions: (quickActions: QuickAction[]) => set({ quickActions, quickActionsLoading: false }),
  quickActionsLoading: false,
  setQuickActionsLoading: (loading: boolean) => set({ quickActionsLoading: loading }),
}));
