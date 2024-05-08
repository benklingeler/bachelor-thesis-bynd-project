import FileUpload from '@/components/file-upload';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useReportStore } from '@/stores/report.store';
import { faDownload } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import moment from 'moment';
import { useEffect } from 'react';

export async function loader() {
  return null;
}

export function Component() {
  const { reports, loadReports } = useReportStore();

  useEffect(() => {
    // Load reports
    loadReports();
  }, []);

  return (
    <div className='border-2 p-4 rounded border-primary/20 flex flex-col gap-8'>
      <FileUpload />
      <div className='space-y-2'>
        <h3 className='text-slate-500 mb-2'>Created Reports</h3>
        {reports.length === 0 && <p>There are no reports created yet</p>}
        {reports
          .sort((a, b) => (moment(a.created_at).isAfter(moment(b.created_at)) ? -1 : 1))
          .map((report) => (
            <div className='border-2 border-primary bg-primary/10 text-primary rounded-lg py-2 px-4 cursor-pointer flex shadow-[0_0px_20px_-10px_rgba(0,0,0,0.2)] shadow-primary/40'>
              <a key={report.label} href={`/chat/${report.id}`} className='flex-1'>
                <p className='font-semibold'>{report.label}</p>
                <p className='opacity-80 text-sm'>Report created {moment(report.created_at).fromNow()}</p>
              </a>
              <TooltipProvider delayDuration={0}>
                <Tooltip>
                  <TooltipTrigger>
                    <a
                      href={`http://localhost:8000/report/${report.label}`}
                      className='flex items-center justify-center'
                      target='_blank'
                    >
                      <FontAwesomeIcon icon={faDownload} className='size-5' />
                    </a>
                  </TooltipTrigger>
                  <TooltipContent side='bottom'>
                    <p>Download PDF</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          ))}
      </div>
    </div>
  );
}
