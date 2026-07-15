import { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button } from 'antd';
import { SettingOutlined, ShoppingOutlined, CloudServerOutlined, LogoutOutlined, DollarOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

const items = [
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
  { key: '/products', icon: <ShoppingOutlined />, label: '选品' },
  { key: '/manage', icon: <CloudServerOutlined />, label: '管理' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    apiClient.get('/api/accounts').then(r => {
      const list = r.data || [];
      if (list.length > 0) {
        return apiClient.get(`/api/balance?account_id=${list[0].id}`);
      }
    }).then(r => {
      if (r) setBalance(r.data.balance);
    }).catch(() => {});
  }, []);

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
        {balance !== null && (
          <span style={{ marginRight: 16, fontSize: 14, color: '#1677ff' }}>
            <DollarOutlined /> 余额 ¥{balance.toFixed(2)}
          </span>
        )}
        <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>退出</Button>
      </div>
      <Outlet />
    </div>
  );
}
