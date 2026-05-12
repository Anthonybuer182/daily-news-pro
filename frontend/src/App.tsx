import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Sidebar'
import PrivateRoute from './components/PrivateRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Rules from './pages/Rules'
import Jobs from './pages/Jobs'
import Articles, { Edit as ArticleEdit } from './pages/Articles'
import Tags from './pages/Tags'
import Channels from './pages/Channels'
import Logs from './pages/Logs'
import ModelConfigs from './pages/ModelConfigs'
import Preview from './pages/Preview'
import ArticleDetail from './pages/Preview/ArticleDetail'
import PreviewLayout from './pages/Preview/PreviewLayout'

const { Content } = Layout

function App() {
  return (
    <Routes>
      {/* 根路径直接跳预览（公开） */}
      <Route path="/" element={<Navigate to="/preview" replace />} />

      {/* 登录页（公开） */}
      <Route path="/login" element={<Login />} />

      {/* 预览服务（公开） */}
      <Route path="/preview" element={
        <PreviewLayout>
          <Preview />
        </PreviewLayout>
      } />
      <Route path="/preview/article/:id" element={
        <PreviewLayout>
          <ArticleDetail />
        </PreviewLayout>
      } />

      {/* 管理后台（需要登录） */}
      <Route path="/*" element={
        <PrivateRoute>
          <Layout style={{ minHeight: '100vh' }}>
            <Sidebar />
            <Layout>
              <Content style={{ margin: '16px', padding: '24px', background: '#fff' }}>
                <Routes>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/rules" element={<Rules />} />
                  <Route path="/jobs" element={<Jobs />} />
                  <Route path="/articles" element={<Articles />} />
                  <Route path="/articles/edit/:id" element={<ArticleEdit />} />
                  <Route path="/tags" element={<Tags />} />
                  <Route path="/channels" element={<Channels />} />
                  <Route path="/logs" element={<Logs />} />
                  <Route path="/model-configs" element={<ModelConfigs />} />
                </Routes>
              </Content>
            </Layout>
          </Layout>
        </PrivateRoute>
      } />
    </Routes>
  )
}

export default App
