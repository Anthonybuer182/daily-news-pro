import { Layout, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Header: AntHeader } = Layout;

interface HeaderProps {
  keyword: string;
  onKeywordChange: (keyword: string) => void;
  onSearch: () => void;
}

export default function Header({ keyword, onKeywordChange, onSearch }: HeaderProps) {
  return (
    <AntHeader
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)',
        padding: '0 32px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <Link
        to="/preview"
        style={{
          color: '#fff',
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: '-0.01em',
        }}
      >
        Daily News
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Input
          placeholder="搜索新闻..."
          value={keyword}
          onChange={e => onKeywordChange(e.target.value)}
          onPressEnter={onSearch}
          style={{ width: 280, borderRadius: 20 }}
          allowClear
          prefix={<SearchOutlined style={{ color: '#999' }} />}
        />
      </div>
    </AntHeader>
  );
}