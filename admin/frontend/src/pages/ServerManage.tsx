import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Card, Table, Button, Popconfirm, Tag, message, Space, Modal, Select, Tabs, Descriptions, Tooltip, Input } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ReloadOutlined, RocketOutlined, DeleteOutlined, CopyOutlined, EyeOutlined, SyncOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

interface Server {
  id: number; server_id: number; product_id: number; region_id: number;
  account_id: number; account_name: string; batch_id: string;
  image: string; disk: number; payment_cycle: number; ip: string;
  status: string; deploy_status: string; ordered_at: string; deployed_at: string;
  country: string; city: string; ip_type: string; has_refund: number;
}

interface ServerDetail {
  id?: number; server_id?: number; ip?: string; status?: string;
  root?: string; password?: string; password_raw?: string;
  cpu?: number; ram?: number; disk?: number; diskData?: number; diskMedia?: string;
  traffic?: number; image?: string;
  startTime?: string; endTime?: string; isAutoRenew?: number;
  country?: string; city?: string; ip_type?: string;
  ordered_at?: string;
}

const COLORS: Record<string, string> = { 运行中: 'success', 已部署: 'blue', 已销毁: 'default' };
function statusColor(s: string) { return COLORS[s] || (s === '—' || s === '' ? 'default' : 'processing'); }

export default function ServerManage() {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(false);
  const [deploying, setDeploying] = useState<Set<number>>(new Set());
  const [destroying, setDestroying] = useState<Set<number>>(new Set());
  const [deleting, setDeleting] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<'active' | 'destroyed'>('active');

  // 详情弹窗
  const [detailTarget, setDetailTarget] = useState<Server | null>(null);
  const [detailData, setDetailData] = useState<ServerDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [lastDetailRefresh, setLastDetailRefresh] = useState(0);

  // 部署弹窗
  const [deployTarget, setDeployTarget] = useState<number | null>(null);
  const [deployGroup, setDeployGroup] = useState('HighSpeed Server');
  const [deployMsg, setDeployMsg] = useState('');
  const [deployError, setDeployError] = useState(false);

  // 筛选状态 — undefined = 不筛选
  const [filterState, setFilterState] = useState<Record<string, string | undefined>>({});

  const pollTargetsRef = useRef<number[]>([]);
  const lastRefreshRef = useRef(0);
  const REFRESH_COOLDOWN = 15000;
  const DETAIL_REFRESH_COOLDOWN = 15000;

  const fetchServers = useCallback(async () => {
    setLoading(true);
    try {
      const r = await apiClient.get('/api/servers');
      setServers(r.data || []);
    } catch (e: any) { message.error(e?.response?.data?.detail || "加载失败"); }
    finally { setLoading(false); }
    lastRefreshRef.current = Date.now();
  }, []);

  const handleRefresh = useCallback(() => {
    const now = Date.now();
    if (now - lastRefreshRef.current < REFRESH_COOLDOWN) {
      setLoading(true);
      setTimeout(() => setLoading(false), 400);
      return;
    }
    lastRefreshRef.current = now;
    fetchServers();
  }, [fetchServers]);

  useEffect(() => { fetchServers(); }, [fetchServers]);

  useEffect(() => {
    pollTargetsRef.current = servers.filter(s => s.status !== '运行中' && s.status !== '已销毁').map(s => s.id);
  }, [servers]);

  useEffect(() => {
    const t = setInterval(async () => {
      const targets = pollTargetsRef.current;
      if (targets.length === 0) return;
      await Promise.all(targets.map(id =>
        apiClient.get(`/api/servers/${id}/poll`).catch(() => {})
      ));
      fetchServers();
    }, 30000);
    return () => clearInterval(t);
  }, [fetchServers]);

  // 详情弹窗逻辑
  const fetchDetail = useCallback(async (dbId: number, force: boolean) => {
    setDetailLoading(true);
    try {
      const r = await apiClient.get(`/api/servers/${dbId}/detail${force ? '?force=true' : ''}`);
      setDetailData(r.data);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载详情失败');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const openDetail = (rec: Server) => {
    setDetailTarget(rec);
    setDetailData(null);
    setLastDetailRefresh(0); // 打开新弹窗时重置冷却
    fetchDetail(rec.id, false);
  };

  const closeDetail = () => {
    setDetailTarget(null);
    setDetailData(null);
  };

  const handleDetailRefresh = () => {
    if (!detailTarget) return;
    const now = Date.now();
    if (now - lastDetailRefresh < DETAIL_REFRESH_COOLDOWN) {
      message.warning(`请 ${Math.ceil((DETAIL_REFRESH_COOLDOWN - (now - lastDetailRefresh)) / 1000)} 秒后再试`);
      return;
    }
    setLastDetailRefresh(now);
    fetchDetail(detailTarget.id, true);
  };

  const handleCopyPassword = (raw: string | undefined) => {
    if (!raw) {
      message.warning('密码不可用');
      return;
    }
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(raw).then(
        () => message.success('已复制密码'),
        () => message.error('复制失败')
      );
    } else {
      // 兼容旧浏览器
      const ta = document.createElement('textarea');
      ta.value = raw;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); message.success('已复制密码'); }
      catch { message.error('复制失败'); }
      finally { document.body.removeChild(ta); }
    }
  };

  const handleDeploy = (dbId: number) => {
    setDeployTarget(dbId);
    setDeployGroup('HighSpeed Server');
    setDeployMsg('');
    setDeployError(false);
  };

  const confirmDeploy = async () => {
    if (deployTarget === null) return;
    const dbId = deployTarget;
    setDeploying(p => new Set(p).add(dbId));
    setDeployMsg('部署中...');
    setDeployError(false);
    try {
      const r = await apiClient.post(`/api/servers/${dbId}/deploy?group_id=${encodeURIComponent(deployGroup)}`);
      if (r.data.success) {
        setDeployMsg('部署成功');
        fetchServers();
        setTimeout(() => setDeployTarget(null), 1500);
      } else {
        setDeployMsg(r.data.message || '部署失败');
        setDeployError(true);
      }
    } catch (e: any) {
      setDeployMsg(e?.response?.data?.detail || '部署失败');
      setDeployError(true);
    }
    finally { setDeploying(p => { const s = new Set(p); s.delete(dbId); return s; }); }
  };

  const handleDestroy = async (dbId: number) => {
    setDestroying(p => new Set(p).add(dbId));
    try {
      await apiClient.delete(`/api/servers/${dbId}`);
      message.success('已销毁');
    } catch (e: any) { message.error(e?.response?.data?.detail || '销毁失败'); }
    finally { setDestroying(p => { const s = new Set(p); s.delete(dbId); return s; }); }
    fetchServers();
  };

  const handleDeleteRecord = async (dbId: number) => {
    setDeleting(p => new Set(p).add(dbId));
    try {
      const r = await apiClient.delete(`/api/servers/${dbId}/record`);
      if (r.data?.success === false) {
        message.error(r.data?.message || '删除失败');
        return;
      }
      message.success('已删除');
      fetchServers();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '删除失败');
    } finally {
      setDeleting(p => { const s = new Set(p); s.delete(dbId); return s; });
    }
  };

  // 计算可筛选项(用于下拉)
  const filterOptions = useMemo(() => {
    const acc = [...new Set(servers.map(s => s.account_name).filter(Boolean))].sort();
    const country = [...new Set(servers.map(s => s.country).filter(Boolean))].sort();
    const city = [...new Set(servers.map(s => s.city).filter(Boolean))].sort();
    const image = [...new Set(servers.map(s => s.image).filter(Boolean))].sort();
    const ip_type = [...new Set(servers.map(s => s.ip_type).filter(Boolean))].sort();
    return {
      account_name: acc.map(v => ({ label: v, value: v })),
      country: country.map(v => ({ label: v, value: v })),
      city: city.map(v => ({ label: v, value: v })),
      image: image.map(v => ({ label: v, value: v })),
      ip_type: ip_type.map(v => ({ label: v, value: v })),
    };
  }, [servers]);

  // 客户端筛选 — undefined = 不筛选
  const applyFilters = useCallback((data: Server[]): Server[] => {
    return data.filter(s => {
      if (filterState.account_name && s.account_name !== filterState.account_name) return false;
      if (filterState.country && s.country !== filterState.country) return false;
      if (filterState.city && s.city !== filterState.city) return false;
      if (filterState.image && s.image !== filterState.image) return false;
      if (filterState.ip_type && s.ip_type !== filterState.ip_type) return false;
      if (filterState.ip && s.ip !== filterState.ip) return false;
      return true;
    });
  }, [filterState]);

  const filteredServers = useMemo(
    () => applyFilters(servers),
    [servers, applyFilters],
  );

  const columns: ColumnsType<Server> = [
    {
      title: '服务器ID',
      dataIndex: 'server_id',
      width: 80,
      render: (v: number, rec: Server) => (
        <a onClick={() => openDetail(rec)} style={{ cursor: 'pointer' }}>{v}</a>
      ),
    },
    { title: 'IP', dataIndex: 'ip', render: (v: string) => v || '—', width: 130 },
    { title: '账户', dataIndex: 'account_name', width: 100, render: (v: string) => v || '—' },
    { title: '批次', dataIndex: 'batch_id', width: 120, render: (v: string) => v ? <Tag color="blue">{v}</Tag> : '—' },
    { title: '国家', dataIndex: 'country', width: 70, render: (v: string) => v || '—' },
    { title: '城市', dataIndex: 'city', width: 80, render: (v: string) => v || '—' },
    { title: 'IP类型', dataIndex: 'ip_type', width: 80, render: (v: string) => v || '—' },
    { title: '操作系统', dataIndex: 'image', width: 120, ellipsis: true, render: (v: string) => v || '—' },
    { title: '磁盘', dataIndex: 'disk', render: (v: number) => `${v}G`, width: 55 },
    { title: '状态', dataIndex: 'status', width: 80, render: (s: string) => <Tag color={statusColor(s)}>{s || '—'}</Tag> },
    { title: '操作', key: 'action', width: 100, fixed: 'right',
      render: (_: unknown, rec: Server) => {
        const isDestroyed = rec.status === '已销毁';
        return (
          <Space size="small">
            <Tooltip title="详情">
              <Button size="small" icon={<EyeOutlined />} onClick={() => openDetail(rec)} />
            </Tooltip>
            {isDestroyed ? (
              <Popconfirm title="确定从数据库删除？" okText="删除" cancelText="取消" okButtonProps={{ danger: true }}
                onConfirm={() => handleDeleteRecord(rec.id)}>
                <Tooltip title="删除记录">
                  <Button size="small" danger icon={<DeleteOutlined />} loading={deleting.has(rec.id)} />
                </Tooltip>
              </Popconfirm>
            ) : (
              <>
                {rec.deploy_status !== '已部署' && rec.status === '运行中' && (
                  <Tooltip title="部署">
                    <Button size="small" type="primary" icon={<RocketOutlined />}
                      loading={deploying.has(rec.id)} onClick={() => handleDeploy(rec.id)} />
                  </Tooltip>
                )}
                <Popconfirm title="确定销毁？" okText="销毁" cancelText="取消" okButtonProps={{ danger: true }}
                  onConfirm={() => handleDestroy(rec.id)}>
                  <Tooltip title="销毁">
                    <Button size="small" danger icon={<DeleteOutlined />} loading={destroying.has(rec.id)} />
                  </Tooltip>
                </Popconfirm>
              </>
            )}
          </Space>
        );
      },
    },
  ];

  // 按 Tab 拆分数据
  const activeData = useMemo(
    () => filteredServers.filter(s => s.status !== '已销毁'),
    [filteredServers]
  );
  const destroyedData = useMemo(
    () => filteredServers.filter(s => s.status === '已销毁'),
    [filteredServers]
  );

  const renderTable = (data: Server[]) => (
    <Table
      columns={columns}
      dataSource={data}
      rowKey="id"
      size="small"
      pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
      scroll={{ x: 1100 }}
    />
  );

  // 详情弹窗内容
  const renderDetailContent = () => {
    if (detailLoading && !detailData) {
      return <div style={{ padding: 40, textAlign: 'center' }}><SyncOutlined spin /> 加载中...</div>;
    }
    if (!detailData) {
      return <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>暂无数据</div>;
    }
    const d = detailData;
    const orderedAt = d.ordered_at || detailTarget?.ordered_at || '—';
    return (
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="服务器ID">{d.server_id ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="状态">{d.status || '—'}</Descriptions.Item>
        <Descriptions.Item label="IP">{d.ip || '—'}</Descriptions.Item>
        <Descriptions.Item label="IP类型">{d.ip_type || '—'}</Descriptions.Item>
        <Descriptions.Item label="国家">{d.country || '—'}</Descriptions.Item>
        <Descriptions.Item label="城市">{d.city || '—'}</Descriptions.Item>
        <Descriptions.Item label="用户名">{d.root || 'root'}</Descriptions.Item>
        <Descriptions.Item label="密码">
          <Space>
            <span style={{ fontFamily: 'monospace', letterSpacing: 2 }}>{d.password || '**'}</span>
            <Tooltip title={d.password_raw ? '复制真实密码' : '暂无可复制的密码'}>
              <Button size="small" icon={<CopyOutlined />}
                disabled={!d.password_raw}
                onClick={() => handleCopyPassword(d.password_raw)} />
            </Tooltip>
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="CPU">{d.cpu != null ? `${d.cpu} 核` : '—'}</Descriptions.Item>
        <Descriptions.Item label="内存">{d.ram != null ? `${d.ram} MB` : '—'}</Descriptions.Item>
        <Descriptions.Item label="系统盘">{d.diskMedia || (d.disk != null ? `${d.disk}G` : '—')}</Descriptions.Item>
        <Descriptions.Item label="数据盘">{d.diskData != null ? `${d.diskData}G` : '—'}</Descriptions.Item>
        <Descriptions.Item label="流量">{d.traffic != null ? `${d.traffic}G` : '—'}</Descriptions.Item>
        <Descriptions.Item label="镜像">{d.image || '—'}</Descriptions.Item>
        <Descriptions.Item label="开通时间">{d.startTime || '—'}</Descriptions.Item>
        <Descriptions.Item label="到期时间">{d.endTime || '—'}</Descriptions.Item>
        <Descriptions.Item label="自动续费">
          {d.isAutoRenew === 1 ? <Tag color="green">已开启</Tag> : <Tag>未开启</Tag>}
        </Descriptions.Item>
        <Descriptions.Item label="下单时间">{orderedAt}</Descriptions.Item>
      </Descriptions>
    );
  };

  return (
    <Card title="服务器管理" style={{ maxWidth: 1700, margin: '20px auto' }}
      extra={<Button onClick={handleRefresh} loading={loading} icon={<ReloadOutlined />}>刷新</Button>}>
      <Space wrap style={{ marginBottom: 8 }}>
        <Select placeholder="账户" allowClear
          style={{ width: 130 }}
          value={filterState.account_name}
          onChange={v => setFilterState(prev => ({ ...prev, account_name: v }))}
          options={filterOptions.account_name} />
        <Select placeholder="国家" allowClear
          style={{ width: 110 }}
          value={filterState.country}
          onChange={v => setFilterState(prev => ({ ...prev, country: v }))}
          options={filterOptions.country} />
        <Select placeholder="城市" allowClear
          style={{ width: 110 }}
          value={filterState.city}
          onChange={v => setFilterState(prev => ({ ...prev, city: v }))}
          options={filterOptions.city} />
        <Select placeholder="操作系统" allowClear
          style={{ width: 150 }}
          value={filterState.image}
          onChange={v => setFilterState(prev => ({ ...prev, image: v }))}
          options={filterOptions.image} />
        <Select placeholder="IP类型" allowClear
          style={{ width: 130 }}
          value={filterState.ip_type}
          onChange={v => setFilterState(prev => ({ ...prev, ip_type: v }))}
          options={filterOptions.ip_type} />
        <Input placeholder="搜索IP" allowClear
          style={{ width: 160 }}
          value={filterState.ip || ''}
          onChange={e => setFilterState(prev => ({ ...prev, ip: e.target.value || undefined }))} />
      </Space>

      <Tabs
        activeKey={activeTab}
        onChange={(k) => setActiveTab(k as 'active' | 'destroyed')}
        items={[
          {
            key: 'active',
            label: `未销毁 (${activeData.length})`,
            children: renderTable(activeData),
          },
          {
            key: 'destroyed',
            label: `已销毁 (${destroyedData.length})`,
            children: renderTable(destroyedData),
          },
        ]}
      />

      {/* 详情弹窗 */}
      <Modal
        title={detailTarget ? `服务器详情 — ${detailTarget.server_id}` : '服务器详情'}
        open={detailTarget !== null}
        onCancel={closeDetail}
        footer={[
          <Button key="refresh" icon={<SyncOutlined spin={detailLoading} />} onClick={handleDetailRefresh}
            disabled={detailLoading}>
            刷新
          </Button>,
          <Button key="close" onClick={closeDetail}>关闭</Button>,
        ]}
        width={780}
        destroyOnClose
      >
        {renderDetailContent()}
      </Modal>

      {/* 部署弹窗(原有) */}
      <Modal title="选择部署分组" open={deployTarget !== null}
        onOk={confirmDeploy} onCancel={() => setDeployTarget(null)}
        okText="确认部署" cancelText="取消"
        confirmLoading={deployTarget !== null && deployMsg === '部署中...'}
        okButtonProps={{ disabled: deployMsg === '部署成功' }}
        destroyOnClose>
        <div style={{ marginBottom: 8 }}>服务器分组：</div>
        <Select value={deployGroup} onChange={setDeployGroup} style={{ width: '100%' }}
          options={[
            { label: 'HighSpeed Server', value: 'HighSpeed Server' },
            { label: 'Vip HighSpeed Server', value: 'Vip HighSpeed Server' },
          ]} />
        {deployMsg && (
          <div style={{ marginTop: 12, padding: '8px 12px', borderRadius: 4,
            background: deployError ? '#fff2f0' : deployMsg === '部署成功' ? '#f6ffed' : '#e6f7ff',
            color: deployError ? '#ff4d4f' : deployMsg === '部署成功' ? '#52c41a' : '#1677ff',
          }}>{deployMsg}</div>
        )}
      </Modal>
    </Card>
  );
}
