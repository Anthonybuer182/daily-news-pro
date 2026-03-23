import { useState, useEffect } from 'react';
import { Layout, Card } from 'antd';
import Header from './components/Header';
import SourceTabs from './components/SourceTabs';
import TimeFilter from './components/TimeFilter';
import TagFilter from './components/TagFilter';
import NewsList from './components/NewsList';
import { FilterProvider, useFilter } from './context/FilterContext';
import { getRules, getTags } from '../../api';

const { Content } = Layout;

function PreviewContent() {
  const { filter, setFilter } = useFilter();
  const [sources, setSources] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState('');

  useEffect(() => {
    // 加载来源列表
    getRules().then(res => {
      const names = res.data.map((r: any) => r.name).filter(Boolean);
      setSources([...new Set(names)]);
    });

    // 加载标签列表
    getTags().then(res => {
      setAvailableTags(res.data || []);
    });
  }, []);

  const handleSearch = () => {
    setFilter({ ...filter, keyword });
  };

  const handleKeywordChange = (value: string) => {
    setKeyword(value);
    if (!value) {
      setFilter({ ...filter, keyword: '' });
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        keyword={keyword}
        onKeywordChange={handleKeywordChange}
        onSearch={handleSearch}
      />
      <Content style={{ padding: 24 }}>
        <Card style={{ marginBottom: 16 }}>
          <SourceTabs sources={sources} />
        </Card>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 500 }}>时间:</span>
            <TimeFilter />
            <span style={{ fontWeight: 500, marginLeft: 16 }}>标签:</span>
            <TagFilter availableTags={availableTags} />
          </div>
        </Card>
        <div style={{ marginBottom: 16, color: '#666' }}>
          共 {total} 篇新闻
        </div>
        <NewsList onTotalChange={setTotal} />
      </Content>
    </Layout>
  );
}

export default function Preview() {
  return (
    <FilterProvider>
      <PreviewContent />
    </FilterProvider>
  );
}