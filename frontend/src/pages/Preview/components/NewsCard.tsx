import { Card, Tag } from 'antd'
import { Link } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

interface NewsCardProps {
  article: {
    id: number
    title: string
    summary: string
    cover_image: string
    rule_name: string
    created_at: string
    tags: string[]
  }
}

export default function NewsCard({ article }: NewsCardProps) {
  const isDarkMode = document.body.classList.contains('dark-mode')

  return (
    <Link to={`/preview/article/${article.id}`} style={{ display: 'block' }}>
      <Card
        hoverable
        style={{
          height: '100%',
          borderRadius: 12,
          overflow: 'hidden',
          transition: 'transform 0.2s, box-shadow 0.2s',
        }}
        styles={{
          body: {
            padding: 0,
            background: isDarkMode ? '#1f1f1f' : '#fff',
          }
        }}
        onMouseEnter={(e) => {
          const card = e.currentTarget as HTMLElement
          card.style.transform = 'translateY(-4px)'
          card.style.boxShadow = isDarkMode ? '0 8px 24px rgba(0,0,0,0.4)' : '0 8px 24px rgba(0,0,0,0.12)'
        }}
        onMouseLeave={(e) => {
          const card = e.currentTarget as HTMLElement
          card.style.transform = 'translateY(0)'
          card.style.boxShadow = 'none'
        }}
      >
        {/* Cover Image with Gradient Overlay */}
        <div style={{ position: 'relative', height: 200, overflow: 'hidden' }}>
          {article.cover_image ? (
            <img
              alt={article.title}
              src={article.cover_image}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <div style={{
              width: '100%',
              height: '100%',
              background: isDarkMode ? '#2d2d2d' : '#f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDarkMode ? '#666' : '#999'
            }}>
              无封面图
            </div>
          )}

          {/* Gradient overlay */}
          <div style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '60%',
            background: 'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%)',
            pointerEvents: 'none'
          }} />

          {/* Tags on image */}
          {article.tags && article.tags.length > 0 && (
            <div style={{
              position: 'absolute',
              top: 12,
              left: 12,
              display: 'flex',
              gap: 6,
              flexWrap: 'wrap'
            }}>
              {article.tags.slice(0, 2).map(tag => (
                <Tag
                  key={tag}
                  style={{
                    borderRadius: 12,
                    background: 'rgba(255,255,255,0.25)',
                    border: 'none',
                    color: '#fff',
                    backdropFilter: 'blur(4px)'
                  }}
                >
                  {tag}
                </Tag>
              ))}
            </div>
          )}

          {/* Source/Time badge */}
          <div style={{
            position: 'absolute',
            bottom: 12,
            right: 12,
            display: 'flex',
            gap: 8,
            alignItems: 'center'
          }}>
            <span style={{
              fontSize: 11,
              color: 'rgba(255,255,255,0.85)',
              background: 'rgba(0,0,0,0.3)',
              padding: '2px 8px',
              borderRadius: 10,
              backdropFilter: 'blur(4px)'
            }}>
              {article.rule_name}
            </span>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '16px' }}>
          <h3 style={{
            fontSize: 16,
            fontWeight: 600,
            marginBottom: 8,
            color: isDarkMode ? '#e8e8e8' : 'rgba(0,0,0,0.88)',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            lineHeight: 1.4,
            minHeight: 44
          }}>
            {article.title}
          </h3>

          {article.summary && (
            <p style={{
              fontSize: 13,
              color: isDarkMode ? '#888' : '#999',
              marginBottom: 8,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              lineHeight: 1.5
            }}>
              {article.summary}
            </p>
          )}

          <span style={{
            fontSize: 12,
            color: isDarkMode ? '#666' : '#aaa'
          }}>
            {dayjs(article.created_at).fromNow()}
          </span>
        </div>
      </Card>
    </Link>
  )
}
