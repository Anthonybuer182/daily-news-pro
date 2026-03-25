import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  PlaySquareOutlined,
  ToolOutlined,
  SendOutlined,
} from '@ant-design/icons'

const { Sider } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/rules', icon: <ToolOutlined />, label: '规则管理' },
  { key: '/jobs', icon: <PlaySquareOutlined />, label: '任务管理' },
  { key: '/articles', icon: <FileTextOutlined />, label: '文章管理' },
  { key: '/channels', icon: <SendOutlined />, label: '渠道管理' },
  { key: '/model-configs', icon: <ToolOutlined />, label: '模型配置' },
  { key: '/logs', icon: <FileTextOutlined />, label: '日志管理' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Sider width={200} style={{ background: '#fff' }}>
      <div style={{ padding: '16px', fontSize: '18px', fontWeight: 'bold', textAlign: 'center' }}>
        Daily News Pro
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ height: '100%', borderRight: 0 }}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  )
}
