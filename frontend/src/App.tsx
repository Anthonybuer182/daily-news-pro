import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Rules from './pages/Rules'
import Jobs from './pages/Jobs'
import Articles from './pages/Articles'

const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Content style={{ margin: '16px', padding: '24px', background: '#fff' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/rules" element={<Rules />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/articles" element={<Articles />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
