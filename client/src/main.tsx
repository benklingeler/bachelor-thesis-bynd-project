import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import Loader from './components/loader';
import './global.css';
import { router } from './lib/router';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <RouterProvider router={router} fallbackElement={<Loader />} />
);
