import { useState, useEffect } from 'react';
import { Layout, Typography, Space } from 'antd';
import Header from './components/Header';
import SourceTabs from './components/SourceTabs';
import TimeFilter from './components/TimeFilter';
import TagFilter from './components/TagFilter';
import NewsList from './components/NewsList';
import { useFilter } from './context/FilterContext';
import { getRules, getTags } from '../../api';

const { Content } = Layout;
const { Text } = Typography;

function PreviewContent() {
  const { filter, setFilter } = useFilter();
  const [sources, setSources] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState('');

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

  return (
    <Layout style={{ minHeight: '100vh', background: '#fafafa' }}>
      <Header
        keyword={keyword}
        onKeywordChange={handleKeywordChange}
        onSearch={handleSearch}
      />
      <Content style={{ padding: '24px 32px' }}>
        {/* 筛选栏 */}
        <div style={{
          background: '#fff',
          borderRadius: 16,
          padding: '20px 24px',
          marginBottom: 20,
          boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
          border: '1px solid rgba(0,0,0,0.04)',
        }}>
          {/* 来源筛选 */}
          <div style={{ marginBottom: 16 }}>
            <SourceTabs sources={sources} />
          </div>

          {/* 时间和标签筛选 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            flexWrap: 'wrap'
          }}>
            <TimeFilter />
            <div style={{
              height: 24,
              width: 1,
              background: '#e8e8e8'
            }} />
            <TagFilter availableTags={availableTags} />
          </div>
        </div>

        {/* 结果统计 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16
        }}>
          <Space>
            <Text style={{ fontSize: 14, color: '#666' }}>共</Text>
            <Text strong style={{ fontSize: 16, color: '#667eea' }}>{total}</Text>
            <Text style={{ fontSize: 14, color: '#666' }}>篇新闻</Text>
          </Space>
        </div>

        <NewsList onTotalChange={setTotal} />
      </Content>
    </Layout>
  );
}

export default PreviewContent;