import { useState, useEffect } from 'react';
import { Layout, Typography, Space, Grid } from 'antd';
import Header from './components/Header';
import SourceTabs from './components/SourceTabs';
import TimeFilter from './components/TimeFilter';
import TagFilter from './components/TagFilter';
import NewsList from './components/NewsList';
import { useFilter } from './context/FilterContext';
import { getRules, getTags } from '../../api';

const { useBreakpoint } = Grid;

const { Content } = Layout;
const { Text } = Typography;

function PreviewContent() {
  const { filter, setFilter } = useFilter();
  const [sources, setSources] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState('');
  const screens = useBreakpoint();
  const isMobile = !screens.sm;

  useEffect(() => {
    getRules().then(res => {
      const names: string[] = res.data.map((r: any) => r.name).filter(Boolean);
      setSources([...new Set(names)]);
    });

    getTags().then(res => {
      const tagNames = (res.data || []).map((t: any) => t.name);
      setAvailableTags(tagNames);
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

  const contentPadding = isMobile ? '12px 12px' : '24px 32px';
  const filterPadding = isMobile ? '12px 16px' : '20px 24px';

  return (
    <Layout style={{ minHeight: '100vh', background: '#fafafa' }}>
      <Header
        keyword={keyword}
        onKeywordChange={handleKeywordChange}
        onSearch={handleSearch}
      />
      <Content style={{ padding: contentPadding, maxWidth: 1600, margin: '0 auto', width: '100%' }}>
        {/* 筛选栏 */}
        <div style={{
          background: '#fff',
          borderRadius: isMobile ? 8 : 12,
          padding: filterPadding,
          marginBottom: isMobile ? 12 : 20,
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        }}>
          {/* 来源筛选 */}
          <div style={{ marginBottom: 12 }}>
            <SourceTabs sources={sources} />
          </div>
          <TagFilter availableTags={availableTags} />
          <div style={{ height: 12 }} />
          <TimeFilter />
        </div>

        {/* 结果统计 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: isMobile ? 10 : 16,
        }}>
          <Space>
            <Text style={{ fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>共</Text>
            <Text strong style={{ fontSize: isMobile ? 14 : 16, color: '#DC2626' }}>{total}</Text>
            <Text style={{ fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>篇新闻</Text>
          </Space>
        </div>

        <NewsList onTotalChange={setTotal} />
      </Content>
    </Layout>
  );
}

export default PreviewContent;