import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Button, Tooltip, Spin, message } from 'antd';
import { ArrowLeftOutlined, BgColorsOutlined, LinkOutlined } from '@ant-design/icons';
import { getArticle, getArticleMarkdown } from '../../api';
import ArticleContent from './components/ArticleContent';

const { Header, Content } = Layout;

export default function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<any>(null);
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

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
        setMarkdown(markdownRes.data.content || '');
      } catch (error) {
        message.error('加载文章失败');
        navigate('/preview');
      } finally {
        setLoading(false);
      }
    };

    loadArticle();
  }, [id, navigate]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle('dark-mode', !darkMode);
  };

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
    <Layout style={{ minHeight: '100vh', background: darkMode ? '#141414' : '#fff' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: darkMode ? '#1f1f1f' : '#001529',
        padding: '0 24px'
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
          <Tooltip title="深色模式">
            <Button
              type="text"
              icon={<BgColorsOutlined />}
              onClick={toggleDarkMode}
              style={{ color: '#fff' }}
            />
          </Tooltip>
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
        <ArticleContent
          title={article.title}
          author={article.author}
          publish_time={article.publish_time}
          content={markdown}
          cover_image={article.cover_image}
          tags={tags}
        />
      </Content>
    </Layout>
  );
}