import { useState, useEffect } from 'react'
import { Typography, Button, Image } from 'antd'
import { ExportOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'

const { Title, Text } = Typography

interface ArticleContentProps {
  title: string
  author?: string
  publish_time?: string
  content: string
  cover_image?: string
  images?: string[]
  tags?: string[]
  url?: string
}

export default function ArticleContent({
  title,
  author,
  publish_time,
  content,
  cover_image,
  images,
  tags,
  url,
}: ArticleContentProps) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [previewVisible, setPreviewVisible] = useState(false)

  // 合并图片列表：优先用 images，fallback 到 cover_image
  const allImages = (images && images.length > 0)
    ? images
    : (cover_image ? [cover_image] : [])

  // images / cover_image 变化时重置索引，防止越界
  useEffect(() => {
    setCurrentIdx(0)
  }, [images, cover_image])

  const hasBanner = allImages.length > 0
  const hasMultiple = allImages.length > 1

  const prev = () => setCurrentIdx(i => (i - 1 + allImages.length) % allImages.length)
  const next = () => setCurrentIdx(i => (i + 1) % allImages.length)

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
          color: 'rgba(0,0,0,0.88)',
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
        marginBottom: 12,
        color: '#666',
        fontSize: 14
      }}>
        {author && (
          <span>
            <Text strong style={{ color: '#333' }}>作者</Text>
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
                background: '#f0f0f0',
                borderRadius: 16,
                fontSize: 13,
                color: '#333'
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* View Original Link */}
      {url && (
        <div style={{ marginBottom: 24 }}>
          <a href={url} target="_blank" rel="noopener noreferrer">
            <Button icon={<ExportOutlined />} size="small">
              查看原文
            </Button>
          </a>
        </div>
      )}

      {/* Image Banner / Carousel */}
      {hasBanner && (
        <div style={{ position: 'relative', marginBottom: 32, borderRadius: 12, overflow: 'hidden', background: '#000' }}>
          {/* 隐藏的 Image.PreviewGroup 用于点击放大 */}
          <Image.PreviewGroup
            preview={{ visible: previewVisible, onVisibleChange: setPreviewVisible, current: currentIdx }}
          >
            {allImages.map((src, i) => (
              <Image key={i} src={src} style={{ display: 'none' }} />
            ))}
          </Image.PreviewGroup>

          {/* 当前图片 */}
          <img
            src={allImages[currentIdx]}
            alt={`${title} - ${currentIdx + 1}`}
            onClick={() => setPreviewVisible(true)}
            style={{
              width: '100%',
              maxHeight: 440,
              objectFit: 'cover',
              display: 'block',
              cursor: 'zoom-in',
            }}
          />

          {/* 左右切换按钮（多图时才显示）*/}
          {hasMultiple && (
            <>
              <button
                onClick={prev}
                style={{
                  position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'rgba(0,0,0,0.4)', border: 'none', borderRadius: '50%',
                  width: 36, height: 36, cursor: 'pointer', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backdropFilter: 'blur(4px)',
                }}
              >
                <LeftOutlined />
              </button>
              <button
                onClick={next}
                style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'rgba(0,0,0,0.4)', border: 'none', borderRadius: '50%',
                  width: 36, height: 36, cursor: 'pointer', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backdropFilter: 'blur(4px)',
                }}
              >
                <RightOutlined />
              </button>

              {/* 圆点指示器 */}
              <div style={{
                position: 'absolute', bottom: 12, left: '50%', transform: 'translateX(-50%)',
                display: 'flex', gap: 6,
              }}>
                {allImages.map((_, i) => (
                  <span
                    key={i}
                    onClick={() => setCurrentIdx(i)}
                    style={{
                      width: i === currentIdx ? 20 : 8,
                      height: 8,
                      borderRadius: 4,
                      background: i === currentIdx ? '#fff' : 'rgba(255,255,255,0.5)',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  />
                ))}
              </div>

              {/* 图片计数 */}
              <div style={{
                position: 'absolute', top: 12, right: 12,
                background: 'rgba(0,0,0,0.45)', color: '#fff',
                fontSize: 12, padding: '2px 8px', borderRadius: 10,
                backdropFilter: 'blur(4px)',
              }}>
                {currentIdx + 1} / {allImages.length}
              </div>
            </>
          )}
        </div>
      )}

      {/* Article Body */}
      <div
        className="article-body"
        style={{
          lineHeight: 1.8,
          fontSize: 16,
          color: '#333'
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
          background: #f5f5f5;
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
          background: #f0f0f0;
          padding: 2px 6px;
          border-radius: 4px;
        }
        .article-body blockquote {
          border-left: 4px solid #ddd;
          padding-left: 20px;
          margin: 1.5em 0;
          color: #666;
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
          border-top: 1px solid #e8e8e8;
          margin: 2em 0;
        }
        .article-body table {
          width: 100%;
          border-collapse: collapse;
          margin: 1.5em 0;
        }
        .article-body th, .article-body td {
          border: 1px solid #e8e8e8;
          padding: 8px 12px;
          text-align: left;
        }
        .article-body th {
          background: #f5f5f5;
        }
      `}</style>
    </article>
  )
}