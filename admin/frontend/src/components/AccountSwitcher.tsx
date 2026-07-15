import { Select } from 'antd';

interface Account {
  id: number;
  name: string;
}

interface Props {
  accounts: Account[];
  value?: number;
  onChange?: (id: number) => void;
}

export default function AccountSwitcher({ accounts, value, onChange }: Props) {
  return (
    <Select
      placeholder="选择账号"
      value={value}
      onChange={onChange}
      options={accounts.map((a) => ({ label: a.name, value: a.id }))}
      style={{ minWidth: 160 }}
    />
  );
}
