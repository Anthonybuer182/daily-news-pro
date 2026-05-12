import { Navigate, useLocation } from 'react-router-dom'
import { getToken } from '../pages/Login'

interface Props {
  children: React.ReactNode
}

export default function PrivateRoute({ children }: Props) {
  const token = getToken()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
