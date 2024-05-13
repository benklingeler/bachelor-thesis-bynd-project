import Message from '@/components/message';
import ProfileSelection from '@/components/profile_selection';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useChatStore } from '@/stores/chat.store';
import { useReportStore } from '@/stores/report.store';
import { faMessage, faPaperPlane, faSpinner, faWandMagicSparkles } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useEffect, useRef, useState } from 'react';
import { LoaderFunctionArgs, redirect, useLoaderData } from 'react-router-dom';

export async function loader({ params }: LoaderFunctionArgs<{ id: string }>) {
  if (!params.id) {
    redirect('/');
    return { chatId: -1 };
  }

  await useReportStore.getState().loadReports();

  const chatId = parseInt(params.id);

  return { chatId };
}
type LoaderData = Awaited<ReturnType<typeof loader>>;

export function Component() {
  const [chatMessage, setChatMessage] = useState('');
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [selectedProfile, setSelectedProfile] = useState('non_technical');

  const { reports, loadReports } = useReportStore();
  const {
    chatEntries,
    addMessage,
    addEvent,
    streamingMessage,
    setStreamingMessage,
    toolCall,
    setToolCall,
    quickActions,
    setQuickActions,
    quickActionsLoading,
    setQuickActionsLoading,
  } = useChatStore();
  const chat = useRef<HTMLDivElement>(null);

  const { chatId } = useLoaderData() as LoaderData;

  useEffect(() => {
    // Load reports
    loadReports();

    setQuickActions([
      {
        label: 'Report Summary',
        prompt:
          'Explain the results of the report and extract/highlight interesting information, based on my user profile.',
      },
      { label: 'Dataset', prompt: 'Explain the dataset that was used. Highlight not used columns from the dataset.' },
    ]);

    addMessage({
      author: 'system',
      content: `Welcome to the interactive report chat! Do you want to learn more about the <strong>${report?.label}</strong> report?`,
    });

    // Create websocket and connect to localhost:3000
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => {
      console.log('Connected to localhost:8000');

      ws.send(JSON.stringify({ type: 'initChat', chatId, user_profile: selectedProfile }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (Object.keys(data).includes('type')) {
        if (data.type === 'message') {
          setStreamingMessage(data.message, data.isFinished);
          chat.current?.scrollTo(0, chat.current.scrollHeight);
        } else if (data.type == 'tool_call') {
          setToolCall(data.name);
          chat.current?.scrollTo(0, chat.current.scrollHeight);
        } else if (data.type == 'quick_actions') {
          if (data.loading) {
            setQuickActionsLoading(true);
          } else {
            setQuickActions(data.actions);
          }
        } else if (data.type == 'user_profile_updated') {
          setSelectedProfile(data.user_profile);
          addEvent(`Profile changed to ${data.user_profile}`);
        }
      }
    };

    setWebsocket(ws);
  }, []);

  const sendPromptMessage = (prompt: string) => {
    if (streamingMessage.length > 0) return;
    addMessage({ author: 'user', content: prompt });
    websocket?.send(JSON.stringify({ type: 'message', message: prompt, user_profile: selectedProfile }));
    chat.current?.scrollTo(0, chat.current.scrollHeight);
    setStreamingMessage(' ', false);
  };

  const sendMessage = () => {
    sendPromptMessage(chatMessage);
    setChatMessage('');
  };

  useEffect(() => {
    chat.current?.scrollTo(0, chat.current.scrollHeight);
  }, [chatEntries]);

  const updateUserProfile = (profile: string) => {
    websocket?.send(JSON.stringify({ type: 'update_user_profile', user_profile: profile }));
  };

  const report = reports.find((report) => report.id == chatId.toString());

  return (
    <div className='border-2 p-4 rounded-lg border-primary/20 flex flex-col gap-8 h-full bg-gradient-to-t from-black/20 to-black/40'>
      <div className='flex items-center bg-background p-4 rounded-lg'>
        <h1 className='text-2xl font-bold flex-1'>
          <FontAwesomeIcon icon={faMessage} className='size-6 mr-2' />
          Chat
        </h1>
        <div>
          <ProfileSelection selectedProfile={selectedProfile} setSelectedProfile={updateUserProfile} />
        </div>
      </div>
      <div ref={chat} className='chat flex-1 justify-end gap-4 overflow-y-auto scroll-mr-4 h-full max-h-full'>
        <div className='space-y-2'>
          {chatEntries.map((entry, index) =>
            entry.type == 'message' ? (
              <Message
                key={index}
                author={entry.message.author}
                message={entry.message.content}
                side={entry.message.author == 'system' ? 'left' : 'right'}
              />
            ) : entry.type == 'event' && index > 0 ? (
              <p className='text-center uppercase tracking-wider text-sm text-slate-500 font-semibold px-2 py-1 w-max mx-auto rounded-lg'>
                {entry.event}
              </p>
            ) : null
          )}
          {streamingMessage.length > 0 && toolCall.length <= 0 && (
            <Message author={'system'} message={streamingMessage} side={'left'} isStreaming />
          )}
          {toolCall.length > 0 && (
            <Message author={'system'} message={`Calling method: ${toolCall}`} side={'left'} isLoading />
          )}
        </div>
      </div>
      {quickActionsLoading && (
        <div className='flex flex-col gap-2 items-center'>
          <p className='uppercase text-slate-500 text-sm tracking-wider'>Loading Quick Prompts</p>
          <FontAwesomeIcon icon={faSpinner} spin />
        </div>
      )}
      {quickActions.length > 0 && !quickActionsLoading && (
        <div className='flex flex-col gap-2 items-center'>
          <p className='uppercase text-slate-500 text-sm tracking-wider'>Quick Prompts</p>
          <div className='flex flex-wrap gap-4 w-4/5'>
            {quickActions.map((action, index) => (
              <Button
                key={index}
                onClick={() => sendPromptMessage(action.prompt)}
                variant={'outline'}
                className='flex flex-col items-start h-auto p-3 px-4 flex-1 justify-start'
              >
                <div className='flex items-center'>
                  <FontAwesomeIcon icon={faWandMagicSparkles} className='mr-2' />
                  <p className='text-base font-semibold'>{action.label}</p>
                </div>
                <p className='text-slate-500 whitespace-pre-wrap text-left'>{action.prompt}</p>
              </Button>
            ))}
          </div>
        </div>
      )}
      <div className='flex gap-4'>
        <Input
          className='bg-primary/10'
          placeholder='Ask a question'
          value={chatMessage}
          onChange={(event) => setChatMessage(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && sendMessage()}
          autoFocus
        />
        <Button onClick={sendMessage} disabled={streamingMessage.length > 0}>
          <FontAwesomeIcon icon={faPaperPlane} className='mr-2' /> Send Message
        </Button>
      </div>
    </div>
  );
}
