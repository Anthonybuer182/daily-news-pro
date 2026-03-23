import { Tabs } from 'antd';
import { useFilter } from '../context/FilterContext';

interface SourceTabsProps {
  sources: string[];
}

export default function SourceTabs({ sources }: SourceTabsProps) {
  const { filter, setFilter } = useFilter();

  const tabs = [
    { key: '', label: '全部' },
    ...sources.map(source => ({ key: source, label: source }))
  ];

  const handleChange = (key: string) => {
    setFilter({ ...filter, source: key });
  };

  return (
    <Tabs
      activeKey={filter.source}
      onChange={handleChange}
      items={tabs}
      style={{ marginBottom: 0 }}
    />
  );
}