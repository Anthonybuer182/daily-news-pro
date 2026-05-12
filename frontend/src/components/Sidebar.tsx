import { Layout, Menu, Modal } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  PlaySquareOutlined,
  ToolOutlined,
  SendOutlined,
  TagsOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { removeToken } from '../pages/Login'

const { Sider } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/rules', icon: <ToolOutlined />, label: '规则管理' },
  { key: '/jobs', icon: <PlaySquareOutlined />, label: '任务管理' },
  { key: '/articles', icon: <FileTextOutlined />, label: '文章管理' },
  { key: '/tags', icon: <TagsOutlined />, label: '标签管理' },
  { key: '/channels', icon: <SendOutlined />, label: '渠道管理' },
  { key: '/model-configs', icon: <ToolOutlined />, label: '模型配置' },
  { key: '/logs', icon: <FileTextOutlined />, label: '日志管理' },
  { key: '__logout__', icon: <LogoutOutlined />, label: '退出登录', danger: true },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === '__logout__') {
      Modal.confirm({
        title: '确认退出',
        content: '退出后需要重新输入密码才能访问管理后台',
        okText: '退出',
        cancelText: '取消',
        okButtonProps: { danger: true },
        onOk: () => {
          removeToken()
          navigate('/login', { replace: true })
        },
      })
      return
    }
    navigate(key)
  }

  return (
    <Sider
      width={220}
      style={{
        background: '#fff',
        borderRight: '1px solid #f0f0f0',
      }}
    >
      <div
        style={{
          padding: '20px 16px',
          fontSize: '18px',
          fontWeight: 700,
          textAlign: 'center',
          color: '#DC2626',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        Daily News Pro
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ height: '100%', borderRight: 0, padding: '12px 8px' }}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Sider>
  )
}
