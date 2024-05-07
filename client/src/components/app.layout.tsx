import { Outlet } from 'react-router-dom';
import { Toaster } from './ui/sonner';

export default function Layout() {
  return (
    <>
      <Toaster position='bottom-center' richColors />
      <div className='flex min-h-screen'>
        <div className='bg-gradient-to-r from-black to-background flex-1'></div>
        <div className='max-w-5xl w-[60rem] bg-background'>
          <header className='pt-24 pb-12'>
            <div className='space-y-8'>
              <img src='/bynd-logo-primary.svg' alt='Bynd' className='w-24' />
              <div className='space-y-2'>
                <h1 className='text-4xl font-bold'>KI-Interpretation Tool</h1>
                <h2 className='text-slate-500 w-3/4'>
                  A tool to interpret and understand the predictions of a machine learning model. Chat with the model to
                  get indepth insights.
                </h2>
              </div>
            </div>
          </header>
          <main>
            <Outlet />
          </main>
        </div>
        <div className='bg-gradient-to-l from-black to-background flex-1'></div>
      </div>
    </>
  );
}
