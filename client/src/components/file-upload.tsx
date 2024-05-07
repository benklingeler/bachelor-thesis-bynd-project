import { cn } from '@/lib/utils';
import { useFileStore } from '@/stores/file.store';
import { useReportStore } from '@/stores/report.store';
import { faCircleChevronDown, faFile, faSearch, faSpinner, faTrash, faUpload } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useState } from 'react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Input } from './ui/input';

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const [label, setLabel] = useState('');

  const { uploadedFiles, setUploadedFiles } = useFileStore();

  const { loadReports } = useReportStore();

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      setUploadedFiles([files[0]]);
    }
  };

  const handleDragOver = (e: any) => {
    setIsDragging(true);
    e.preventDefault();
  };

  const handleDragLeave = (e: any) => {
    setIsDragging(false);
    e.preventDefault();
  };

  const handleDrop = (e: any) => {
    setIsDragging(false);
    e.preventDefault();
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      const file = Array.from(droppedFiles)[0] as File;
      // Check if file is json
      if (file.type !== 'application/json') {
        toast.error('Invalid file type. Please upload a JSON file');
        return;
      }
      setUploadedFiles([file]);
    }
  };

  const handleResetUpload = () => {
    setUploadedFiles([]);
  };

  const handleUpload = async () => {
    setIsUploading(true);

    if (label === '') {
      toast.error('Please provide a label for the report');
      setIsUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadedFiles[0]);
    formData.append('label', label);

    try {
      const reponse = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      if (!reponse.ok) {
        throw new Error('An error occurred while uploading the file');
      }
    } catch (error) {
      toast.error('An error occurred while uploading the file');
      setIsUploading(false);
      return;
    }

    await loadReports();

    toast.success('Report created successfully');
    setIsUploading(false);
  };

  return (
    <div className='border-dashed border-2 rounded-lg p-12 flex items-center justify-center gap-0 flex-col border-primary/40 relative'>
      {uploadedFiles.length > 0 ? (
        <div className='flex flex-col'>
          <div className='flex gap-2 items-center'>
            <FontAwesomeIcon icon={faFile} className='text-primary' />
            <p>{uploadedFiles[0].name}</p>
            <p className='text-slate-500'>{(uploadedFiles[0].size / 1024 / 1024).toFixed(2)}mb</p>
          </div>
          <Input
            className='mt-6'
            placeholder='Label for the report'
            value={label}
            onChange={(event) => setLabel(event.target.value)}
          />
          <div className='flex gap-4'>
            <Button className='mt-6' onClick={handleUpload}>
              <FontAwesomeIcon
                icon={isUploading ? faSpinner : faSearch}
                className={cn('mr-2', isUploading && 'animate-spin')}
              />{' '}
              Analyze Model Results
            </Button>
            <Button className='mt-6' variant={'outline'} onClick={handleResetUpload}>
              <FontAwesomeIcon icon={faTrash} className='mr-2' /> Reset Upload
            </Button>
          </div>
        </div>
      ) : (
        <>
          <input id='file' type='file' className='hidden' onChange={handleFileUpload} accept='application/json' />
          <label
            htmlFor='file'
            className='absolute top-0 left-0 w-full h-full cursor-pointer z-10'
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragEnd={handleDragLeave}
            onDragExit={handleDragLeave}
            onDragLeave={handleDragLeave}
          ></label>
          {isDragging ? (
            <>
              <div className='flex flex-col items-center justify-center absolute left-0 top-0 w-full h-full z-0'>
                <FontAwesomeIcon icon={faCircleChevronDown} className='size-12 text-primary' />
                <p className='text-2xl font-semibold uppercase tracking-wider mt-6'>Release to select</p>
              </div>
              <div className='flex flex-col items-center justify-center invisible'>
                <FontAwesomeIcon icon={faUpload} className='size-12 text-primary' />
                <p className='text-2xl font-semibold uppercase tracking-wider mt-6'>File upload</p>
                <p className='text-slate-500'>Drag a file into the field</p>
                <Button className='mt-6'>Select File</Button>
              </div>
            </>
          ) : (
            <div className='flex flex-col items-center justify-center'>
              <FontAwesomeIcon icon={faUpload} className='size-12 text-primary' />
              <p className='text-2xl font-semibold uppercase tracking-wider mt-6'>File upload</p>
              <p className='text-slate-500'>Drag a file into the field</p>
              <Button className='mt-6'>Select File</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
