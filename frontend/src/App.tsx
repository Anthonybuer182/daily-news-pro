import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Rules from './pages/Rules'
import Jobs from './pages/Jobs'
import Articles from './pages/Articles'
import Preview from './pages/Preview'
import ArticleDetail from './pages/Preview/ArticleDetail'

const { Content } = Layout

function App() {
  return (
    <Routes>
      {/* 管理后台 */}
      <Route path="/" element={
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
      } />

      {/* 预览服务 */}
      <Route path="/preview" element={<Preview />} />
      <Route path="/preview/article/:id" element={<ArticleDetail />} />
    </Routes>
  )
}

export default App
