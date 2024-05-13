import { cn } from '@/lib/utils';
import { faBrain, faBriefcase, faCheck, faGears, faUser } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';

export type ProfileSelectionProps = {
  selectedProfile: string;
  setSelectedProfile: (profile: string) => void;
};
export default function ProfileSelection({ selectedProfile, setSelectedProfile }: ProfileSelectionProps) {
  return (
    <Dialog>
      <DialogTrigger>
        <Button variant='outline'>
          {selectedProfile == 'non_technical' && (
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faUser} className='size-5' />
              <p className='font-semibold flex-1'>Non Technical</p>
            </div>
          )}
          {selectedProfile == 'technical' && (
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faGears} className='size-5' />
              <p className='font-semibold flex-1'>Technical</p>
            </div>
          )}
          {selectedProfile == 'business' && (
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faBriefcase} className='size-5' />
              <p className='font-semibold flex-1'>Business</p>
            </div>
          )}
          {selectedProfile == 'expert' && (
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faBrain} className='size-5' />
              <p className='font-semibold flex-1'>Expert</p>
            </div>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className='dark'>
        <DialogHeader>
          <DialogTitle className='text-primary'>User Profile</DialogTitle>
          <DialogDescription>
            Changing the profile will remove previous messages from the context of the chat, for any following
            conversation. The messages will still be shown in chat.{' '}
          </DialogDescription>
        </DialogHeader>
        <div className='flex flex-col gap-2'>
          <div
            className={cn(
              'border rounded-lg text-foreground cursor-pointer p-4 gap-2 flex flex-col',
              selectedProfile == 'non_technical' ? 'border-primary' : 'cursor-pointer'
            )}
            onClick={() => setSelectedProfile('non_technical')}
          >
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faUser} className='size-5' />
              <p className='font-semibold flex-1'>Non Technical</p>
              {selectedProfile == 'non_technical' && <FontAwesomeIcon icon={faCheck} className='text-primary' />}
            </div>
            <p className='text-sm text-slate-500'>
              Suited for non-technical personnel. Answers will be given in a non-technical manner, without technical
              jargon.
            </p>
          </div>
          <div
            className={cn(
              'border rounded-lg text-foreground cursor-pointer p-4 gap-2 flex flex-col',
              selectedProfile == 'technical' ? 'border-primary' : 'cursor-pointer'
            )}
            onClick={() => setSelectedProfile('technical')}
          >
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faGears} className='size-5' />
              <p className='font-semibold flex-1'>Technical</p>
              {selectedProfile == 'technical' && <FontAwesomeIcon icon={faCheck} className='text-primary' />}
            </div>
            <p className='text-sm text-slate-500'>
              Answers will be given in a technical manner, with technical jargon. Suited for technical personnel.
            </p>
          </div>
          <div
            className={cn(
              'border rounded-lg text-foreground cursor-pointer p-4 gap-2 flex flex-col',
              selectedProfile == 'business' ? 'border-primary' : 'cursor-pointer'
            )}
            onClick={() => setSelectedProfile('business')}
          >
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faBriefcase} className='size-5' />
              <p className='font-semibold flex-1'>Business</p>
              {selectedProfile == 'business' && <FontAwesomeIcon icon={faCheck} className='text-primary' />}
            </div>
            <p className='text-sm text-slate-500'>
              Focused on making business decisions. Answers will be explained in a business context.
            </p>
          </div>
          <div
            className={cn(
              'border rounded-lg text-foreground cursor-pointer p-4 gap-2 flex flex-col',
              selectedProfile == 'expert' ? 'border-primary' : 'cursor-pointer'
            )}
            onClick={() => setSelectedProfile('expert')}
          >
            <div className='flex items-center gap-2'>
              <FontAwesomeIcon icon={faBrain} className='size-5' />
              <p className='font-semibold flex-1'>Expert</p>
              {selectedProfile == 'expert' && <FontAwesomeIcon icon={faCheck} className='text-primary' />}
            </div>
            <p className='text-sm text-slate-500'>
              Requireds a broad knowledge of the subject. Answers will be given in a detailed and expert manner.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
