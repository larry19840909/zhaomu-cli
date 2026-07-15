import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Login from './pages/Login';
import Settings from './pages/Settings';
import ProductSelect from './pages/ProductSelect';
import ServerManage from './pages/ServerManage';
import AppLayout from './components/Layout';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<AppLayout />}>
              <Route path="/settings" element={<Settings />} />
              <Route path="/products" element={<ProductSelect />} />
              <Route path="/manage" element={<ServerManage />} />
            </Route>
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}

export default App;
