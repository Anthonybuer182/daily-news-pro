import { Segmented } from 'antd';
import { useFilter } from '../context/FilterContext';

interface SourceTabsProps {
  sources: string[];
}

export default function SourceTabs({ sources }: SourceTabsProps) {
  const { filter, setFilter } = useFilter();

  const options = [
    { value: '', label: '全部' },
    ...sources.map(source => ({ value: source, label: source }))
  ];

  const handleChange = (value: string) => {
    setFilter({ ...filter, source: value });
  };

  return (
    <div style={{
      overflowX: 'auto',
      marginBottom: 8,
    }}>
      <div style={{ minWidth: 'max-content' }}>
        <Segmented
          value={filter.source}
          onChange={handleChange}
          options={options}
        />
      </div>
    </div>
  );
}