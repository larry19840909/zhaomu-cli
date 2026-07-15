import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const [isFirstTime, setIsFirstTime] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get('/api/settings').then(r => {
      setIsFirstTime(!r.data.has_password);
    }).catch(() => {
      setIsFirstTime(false);
    });
  }, []);

  const onSetup = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const resp = await apiClient.post('/api/auth/login', { password: values.password });
      localStorage.setItem('admin_token', resp.data.token);
      localStorage.setItem('admin_user', values.username);
      message.success('设置成功');
      navigate('/settings');
    } catch {
      // 错误由 apiClient 拦截器处理
    } finally {
      setLoading(false);
    }
  };

  const onLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const resp = await apiClient.post('/api/auth/login', { password: values.password });
      localStorage.setItem('admin_token', resp.data.token);
      localStorage.setItem('admin_user', values.username);
      message.success('登录成功');
      navigate('/settings');
    } catch {
      // 错误由 apiClient 拦截器处理
    } finally {
      setLoading(false);
    }
  };

  if (isFirstTime === null) return null;

  if (isFirstTime) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        minHeight: '100vh', background: '#f5f5f5',
      }}>
        <Card title="首次使用 — 创建管理员" style={{ width: 400 }}>
          <Form onFinish={onSetup} size="large">
            <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input prefix={<UserOutlined />} placeholder="用户名（随意设置）" autoFocus />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: '请设置管理密码' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="设置管理密码" />
            </Form.Item>
            <Form.Item name="confirm" dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) return Promise.resolve();
                    return Promise.reject(new Error('两次输入的密码不一致'));
                  },
                }),
              ]}>
              <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>设置密码</Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      minHeight: '100vh', background: '#f5f5f5',
    }}>
      <Card title="zhaomu 管理后台" style={{ width: 400 }}>
        <Form onFinish={onLogin} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" autoFocus />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入管理密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="管理密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>登录</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
