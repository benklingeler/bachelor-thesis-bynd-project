import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/stores/chat.store';
import { useReportStore } from '@/stores/report.store';
import { faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useEffect, useRef, useState } from 'react';
import { LoaderFunctionArgs, redirect, useLoaderData } from 'react-router-dom';

export async function loader({ request, params }: LoaderFunctionArgs<{ id: string }>) {
  if (!params.id) {
    redirect('/');
    return { chatId: -1 };
  }

  const chatId = parseInt(params.id);

  return { chatId };
}
type LoaderData = Awaited<ReturnType<typeof loader>>;

export function Component() {
  const [chatMessage, setChatMessage] = useState('');
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const { reports, loadReports } = useReportStore();
  const { messages, addMessage, streamingMessage, setStreamingMessage } = useChatStore();
  const chat = useRef<HTMLDivElement>(null);

  const { chatId } = useLoaderData() as LoaderData;

  useEffect(() => {
    // Load reports
    loadReports();

    // Create websocket and connect to localhost:3000
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => {
      console.log('Connected to localhost:8000');

      ws.send(JSON.stringify({ chatId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (Object.keys(data).includes('message')) {
        setStreamingMessage(data.message, data.isFinished);
        // Scroll chat div down
        chat.current?.scrollTo(0, chat.current.scrollHeight);
      }
    };

    setWebsocket(ws);
  }, []);

  const sendMessage = () => {
    addMessage({ author: 'user', content: chatMessage });
    websocket?.send(JSON.stringify({ chatId, message: chatMessage }));
    chat.current?.scrollTo(0, chat.current.scrollHeight);
    setChatMessage('');
  };

  useEffect(() => {
    chat.current?.scrollTo(0, chat.current.scrollHeight);
  }, [messages]);

  return (
    <div className='border-2 p-4 rounded-lg border-primary/20 flex flex-col gap-8'>
      <div>
        <div ref={chat} className='chat max-h-[50vh] overflow-y-auto'>
          {messages.map((message, index) => (
            <div key={index} className={cn('flex flex-col gap-1', message.author == 'user' && 'items-end')}>
              <div className='uppercase text-slate-500'>{message.author}</div>
              <div
                className='w-3/4 rounded-lg bg-primary/5 p-2'
                dangerouslySetInnerHTML={{ __html: message.content }}
              ></div>
            </div>
          ))}
          {streamingMessage.length > 0 && (
            <div className='flex flex-col gap-1'>
              <div className='uppercase text-slate-500'>system</div>
              <div
                className='w-3/4 rounded-lg bg-primary/5 p-2'
                dangerouslySetInnerHTML={{ __html: streamingMessage }}
              ></div>
            </div>
          )}
        </div>
        <div className='flex gap-4 mt-8'>
          <Input
            className='bg-primary/10'
            placeholder='Ask a question'
            value={chatMessage}
            onChange={(event) => setChatMessage(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && sendMessage()}
          />
          <Button onClick={sendMessage}>
            <FontAwesomeIcon icon={faPaperPlane} className='mr-2' /> Send Message
          </Button>
        </div>
      </div>
    </div>
  );
}
