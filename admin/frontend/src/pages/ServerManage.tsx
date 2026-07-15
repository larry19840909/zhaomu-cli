import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Table, Button, Popconfirm, Tag, message, Space, Select } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ReloadOutlined, RocketOutlined, DeleteOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

interface Server {
  id: number; server_id: number; product_id: number; region_id: number;
  image: string; disk: number; payment_cycle: number; ip: string;
  status: string; ordered_at: string; deployed_at: string; account_id: number;
}
interface Account { id: number; name: string; apikey_masked: string; }
const COLORS: Record<string, string> = { provisioning: 'processing', running: 'success', deployed: 'blue', destroyed: 'default', stopped: 'warning' };
const CYCLES: Record<number, string> = { 1: '月付', 2: '季付', 3: '半年', 4: '年付' };

export default function ServerManage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(false);
  const [deploying, setDeploying] = useState<Set<number>>(new Set());
  const [destroying, setDestroying] = useState<Set<number>>(new Set());
  const pollTargetsRef = useRef<number[]>([]);

  useEffect(() => {
    apiClient.get('/api/accounts').then(r => {
      const list = r.data || [];
      setAccounts(list);
      if (list.length === 1) setAccountId(list[0].id);
    }).catch(() => {});
  }, []);

  const fetchServers = useCallback(async () => {
    if (accountId === null) return;
    setLoading(true);
    try {
      const r = await apiClient.get(`/api/servers?account_id=${accountId}`);
      setServers(r.data || []);
    } catch { }
    finally { setLoading(false); }
  }, [accountId]);

  useEffect(() => { fetchServers(); }, [fetchServers]);

  // 独立轮询：使用 ref 保持轮询目标，不依赖 servers state
  useEffect(() => {
    pollTargetsRef.current = servers.filter(s => s.status === 'provisioning').map(s => s.id);
  }, [servers]);

  useEffect(() => {
    if (accountId === null) return;
    const t = setInterval(async () => {
      const targets = pollTargetsRef.current;
      if (targets.length === 0) return;
      await Promise.all(targets.map(id =>
        apiClient.get(`/api/servers/${id}/poll?account_id=${accountId}`).catch(() => {})
      ));
      fetchServers();
    }, 30000);
    return () => clearInterval(t);
  }, [accountId, fetchServers]);

  const handleDeploy = async (dbId: number) => {
    if (accountId === null) return;
    setDeploying(p => new Set(p).add(dbId));
    try {
      const r = await apiClient.post(`/api/servers/${dbId}/deploy?account_id=${accountId}`);
      if (r.data.success) message.success('部署成功'); else message.warning(r.data.message || '部署失败');
      fetchServers();
    } catch { }
    finally { setDeploying(p => { const s = new Set(p); s.delete(dbId); return s; }); }
  };

  const handleDestroy = async (dbId: number) => {
    if (accountId === null) return;
    setDestroying(p => new Set(p).add(dbId));
    try {
      await apiClient.delete(`/api/servers/${dbId}?account_id=${accountId}`);
      message.success('已销毁');
    } catch { }
    finally { setDestroying(p => { const s = new Set(p); s.delete(dbId); return s; }); }
    fetchServers();
  };

  const handlePoll = async (dbId: number) => {
    if (accountId === null) return;
    try { await apiClient.get(`/api/servers/${dbId}/poll?account_id=${accountId}`); fetchServers(); } catch { }
  };

  const columns: ColumnsType<Server> = [
    { title: 'ID', dataIndex: 'server_id', width: 80 },
    { title: 'IP', dataIndex: 'ip', render: (v: string) => v || '—', width: 140 },
    { title: '镜像', dataIndex: 'image', ellipsis: true, width: 160 },
    { title: '磁盘', dataIndex: 'disk', render: (v: number) => `${v}G`, width: 60 },
    { title: '周期', dataIndex: 'payment_cycle', render: (v: number) => CYCLES[v] || v, width: 60 },
    { title: '状态', dataIndex: 'status', width: 100, render: (s: string) => <Tag color={COLORS[s] || 'default'}>{s}</Tag> },
    { title: '下单时间', dataIndex: 'ordered_at', width: 160 },
    { title: '操作', key: 'action', width: 220,
      render: (_: unknown, rec: Server) => (
        <Space size="small">
          <Button size="small" icon={<ReloadOutlined />} onClick={() => handlePoll(rec.id)} />
          {rec.status === 'running' && <Button size="small" type="primary" icon={<RocketOutlined />}
            loading={deploying.has(rec.id)} onClick={() => handleDeploy(rec.id)}>部署</Button>}
          {rec.status !== 'destroyed' && <Popconfirm title="确定销毁？" onConfirm={() => handleDestroy(rec.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} loading={destroying.has(rec.id)} /></Popconfirm>}
        </Space>
      )},
  ];

  return (
    <Card title="服务器管理" style={{ maxWidth: 1200, margin: '20px auto' }}
      extra={
        <Space>
          <Select placeholder="选择账户" value={accountId} onChange={setAccountId}
            style={{ minWidth: 180 }} options={accounts.map(a => ({ label: a.name, value: a.id }))} />
          <Button onClick={fetchServers} loading={loading} icon={<ReloadOutlined />}>刷新</Button>
        </Space>
      }>
      <Table columns={columns} dataSource={servers} rowKey="id" size="small" pagination={{ pageSize: 20 }} />
    </Card>
  );
}
