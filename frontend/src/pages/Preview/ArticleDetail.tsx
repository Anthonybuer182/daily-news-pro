import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Button, Tooltip, Spin, message } from 'antd';
import { ArrowLeftOutlined, LinkOutlined } from '@ant-design/icons';
import { getArticle, getArticleMarkdown } from '../../api';
import ArticleContent from './components/ArticleContent';

const { Header, Content } = Layout;

export default function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<any>(null);
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const loadArticle = async () => {
      setLoading(true);
      try {
        const [articleRes, markdownRes] = await Promise.all([
          getArticle(parseInt(id)),
          getArticleMarkdown(parseInt(id))
        ]);
        setArticle(articleRes.data);
        // Strip header lines (Source/Author/Date) and cover image from markdown
        const rawMarkdown = markdownRes.data.content || '';
        const cleanedMarkdown = rawMarkdown
          .replace(/^\*\*Source\*\*:.*\n?/gm, '')
          .replace(/^\*\*Author\*\*:.*\n?/gm, '')
          .replace(/^\*\*Date\*\*:.*\n?/gm, '')
          .replace(/^#.*\n?/, '') // Remove title line if it starts with #
          .replace(/^!\[[^\]]*\]\([^)]*\)\n?/gm, '') // Remove ![Cover](url) image
          .replace(/^\n+/, '') // Remove leading newlines
          .trim();
        setMarkdown(cleanedMarkdown);
      } catch (error) {
        message.error('加载文章失败');
        navigate('/preview');
      } finally {
        setLoading(false);
      }
    };

    loadArticle();
  }, [id, navigate]);

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  if (!article) {
    return null;
  }

  // 解析 tags
  let tags: string[] = [];
  if (article.tags) {
    try {
      tags = typeof article.tags === 'string' ? JSON.parse(article.tags) : article.tags;
    } catch {
      tags = [];
    }
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#fff' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/preview')}
            style={{ color: '#fff' }}
          >
            返回
          </Button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {article.url && (
            <Tooltip title="查看原文">
              <Button
                type="text"
                icon={<LinkOutlined />}
                onClick={() => window.open(article.url, '_blank')}
                style={{ color: '#fff' }}
              />
            </Tooltip>
          )}
        </div>
      </Header>
      <Content style={{ padding: '24px 0' }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '16px' }}>
          <ArticleContent
            title={article.title}
            author={article.author}
            publish_time={article.publish_time}
            content={markdown}
            cover_image={article.cover_image}
            tags={tags}
          />
        </div>
      </Content>
    </Layout>
  );
}