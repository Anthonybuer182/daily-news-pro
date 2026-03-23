import { createContext, useContext, useState, ReactNode } from 'react';

export interface PreviewFilter {
  source: string;      // 来源（空=全部）
  timeRange: '' | 'today' | 'week' | 'month';
  tags: string[];      // 选中标签（空=全部）
  keyword: string;     // 搜索关键词
}

interface FilterContextType {
  filter: PreviewFilter;
  setFilter: (filter: PreviewFilter) => void;
  resetFilter: () => void;
}

const defaultFilter: PreviewFilter = {
  source: '',
  timeRange: '',
  tags: [],
  keyword: '',
};

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filter, setFilter] = useState<PreviewFilter>(defaultFilter);

  const resetFilter = () => setFilter(defaultFilter);

  return (
    <FilterContext.Provider value={{ filter, setFilter, resetFilter }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilter() {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error('useFilter must be used within FilterProvider');
  }
  return context;
}