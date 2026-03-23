import { Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

interface SearchBarProps {
  keyword: string;
  onChange: (keyword: string) => void;
  onSearch: () => void;
}

export default function SearchBar({ keyword, onChange, onSearch }: SearchBarProps) {
  return (
    <Input
      placeholder="搜索文章标题或摘要..."
      prefix={<SearchOutlined />}
      value={keyword}
      onChange={e => onChange(e.target.value)}
      onPressEnter={onSearch}
      allowClear
      size="large"
    />
  );
}