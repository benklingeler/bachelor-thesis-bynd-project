import { cn } from '@/lib/utils';
import { faSpinner, faUser, faWandMagicSparkles } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

type MessageProps = {
  author: 'system' | 'user';
  message: string;
  side?: 'left' | 'right';
  isStreaming?: boolean;
  isLoading?: boolean;
};
export default function Message({ author, message, side = 'left', isStreaming, isLoading }: MessageProps) {
  const avatar = (
    <div
      className={cn(
        'size-10 rounded-lg grid place-items-center p-1',
        author == 'system' ? 'bg-primary/40' : 'bg-primary/20'
      )}
    >
      {author == 'system' ? (
        <img src='/bynd-logo-white.svg' className='w-full' />
      ) : (
        <FontAwesomeIcon icon={faUser} className='text-primary' />
      )}
    </div>
  );

  const content = <div dangerouslySetInnerHTML={{ __html: message }} className=''></div>;

  return (
    <div className={cn('flex w-full items-start gap-4', side == 'left' ? 'justify-start' : 'justify-end')}>
      {side == 'left' && avatar}
      <div
        className={cn(
          'bg-primary/10 p-4 rounded-lg max-w-[60%]',
          isLoading && 'bg-violet-600 flex items-center gap-2 text-white'
        )}
      >
        {isLoading && <FontAwesomeIcon icon={faWandMagicSparkles} />}
        {content}
        {isStreaming && <MessageWritingAnimation withText />}
        {isLoading && <FontAwesomeIcon icon={faSpinner} spin />}
      </div>
      {side == 'right' && avatar}
    </div>
  );
}

type MessageWritingAnimationProps = {
  withText?: boolean;
};
function MessageWritingAnimation({ withText = false }: MessageWritingAnimationProps) {
  return (
    <div className={cn('inline-flex gap-1 items-center', withText && 'ml-2')}>
      <div className='size-[5px] rounded-full bg-white delay-100 animate-pulse duration-1000'></div>
      <div className='size-[5px] rounded-full bg-white delay-200 animate-pulse duration-1000'></div>
      <div className='size-[5px] rounded-full bg-white delay-300 animate-pulse duration-1000'></div>
    </div>
  );
}
