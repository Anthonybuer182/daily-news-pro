import { Segmented, Grid } from 'antd';
import { useFilter } from '../context/FilterContext';

const { useBreakpoint } = Grid;

export default function TimeFilter() {
  const { filter, setFilter } = useFilter();
  const screens = useBreakpoint();
  const isMobile = !screens.sm;

  const options = [
    { value: '', label: '全部' },
    { value: 'today', label: '当天' },
    { value: 'week', label: '本周' },
    { value: 'month', label: '当月' },
  ];

  return (
    <Segmented
      value={filter.timeRange}
      onChange={value => setFilter({ ...filter, timeRange: value as '' | 'today' | 'week' | 'month' })}
      options={options}
      size={isMobile ? 'small' : 'middle'}
    />
  );
}