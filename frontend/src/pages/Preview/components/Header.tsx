import { Layout, Input, Button, Tooltip } from 'antd';
import { BgColorsOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import useTheme from '../context/ThemeContext';

const { Header: AntHeader } = Layout;

interface HeaderProps {
  keyword: string;
  onKeywordChange: (keyword: string) => void;
  onSearch: () => void;
}

export default function Header({ keyword, onKeywordChange, onSearch }: HeaderProps) {
  const { darkMode, toggleDarkMode } = useTheme();

  return (
    <AntHeader style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: '#001529',
      padding: '0 24px'
    }}>
      <Link to="/preview" style={{ color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
        Daily News
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Input
          placeholder="搜索新闻..."
          value={keyword}
          onChange={e => onKeywordChange(e.target.value)}
          onPressEnter={onSearch}
          style={{ width: 200 }}
          allowClear
        />
        <Tooltip title="深色模式">
          <Button
            type="text"
            icon={<BgColorsOutlined />}
            onClick={toggleDarkMode}
            style={{ color: '#fff' }}
          />
        </Tooltip>
      </div>
    </AntHeader>
  );
}