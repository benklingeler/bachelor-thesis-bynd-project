import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

export default function Loader() {
  return (
    <div className='h-screen grid place-items-center'>
      <FontAwesomeIcon icon={faSpinner} spin />
    </div>
  );
}
