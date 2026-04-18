import { Link } from "react-router-dom";
import { ExclamationTriangleIcon, HomeIcon } from "@heroicons/react/24/outline";

function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center">
        <ExclamationTriangleIcon className="h-16 w-16 mx-auto text-yellow-500" />
        <h1 className="mt-4 text-4xl font-bold text-gray-900">404</h1>
        <p className="mt-2 text-lg text-gray-600">Page not found</p>
        <p className="mt-1 text-gray-500">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to="/dashboard"
          className="mt-6 btn-primary inline-flex items-center"
        >
          <HomeIcon className="h-5 w-5 mr-2" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
