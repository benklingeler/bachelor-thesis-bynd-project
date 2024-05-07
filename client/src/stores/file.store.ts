import { create } from 'zustand';

type FileStore = {
  uploadedFiles: File[];
  setUploadedFiles: (files: File[]) => void;
  addUploadedFiles: (file: File) => void;
  removeUploadedFiles: (index: number) => void;
};

export const useFileStore = create<FileStore>()((set, get) => ({
  uploadedFiles: [],
  setUploadedFiles: (files: File[]) => set({ uploadedFiles: files }),
  addUploadedFiles: (file: File) => set({ uploadedFiles: [...get().uploadedFiles, file] }),
  removeUploadedFiles: (index: number) => {
    const files = get().uploadedFiles;
    files.splice(index, 1);
    set({ uploadedFiles: files });
  },
}));
