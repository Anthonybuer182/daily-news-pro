import { useEffect, useRef } from 'react';
import { Row, Col, Spin } from 'antd';
import NewsCard from './NewsCard';
import { useArticles } from '../hooks/useArticles';

interface NewsListProps {
  onTotalChange: (total: number) => void;
}

export default function NewsList({ onTotalChange }: NewsListProps) {
  const { articles, loading, loadingMore, hasMore, loadMore, total } = useArticles();
  const observerRef = useRef<HTMLDivElement>(null);
  const isDarkMode = document.body.classList.contains('dark-mode');

  useEffect(() => {
    onTotalChange(total);
  }, [total, onTotalChange]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (observerRef.current) {
      observer.observe(observerRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loadingMore, loadMore]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>;
  }

  if (articles.length === 0) {
    return <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>暂无新闻</div>;
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        {articles.map(article => (
          <Col key={article.id} xs={24} sm={12} md={8} lg={6}>
            <NewsCard article={article} />
          </Col>
        ))}
      </Row>
      <div ref={observerRef} style={{ textAlign: 'center', padding: 20 }}>
        {loadingMore && <Spin />}
        {!hasMore && articles.length > 0 && (
          <span style={{ color: isDarkMode ? '#666' : '#999' }}>没有更多了</span>
        )}
      </div>
    </div>
  );
}