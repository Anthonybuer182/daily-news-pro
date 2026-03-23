import { Card, Tag, Typography } from 'antd';
import { Link } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Text } = Typography;

interface NewsCardProps {
  article: {
    id: number;
    title: string;
    summary: string;
    cover_image: string;
    rule_name: string;
    created_at: string;
    tags: string[];
  };
}

export default function NewsCard({ article }: NewsCardProps) {
  const isDarkMode = document.body.classList.contains('dark-mode');

  return (
    <Link to={`/preview/article/${article.id}`}>
      <Card
        hoverable
        cover={article.cover_image && <img alt={article.title} src={article.cover_image} style={{ height: 160, objectFit: 'cover' }} />}
        style={{
          height: '100%',
          background: isDarkMode ? '#1f1f1f' : '#fff',
          borderColor: isDarkMode ? '#303030' : '#e8e8e8'
        }}
        styles={{
          body: { color: isDarkMode ? '#e8e8e8' : 'rgba(0,0,0,0.88)' }
        }}
      >
        <Card.Meta
          title={article.title}
          description={
            <>
              <Text type="secondary" style={{ fontSize: 12, color: isDarkMode ? '#888' : '#999' }}>
                {article.rule_name} · {dayjs(article.created_at).fromNow()}
              </Text>
              {article.summary && (
                <p style={{ marginTop: 8, color: isDarkMode ? '#bbb' : '#666', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {article.summary}
                </p>
              )}
              {article.tags && article.tags.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  {article.tags.slice(0, 3).map(tag => (
                    <Tag key={tag} style={{ marginBottom: 4 }}>{tag}</Tag>
                  ))}
                </div>
              )}
            </>
          }
        />
      </Card>
    </Link>
  );
}