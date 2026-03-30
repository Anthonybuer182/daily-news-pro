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
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: 8,
      alignItems: 'center'
    }}>
      {availableTags.map(tag => {
        const isSelected = filter.tags.includes(tag);
        return (
          <button
            key={tag}
            onClick={() => toggleTag(tag)}
            style={{
              padding: '4px 12px',
              border: isSelected ? '1px solid #DC2626' : '1px solid #e8e8e8',
              borderRadius: 16,
              fontSize: 13,
              cursor: 'pointer',
              transition: 'all 0.2s',
              background: isSelected
                ? 'linear-gradient(135deg, rgba(220,38,38,0.1) 0%, rgba(185,28,28,0.1) 100%)'
                : '#fff',
              color: isSelected ? '#DC2626' : '#666',
              fontWeight: isSelected ? 500 : 400,
            }}
          >
            {tag}
          </button>
        );
      })}
    </div>
  );
}