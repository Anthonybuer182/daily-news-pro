import { Typography } from 'antd'
import ReactMarkdown from 'react-markdown'

const { Title, Text } = Typography

interface ArticleContentProps {
  title: string
  author: string
  publish_time: string
  content: string
  cover_image: string
  tags: string[]
}

export default function ArticleContent({
  title,
  author,
  publish_time,
  content,
  cover_image,
  tags
}: ArticleContentProps) {
  const isDarkMode = document.body.classList.contains('dark-mode')

  return (
    <article style={{
      maxWidth: 800,
      margin: '0 auto',
      padding: '0 16px 60px'
    }}>
      {/* Title */}
      <Title
        level={1}
        style={{
          fontSize: 36,
          fontWeight: 700,
          marginBottom: 16,
          color: isDarkMode ? '#e8e8e8' : 'rgba(0,0,0,0.88)',
          lineHeight: 1.3
        }}
      >
        {title}
      </Title>

      {/* Meta info */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        marginBottom: 20,
        color: isDarkMode ? '#888' : '#666',
        fontSize: 14
      }}>
        {author && (
          <span>
            <Text strong style={{ color: isDarkMode ? '#aaa' : '#333' }}>作者</Text>
            {' '}{author}
          </span>
        )}
        {author && publish_time && <span>·</span>}
        {publish_time && <span>{publish_time}</span>}
      </div>

      {/* Tags */}
      {tags && tags.length > 0 && (
        <div style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          marginBottom: 24
        }}>
          {tags.map(tag => (
            <span
              key={tag}
              style={{
                display: 'inline-block',
                padding: '4px 12px',
                background: isDarkMode ? '#2d2d2d' : '#f0f0f0',
                borderRadius: 16,
                fontSize: 13,
                color: isDarkMode ? '#e8e8e8' : '#333'
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Cover Image */}
      {cover_image && (
        <img
          src={cover_image}
          alt={title}
          style={{
            width: '100%',
            maxHeight: 400,
            objectFit: 'cover',
            borderRadius: 12,
            marginBottom: 32
          }}
        />
      )}

      {/* Article Body */}
      <div
        className="article-body"
        style={{
          lineHeight: 1.8,
          fontSize: 16,
          color: isDarkMode ? '#d0d0d0' : '#333'
        }}
      >
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>

      <style>{`
        .article-body {
          max-width: 720px;
        }
        .article-body h1 {
          font-size: 1.75em;
          margin-top: 2em;
          margin-bottom: 0.75em;
          font-weight: 600;
          color: inherit;
        }
        .article-body h2 {
          font-size: 1.5em;
          margin-top: 1.75em;
          margin-bottom: 0.6em;
          font-weight: 600;
          color: inherit;
        }
        .article-body h3 {
          font-size: 1.25em;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          font-weight: 600;
          color: inherit;
        }
        .article-body p {
          margin-bottom: 1.25em;
        }
        .article-body img {
          max-width: 100%;
          height: auto;
          border-radius: 8px;
          margin: 1.5em 0;
        }
        .article-body pre {
          background: ${isDarkMode ? '#1a1a1a' : '#f5f5f5'};
          padding: 16px 20px;
          border-radius: 8px;
          overflow-x: auto;
          margin: 1.5em 0;
        }
        .article-body code {
          font-family: 'Fira Code', 'Monaco', monospace;
          font-size: 0.9em;
        }
        .article-body :not(pre) > code {
          background: ${isDarkMode ? '#2d2d2d' : '#f0f0f0'};
          padding: 2px 6px;
          border-radius: 4px;
        }
        .article-body blockquote {
          border-left: 4px solid ${isDarkMode ? '#555' : '#ddd'};
          padding-left: 20px;
          margin: 1.5em 0;
          color: ${isDarkMode ? '#999' : '#666'};
          font-style: italic;
        }
        .article-body ul, .article-body ol {
          margin: 1em 0;
          padding-left: 1.5em;
        }
        .article-body li {
          margin: 0.5em 0;
        }
        .article-body a {
          color: #1890ff;
          text-decoration: none;
        }
        .article-body a:hover {
          text-decoration: underline;
        }
        .article-body hr {
          border: none;
          border-top: 1px solid ${isDarkMode ? '#333' : '#e8e8e8'};
          margin: 2em 0;
        }
        .article-body table {
          width: 100%;
          border-collapse: collapse;
          margin: 1.5em 0;
        }
        .article-body th, .article-body td {
          border: 1px solid ${isDarkMode ? '#333' : '#e8e8e8'};
          padding: 8px 12px;
          text-align: left;
        }
        .article-body th {
          background: ${isDarkMode ? '#2d2d2d' : '#f5f5f5'};
        }
      `}</style>
    </article>
  )
}