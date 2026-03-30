import { Tabs } from 'antd';
import { useFilter } from '../context/FilterContext';

interface SourceTabsProps {
  sources: string[];
}

export default function SourceTabs({ sources }: SourceTabsProps) {
  const { filter, setFilter } = useFilter();

  const items = [
    { key: '', label: '全部' },
    ...sources.map(source => ({ key: source, label: source }))
  ];

  const handleChange = (key: string) => {
    setFilter({ ...filter, source: key });
  };

  return (
    <div style={{ marginBottom: -16 }}>
      <style>{`
        .source-tabs .ant-tabs-nav::before {
          display: none;
        }
        .source-tabs .ant-tabs-ink-bar {
          display: none;
        }
      `}</style>
      <Tabs
        className="source-tabs"
        activeKey={filter.source}
        onChange={handleChange}
        items={items}
        size="small"
      />
    </div>
  );
}