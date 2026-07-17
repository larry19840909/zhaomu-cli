import { useState, useEffect, useCallback, useMemo } from 'react';
import type { ColumnsType } from 'antd/es/table';
import { Card, Select, InputNumber, Table, Button, Modal, message, Space, Checkbox } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

interface Region { id: number; city: string; zone: string; country: string; }
interface Product {
  id: number; cpu: number; ram: number; disk: number; diskMax: number;
  traffic: number; bandwidth: number; diskMedia: string; price: number; priceQuarter: number;
  priceHalfYear: number; priceYear: number; tags: string; zone: number;
}
interface ImageItem { id: number; name: string; type: string; }
interface Account { id: number; name: string; apikey_masked: string; }

export default function ProductSelect() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string | undefined>(undefined);
  const [selectedCity, setSelectedCity] = useState<string | undefined>(undefined);
  const [cpu, setCpu] = useState<number | null>(null);
  const [traffic, setTraffic] = useState<string | undefined>(undefined);
  const [tagFilters, setTagFilters] = useState<string[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [orderOpen, setOrderOpen] = useState(false);
  const [orderItems, setOrderItems] = useState<Map<number, { imageId: number; imageName: string; disk: number; cycle: number; quantity: number }>>(new Map());
  const [images, setImages] = useState<Map<number, ImageItem[]>>(new Map());
  const [prepLoading, setPrepLoading] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [refundZoneIds, setRefundZoneIds] = useState<Set<number>>(new Set());
  const [balance, setBalance] = useState<number | null>(null);

  // 加载账户
  useEffect(() => {
    apiClient.get('/api/accounts').then(r => {
      const list = r.data || [];
      setAccounts(list);
      if (list.length === 1) setAccountId(list[0].id);
    }).catch(() => {});
  }, []);

  // 查询余额
  const fetchBalance = useCallback(async (aid: number) => {
    try {
      const r = await apiClient.get(`/api/balance?account_id=${aid}`);
      setBalance(r.data.balance);
    } catch { setBalance(null); }
  }, []);

  // 账户变化时自动查询余额（含初始自动选中 + 手动切换）
  useEffect(() => {
    if (accountId !== null) fetchBalance(accountId);
    else setBalance(null);
  }, [accountId, fetchBalance]);

  // 加载地域列表
  useEffect(() => {
    if (accountId === null) { setRegions([]); return; }
    apiClient.get(`/api/filter/regions?account_id=${accountId}`).then(r => setRegions(r.data)).catch(() => {});
  }, [accountId]);

  // 国家列表
  const countries = useMemo(() => {
    return [...new Set(regions.map(r => r.country))].sort();
  }, [regions]);

  // 当前国家下的城市列表
  const cityOptions = useMemo(() => {
    const filtered = selectedCountry ? regions.filter(r => r.country === selectedCountry) : regions;
    return [...new Set(filtered.map(r => r.city))].map(city => ({ label: city, value: city }));
  }, [regions, selectedCountry]);

  // 可用区 ID→zone 字母映射
  const zoneMap = useMemo(() => {
    const m = new Map<number, string>();
    regions.forEach(r => m.set(r.id, r.zone));
    return m;
  }, [regions]);

  // 选中城市对应的所有可用区 ID
  const zoneIds = useMemo(() => {
    if (!selectedCity) return [] as number[];
    const base = selectedCountry ? regions.filter(r => r.country === selectedCountry) : regions;
    return base.filter(r => r.city === selectedCity).map(r => r.id);
  }, [selectedCity, selectedCountry, regions]);

  // 查询产品
  const fetchProducts = useCallback(async () => {
    if (accountId === null || zoneIds.length === 0) return;
    setLoading(true);
    try {
      const params: Record<string, string | number> = { account_id: accountId, region_ids: zoneIds.join(',') };
      if (cpu) params.cpu = cpu;
      if (traffic) params.traffic = traffic;
      const r = await apiClient.get('/api/products', { params });
      setProducts(r.data || []);
      setSelectedKeys([]);
    } catch { }
    finally { setLoading(false); }
  }, [accountId, zoneIds, cpu, traffic]);

  // 选城市后自动查询 + 查询退款信息
  useEffect(() => {
    if (zoneIds.length === 0) { setProducts([]); setRefundZoneIds(new Set()); return; }
    fetchProducts();
    // 并行查询各可用区的退款支持
    let cancelled = false;
    const fetchRefund = async () => {
      const refundSet = new Set<number>();
      await Promise.all(zoneIds.map(async (zid) => {
        try {
          const r = await apiClient.get(`/api/filter/regions/${zid}/compare?account_id=${accountId}`);
          if (r.data.has_refund) refundSet.add(zid);
        } catch { /* 静默降级 */ }
      }));
      if (!cancelled) setRefundZoneIds(refundSet);
    };
    fetchRefund();
    return () => { cancelled = true; };
  }, [zoneIds.join(','), accountId]);

  // 客户端筛选
  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      if (tagFilters.length === 0) return true;
      return tagFilters.every(f => {
        if (f === 'refund') return refundZoneIds.has(p.zone);
        if (f === '原生IP') return p.tags?.includes('原生IP');
        if (f === '住宅IP') return p.tags?.includes('住宅IP');
        return true;
      });
    });
  }, [products, tagFilters, refundZoneIds]);

  // 查询按钮（CPU/流量变化后点）
  const handleSearch = () => {
    if (accountId === null) { message.warning('请先选择账户'); return; }
    if (!selectedCity) { message.warning('请先选择城市'); return; }
    fetchProducts();
  };

  const handlePrepare = async () => {
    if (accountId === null) { message.warning('请先选择账户'); return; }
    if (selectedKeys.length === 0) { message.warning('请先勾选产品'); return; }
    setPrepLoading(true);
    const imgMap = new Map<number, ImageItem[]>();
    const items = new Map<number, { imageId: number; imageName: string; disk: number; cycle: number; quantity: number }>();
    try {
      // 并行获取所有选中产品的镜像信息
      const results = await Promise.all(
        selectedKeys.map(key => {
          const pid = Number(key);
          return apiClient.get(`/api/orders/prepare/${pid}?account_id=${accountId}`)
            .then(r => ({ pid, data: r.data }));
        }),
      );
      for (const { pid, data } of results) {
        const imgs: ImageItem[] = data.images || [];
        imgMap.set(pid, imgs);
        const defaultImage = imgs.find(i => i.name.includes('Ubuntu 20.04'))
          || imgs.find(i => i.name.includes('Ubuntu 22.04'))
          || imgs[0];
        items.set(pid, {
          imageId: defaultImage?.id || 0,
          imageName: defaultImage?.name || '',
          disk: data.defaultDisk || 20,
          cycle: data.minPaymentCycle || 1,
          quantity: 1,
        });
      }
      setImages(imgMap);
      setOrderItems(items);
      setOrderOpen(true);
    } catch { }
    finally { setPrepLoading(false); }
  };

  const handleOrder = async () => {
    if (accountId === null) { message.warning('请先选择账户'); return; }
    const orders = Array.from(orderItems.entries()).map(([pid, item]) => {
      const prod = products.find(p => p.id === pid);
      const ip_type = prod?.tags?.includes('原生IP') ? '原生IP'
        : prod?.tags?.includes('住宅IP') ? '住宅IP' : '';
      return {
        product_id: pid, image_id: item.imageId, image_name: item.imageName,
        disk: item.disk, payment_cycle: item.cycle, quantity: item.quantity,
        ip_type,
      };
    });
    setOrderLoading(true);
    try {
      const r = await apiClient.post(`/api/orders?account_id=${accountId}`, orders);
      message.success(`成功下单 ${r.data.success_count} 台服务器`);
      setOrderOpen(false); setSelectedKeys([]);
      fetchBalance(accountId);
    } catch { }
    finally { setOrderLoading(false); }
  };

  // 计算本次下单总价（月付单价 × 数量）
  const totalPrice = useMemo(() => {
    return Array.from(orderItems.entries()).reduce((sum, [pid, item]) => {
      const prod = products.find(p => p.id === pid);
      return sum + (prod?.price || 0) * (item.quantity || 1);
    }, 0);
  }, [orderItems, products]);

  const columns: ColumnsType<Product> = [
    { title: 'CPU', dataIndex: 'cpu', render: (v: number) => `${v}核`, width: 60 },
    { title: '内存', dataIndex: 'ram', render: (v: number) => v >= 1024 ? `${v / 1024}G` : `${v}M`, width: 70 },
    { title: '磁盘', dataIndex: 'disk', render: (v: number) => `${v}G`, width: 65 },
    { title: '带宽', dataIndex: 'bandwidth', render: (v: number) => (v == null || v === 0) ? '不限' : `${v}M`, width: 70 },
    { title: '流量', dataIndex: 'traffic', render: (v: number) => v === 0 ? '不限' : `${v}G`, width: 70 },
    { title: '月付', dataIndex: 'price', render: (v: number) => `¥${v}`, width: 70 },
    { title: '季付', dataIndex: 'priceQuarter', render: (v: number) => `¥${v}`, width: 70 },
    { title: '标签', dataIndex: 'tags', ellipsis: true },
    { title: '可用区', dataIndex: 'zone', width: 60, render: (v: number) => zoneMap.get(v) || String(v) },
  ];

  return (
    <Card title="选品下单" style={{ maxWidth: 1200, margin: '20px auto' }}>
      <Space wrap style={{ marginBottom: 8 }}>
        <Select placeholder="选择账户" value={accountId}
          onChange={(v) => { setAccountId(v); setProducts([]); setSelectedKeys([]); setRefundZoneIds(new Set()); }}
          style={{ minWidth: 180 }} options={accounts.map(a => ({ label: a.name, value: a.id }))} />

        <Select placeholder="选择国家" value={selectedCountry}
          onChange={(v) => { setSelectedCountry(v); setSelectedCity(undefined); }}
          allowClear showSearch filterOption={(input, option) => (option?.label as string || '').includes(input)}
          style={{ width: 160 }} options={countries.map(c => ({ label: c, value: c }))} />

        <Select placeholder="选择城市" value={selectedCity}
          onChange={(v) => { setSelectedCity(v); setTagFilters([]); }}
          showSearch filterOption={(input, option) => (option?.label as string || '').includes(input)}
          style={{ width: 180 }} options={cityOptions} />

        <InputNumber placeholder="CPU 核数" value={cpu} onChange={setCpu} min={1} max={64} style={{ width: 120 }} />
        <Select placeholder="流量" value={traffic} onChange={setTraffic} allowClear
          options={[{ label: '不限流量', value: 'unlimited' }, { label: '≥1000G', value: '1000' }, { label: '≥2000G', value: '2000' }]} />

        <Button type="primary" onClick={handleSearch} loading={loading}>查询</Button>
      </Space>

      <div style={{ marginBottom: 12 }}>
        <Checkbox.Group value={tagFilters} onChange={(v) => setTagFilters(v as string[])}
          options={[
            { label: '销毁退款', value: 'refund' },
            { label: '原生IP', value: '原生IP' },
            { label: '住宅IP', value: '住宅IP' },
          ]} />
      </div>

      {selectedCity && (
        <div style={{ marginBottom: 12, padding: '8px 12px', background: '#f0f5ff', borderRadius: 4, fontSize: 13 }}>
          <InfoCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          当前城市 {zoneIds.length} 个可用区，退款与 IP 类型来自 zhaomu 官方数据
        </div>
      )}

      <Table rowSelection={{ selectedRowKeys: selectedKeys, onChange: setSelectedKeys }}
        columns={columns} dataSource={filteredProducts} rowKey="id" size="small" pagination={{ pageSize: 20 }}
        scroll={{ x: 800 }}
        footer={() => (
          <Button type="primary" size="large" block onClick={handlePrepare} loading={prepLoading} disabled={selectedKeys.length === 0}>
            配置下单 ({selectedKeys.length} 项)
          </Button>
        )} />

      <Modal title="确认下单" open={orderOpen} onCancel={() => setOrderOpen(false)}
        onOk={handleOrder} confirmLoading={orderLoading} okText="确认下单" cancelText="取消" width={700}
        okButtonProps={{ disabled: balance !== null && balance < totalPrice }}>
        {Array.from(orderItems.entries()).map(([pid, item]) => {
          const prod = products.find(p => p.id === pid);
          if (!prod) return null;
          const imgs = images.get(pid) || [];
          return (
            <Card key={pid} size="small" style={{ marginBottom: 8 }}
              title={`${prod.cpu}核/${prod.ram >= 1024 ? prod.ram / 1024 + 'G' : prod.ram + 'M'}/${prod.disk}G — ${zoneMap.get(prod.zone) || prod.zone}`}>
              <Space wrap>
                <span>镜像：<Select value={item.imageId} style={{ width: 160 }}
                  onChange={(v) => {
                    const imgItem = imgs.find(i => i.id === v);
                    setOrderItems(prev => new Map(prev).set(pid, { ...item, imageId: v, imageName: imgItem?.name || '' }));
                  }}
                  options={imgs.map(i => ({ label: i.name, value: i.id }))} /></span>
                <span>磁盘：{prod.disk}G（默认）</span>
                <span>周期：月付</span>
                <span>数量：<InputNumber min={1} max={5} value={item.quantity}
                  onChange={(v) => setOrderItems(prev => new Map(prev).set(pid, { ...item, quantity: v ?? 1 }))} style={{ width: 60 }} /> 台</span>
              </Space>
            </Card>
          );
        })}
        <div style={{ marginTop: 16, padding: '12px 16px', background: '#fafafa', borderRadius: 6 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>余额：<strong style={{ color: '#1677ff' }}>¥{balance?.toFixed(2) ?? '--'}</strong></span>
            <span>总价：<strong>¥{totalPrice.toFixed(2)}</strong></span>
          </div>
          {balance !== null && balance < totalPrice && (
            <div style={{ marginTop: 8, color: '#ff4d4f', fontWeight: 500 }}>
              余额不足，还差 ¥{(totalPrice - balance).toFixed(2)}
            </div>
          )}
        </div>
      </Modal>
    </Card>
  );
}
