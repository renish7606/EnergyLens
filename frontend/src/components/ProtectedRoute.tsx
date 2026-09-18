import {Navigate,useLocation} from 'react-router-dom';import {useAuth} from '../auth';
export function ProtectedRoute({children}:{children:React.ReactNode}){const {isAuthenticated}=useAuth();const location=useLocation();return isAuthenticated?<>{children}</>:<Navigate to="/login" replace state={{from:location.pathname}}/>}
