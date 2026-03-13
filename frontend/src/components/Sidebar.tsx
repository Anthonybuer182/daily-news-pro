import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  SettingOutlined,
  FileTextOutlined,
  PlaySquareOutlined,
  ToolOutlined,
} from '@ant-design/icons'

const { Sider } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/rules', icon: <ToolOutlined />, label: '规则管理' },
  { key: '/jobs', icon: <PlaySquareOutlined />, label: '任务管理' },
  { key: '/articles', icon: <FileTextOutlined />, label: '文章管理' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
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
