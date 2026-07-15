import { useEffect, useState, useCallback } from 'react';
import {
  Card, Tabs, Table, Button, Modal, Form, Input,
  Popconfirm, message, Space,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

interface Account {
  id: number;
  name: string;
  apikey_masked: string;
  created_at: string;
}

export default function Settings() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [sosMasked, setSosMasked] = useState('');
  const [hasPassword, setHasPassword] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [pwdLoading, setPwdLoading] = useState(false);
  const [sosLoading, setSosLoading] = useState(false);
  const [addForm] = Form.useForm();
  const [pwdForm] = Form.useForm();
  const [sosForm] = Form.useForm();

  const fetchData = useCallback(async () => {
    try {
      const resp = await apiClient.get('/api/settings');
      setAccounts(resp.data.accounts || []);
      setSosMasked(resp.data.sos_token_masked || '');
      setHasPassword(resp.data.has_password);
    } catch { /* handled by interceptor */ }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAddAccount = async (values: { name: string; apikey: string }) => {
    setAddLoading(true);
    try {
      await apiClient.post('/api/accounts', values);
      message.success('账号添加成功');
      addForm.resetFields();
      setAddOpen(false);
      fetchData();
    } catch { /* handled */ }
    finally { setAddLoading(false); }
  };

  const handleDeleteAccount = async (id: number) => {
    try {
      await apiClient.delete(`/api/accounts/${id}`);
      message.success('账号已删除');
      fetchData();
    } catch { /* handled */ }
  };

  const handleSetPassword = async (values: { new_password: string }) => {
    setPwdLoading(true);
    try {
      await apiClient.put('/api/settings/password', values);
      message.success('密码已更新');
      pwdForm.resetFields();
      setHasPassword(true);
    } catch { /* handled */ }
    finally { setPwdLoading(false); }
  };

  const handleSetSos = async (values: { token: string }) => {
    setSosLoading(true);
    try {
      await apiClient.put('/api/settings/sos-token', values);
      message.success('SOS 令牌已保存');
      sosForm.resetFields();
      fetchData();
    } catch { /* handled */ }
    finally { setSosLoading(false); }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: 'API Key', dataIndex: 'apikey_masked', key: 'apikey' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作', key: 'action', render: (_: unknown, record: Account) => (
        <Popconfirm title="确定删除此账号？" onConfirm={() => handleDeleteAccount(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  const tabs = [
    {
      key: 'accounts', label: '账号管理', children: (
        <div>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddOpen(true)} style={{ marginBottom: 16 }}>添加账号</Button>
          <Table columns={columns} dataSource={accounts} rowKey="id" size="small" />
        </div>
      ),
    },
    {
      key: 'security', label: '安全设置', children: (
        <Form form={pwdForm} onFinish={handleSetPassword} layout="vertical" style={{ maxWidth: 400 }}>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, message: '请输入新密码' }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="confirm_password" label="确认密码" dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) return Promise.resolve();
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={pwdLoading}>
              {hasPassword ? '更新密码' : '设置密码'}
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'sos', label: 'SOS 令牌', children: (
        <div>
          {sosMasked && <p style={{ color: '#888' }}>当前令牌：{sosMasked}</p>}
          <Form form={sosForm} onFinish={handleSetSos} layout="vertical" style={{ maxWidth: 400 }}>
            <Form.Item name="token" label="SOS Token" rules={[{ required: true, message: '请输入 SOS 令牌' }]}>
              <Input placeholder="来自 dashboard.metrovpn.xyz" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={sosLoading}>保存</Button>
            </Form.Item>
          </Form>
        </div>
      ),
    },
  ];

  return (
    <Card title="系统设置" style={{ maxWidth: 800, margin: '40px auto' }}>
      <Tabs items={tabs} />
      <Modal title="添加账号" open={addOpen} onCancel={() => { setAddOpen(false); addForm.resetFields(); }} footer={null} destroyOnClose>
        <Form form={addForm} onFinish={handleAddAccount} layout="vertical">
          <Form.Item name="name" label="账号名称" rules={[{ required: true }]}>
            <Input placeholder="如：主账号、测试账号" />
          </Form.Item>
          <Form.Item name="apikey" label="API Key" rules={[{ required: true, message: '请输入 API Key' }]}>
            <Input.Password placeholder="zhaomu API Key" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={addLoading}>确认添加</Button>
              <Button onClick={() => { setAddOpen(false); addForm.resetFields(); }}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
