import { useState } from 'react';
import { Layout, Input, Grid } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Header: AntHeader } = Layout;
const { useBreakpoint } = Grid;

interface HeaderProps {
  keyword: string;
  onKeywordChange: (keyword: string) => void;
  onSearch: () => void;
}

export default function Header({ keyword, onKeywordChange, onSearch }: HeaderProps) {
  const screens = useBreakpoint();
  const isMobile = !screens.sm;
  const [searchExpanded, setSearchExpanded] = useState(false);

  const handleSearchIconClick = () => {
    setSearchExpanded(true);
  };

  const handleSearchBlur = () => {
    if (!keyword) {
      setSearchExpanded(false);
    }
  };

  return (
    <AntHeader
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)',
        padding: isMobile ? '0 16px' : '0 32px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        height: isMobile ? 52 : 64,
      }}
    >
      {/* 移动端搜索展开时隐藏 logo */}
      {!(isMobile && searchExpanded) && (
        <Link
          to="/preview"
          style={{
            color: '#fff',
            fontSize: isMobile ? 18 : 22,
            fontWeight: 700,
            letterSpacing: '-0.01em',
            whiteSpace: 'nowrap',
          }}
        >
          Daily News
        </Link>
      )}

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        flex: isMobile && searchExpanded ? 1 : undefined,
      }}>
        {isMobile ? (
          searchExpanded ? (
            <Input
              autoFocus
              placeholder="搜索新闻..."
              value={keyword}
              onChange={e => onKeywordChange(e.target.value)}
              onPressEnter={() => { onSearch(); setSearchExpanded(false); }}
              onBlur={handleSearchBlur}
              style={{ borderRadius: 20, flex: 1 }}
              allowClear
              prefix={<SearchOutlined style={{ color: '#999' }} />}
            />
          ) : (
            <SearchOutlined
              onClick={handleSearchIconClick}
              style={{ color: '#fff', fontSize: 18, cursor: 'pointer', padding: '4px' }}
            />
          )
        ) : (
          <Input
            placeholder="搜索新闻..."
            value={keyword}
            onChange={e => onKeywordChange(e.target.value)}
            onPressEnter={onSearch}
            style={{ width: 280, borderRadius: 20 }}
            allowClear
            prefix={<SearchOutlined style={{ color: '#999' }} />}
          />
        )}
      </div>
    </AntHeader>
  );
}