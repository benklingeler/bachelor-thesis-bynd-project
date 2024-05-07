import { create } from 'zustand';

type Report = {
  id: string;
  label: string;
  created_at: string;
};

type ReportStore = {
  reports: Report[];
  loadReports: () => Promise<Report[]>;
};

export const useReportStore = create<ReportStore>()((set, get) => ({
  reports: [],
  loadReports: async () => {
    const response = await fetch('http://localhost:8000/reports');
    const reports = await response.json();
    set({ reports });
    return reports;
  },
}));
