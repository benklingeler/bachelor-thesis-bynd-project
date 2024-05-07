import Layout from '@/components/app.layout';
import { createBrowserRouter } from 'react-router-dom';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,

    children: [
      {
        index: true,
        lazy: () => import('@/routes/home.route'),
      },
      {
        path: 'chat/:id',
        lazy: () => import('@/routes/chat.route'),
      },
    ],
  },
]);
