import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Sidebar'
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
      {/* 管理后台 */}
      <Route path="/*" element={
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
                <Route path="/articles/edit/:id" element={<ArticleEdit />} />
                <Route path="/tags" element={<Tags />} />
                <Route path="/channels" element={<Channels />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/model-configs" element={<ModelConfigs />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      } />

      {/* 预览服务 */}
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
    </Routes>
  )
}

export default App
