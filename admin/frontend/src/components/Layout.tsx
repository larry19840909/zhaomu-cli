import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button } from 'antd';
import { SettingOutlined, ShoppingOutlined, CloudServerOutlined, LogoutOutlined } from '@ant-design/icons';

const items = [
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
  { key: '/products', icon: <ShoppingOutlined />, label: '选品' },
  { key: '/manage', icon: <CloudServerOutlined />, label: '管理' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    navigate('/login');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0',
      }}>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={items}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, border: 'none' }}
        />
        <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>退出</Button>
      </div>
      <Outlet />
    </div>
  );
}
