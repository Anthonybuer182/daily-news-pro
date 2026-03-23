import { Typography } from 'antd';
import ReactMarkdown from 'react-markdown';

const { Title } = Typography;

interface ArticleContentProps {
  title: string;
  author: string;
  publish_time: string;
  content: string;
  cover_image: string;
  tags: string[];
}

export default function ArticleContent({
  title,
  author,
  publish_time,
  content,
  cover_image,
  tags
}: ArticleContentProps) {
  return (
    <article style={{ maxWidth: 800, margin: '0 auto', padding: '0 16px' }}>
      <Title level={2} style={{ marginBottom: 8 }}>{title}</Title>

      <div style={{ color: '#666', marginBottom: 16 }}>
        {author && <span>作者: {author}</span>}
        {author && publish_time && <span> · </span>}
        {publish_time && <span>{publish_time}</span>}
      </div>

      {tags && tags.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {tags.map(tag => (
            <span key={tag} style={{
              display: 'inline-block',
              padding: '2px 8px',
              marginRight: 8,
              background: '#f0f0f0',
              borderRadius: 4,
              fontSize: 12
            }}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {cover_image && (
        <img
          src={cover_image}
          alt={title}
          style={{ maxWidth: '100%', marginBottom: 24, borderRadius: 8 }}
        />
      )}

      <div className="article-body" style={{ lineHeight: 1.8 }}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>

      <style>{`
        .article-body h1 { font-size: 1.5em; margin-top: 1.5em; margin-bottom: 0.5em; }
        .article-body h2 { font-size: 1.3em; margin-top: 1.5em; margin-bottom: 0.5em; }
        .article-body h3 { font-size: 1.1em; margin-top: 1.5em; margin-bottom: 0.5em; }
        .article-body p { margin-bottom: 1em; }
        .article-body img { max-width: 100%; height: auto; }
        .article-body pre { background: #f5f5f5; padding: 16px; border-radius: 4px; overflow-x: auto; }
        .article-body code { background: #f5f5f5; padding: 2px 6px; border-radius: 2px; }
        .article-body blockquote { border-left: 4px solid #ddd; padding-left: 16px; margin-left: 0; color: #666; }
        .dark-mode .article-body pre { background: #2d2d2d; }
        .dark-mode .article-body code { background: #2d2d2d; }
        .dark-mode .article-body blockquote { border-color: #555; }
      `}</style>
    </article>
  );
}