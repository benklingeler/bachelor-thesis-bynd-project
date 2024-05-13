import { faFileCsv, faFilePdf } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Outlet } from 'react-router-dom';
import { Toaster } from './ui/sonner';

export default function Layout() {
  return (
    <>
      <Toaster position='bottom-center' richColors />
      <div className='flex bg-background h-screen max-h-screen'>
        <aside className='flex flex-col w-64 border-r py-16 gap-8 bg-black/40'>
          <img src='/bynd-logo-white.svg' className='w-24 mx-auto' />
          <div>
            <div className='flex items-center gap-3 w-full px-6 py-3'>
              <FontAwesomeIcon icon={faFilePdf} className='size-5' />
              <p className='uppercase'>Reports</p>
            </div>
            <div className='flex items-center gap-3 w-full px-6 py-3'>
              <FontAwesomeIcon icon={faFileCsv} className='size-5' />
              <p className='uppercase'>Reports</p>
            </div>
            <div className='flex items-center gap-3 w-full px-6 py-3'>
              <FontAwesomeIcon icon={faFileCsv} className='size-5' />
              <p className='uppercase'>Reports</p>
            </div>
          </div>
        </aside>
        <main className='container flex-1 py-16 flex flex-col'>
          <Outlet />
        </main>
      </div>
    </>
  );
}
