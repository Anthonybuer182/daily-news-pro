import { Tag } from 'antd';
import { useFilter } from '../context/FilterContext';

interface TagFilterProps {
  availableTags: string[];
}

export default function TagFilter({ availableTags }: TagFilterProps) {
  const { filter, setFilter } = useFilter();

  const toggleTag = (tag: string) => {
    const newTags = filter.tags.includes(tag)
      ? filter.tags.filter(t => t !== tag)
      : [...filter.tags, tag];
    setFilter({ ...filter, tags: newTags });
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {availableTags.map(tag => (
        <Tag
          key={tag}
          color={filter.tags.includes(tag) ? 'blue' : 'default'}
          onClick={() => toggleTag(tag)}
          style={{ cursor: 'pointer' }}
        >
          {tag}
        </Tag>
      ))}
    </div>
  );
}