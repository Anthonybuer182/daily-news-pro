import { Radio } from 'antd';
import { useFilter } from '../context/FilterContext';

export default function TimeFilter() {
  const { filter, setFilter } = useFilter();

  const options = [
    { value: '', label: '全部' },
    { value: 'today', label: '当天' },
    { value: 'week', label: '本周' },
    { value: 'month', label: '当月' },
  ];

  return (
    <Radio.Group
      value={filter.timeRange}
      onChange={e => setFilter({ ...filter, timeRange: e.target.value })}
      options={options}
      optionType="button"
      buttonStyle="solid"
    />
  );
}