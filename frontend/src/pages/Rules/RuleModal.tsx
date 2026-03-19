import { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, InputNumber, Segmented, Tabs, Button, Space, Typography } from 'antd'
import { createRule, updateRule } from '../../api'

const { TextArea } = Input
const { Text } = Typography

interface RuleModalProps {
  visible: boolean
  rule: any
  onClose: () => void
  onSuccess: () => void
}

const SOURCE_TYPE_OPTIONS = [
  { label: 'RSS 订阅', value: 'rss' },
  { label: 'API 接口', value: 'api' },
  { label: '网页抓取', value: 'playwright' },
]

// 默认的 Playwright 配置模板（两阶段抓取）
const DEFAULT_PLAYWRIGHT_CONFIG = {
  list: {
    url: '',
    selector: '.article-item',  // 列表中每个文章的容器选择器
    link_attr: 'href',
    max_items: 3,  // 默认抓取前3条，可设置为更大值或移除以抓取全部
    // 列表中每个item的基本信息提取配置
    item_fields: {
      title: { selector: '.title, h3', type: 'text' },
      summary: { selector: '.desc, .summary, p', type: 'text' },
      image: { selector: 'img', type: 'attribute', attr: 'src' },
      date: { selector: '.date, .time', type: 'text' },
      author: { selector: '.author', type: 'text' }
    }
  },
  detail: {
    title: { selector: 'h1', type: 'text' },
    content: { selector: 'article, .content, .article-content', type: 'html' },
    author: { selector: '.author, .name', type: 'text' },
    date: { selector: '.date, .time, time', type: 'text' },
    image: { selector: 'img.cover', type: 'attribute', attr: 'src' }
  }
}

// 默认的 RSS 配置模板
const DEFAULT_RSS_CONFIG = {
  title: 'title',
  link: 'link',
  content: 'content:encoded',
  description: 'description',
  author: 'author',
  date: 'pubDate'
}

// 默认的 API 配置模板
const DEFAULT_API_CONFIG = {
  items_path: 'data.items',
  mapping: {
    title: 'title',
    url: 'url',
    content: 'body',
    author: 'author.name',
    date: 'created_at'
  }
}

export default function RuleModal({ visible, rule, onClose, onSuccess }: RuleModalProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [sourceType, setSourceType] = useState<string>('playwright')

  useEffect(() => {
    if (visible && rule) {
      form.setFieldsValue(rule)
      setSourceType(rule.source_type || 'playwright')
    } else if (visible) {
      form.resetFields()
      setSourceType('playwright')
      form.setFieldsValue({
        source_type: 'playwright',
        delay_min: 1,
        delay_max: 3,
        status: 'disabled',
      })
    }
  }, [visible, rule])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      if (rule) {
        await updateRule(rule.id, values)
      } else {
        await createRule(values)
      }
      onSuccess()
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSourceTypeChange = (value: string) => {
    setSourceType(value)
    form.setFieldValue('source_type', value)
  }

  // 填充默认配置
  const fillDefaultConfig = (type: string) => {
    if (type === 'playwright') {
      form.setFieldValue('extract_config', JSON.stringify(DEFAULT_PLAYWRIGHT_CONFIG, null, 2))
    } else if (type === 'rss') {
      form.setFieldValue('field_mapping', JSON.stringify(DEFAULT_RSS_CONFIG, null, 2))
    } else if (type === 'api') {
      form.setFieldValue('field_mapping', JSON.stringify(DEFAULT_API_CONFIG.mapping, null, 2))
    }
  }

  // 渲染 RSS 模式配置
  const renderRssFields = () => (
    <>
      <Form.Item
        name="source_url"
        label="RSS 链接"
        rules={[{ required: true, message: '请输入 RSS 订阅链接' }]}
      >
        <Input placeholder="https://example.com/feed.xml" />
      </Form.Item>
      <Form.Item
        name="field_mapping"
        label="字段映射"
        tooltip="映射 RSS 字段到文章字段"
      >
        <TextArea
          rows={6}
          placeholder={JSON.stringify(DEFAULT_RSS_CONFIG, null, 2)}
        />
      </Form.Item>
      <Button type="link" onClick={() => fillDefaultConfig('rss')}>
        填充默认配置
      </Button>
    </>
  )

  // 渲染 API 模式配置
  const renderApiFields = () => (
    <>
      <Form.Item
        name="source_url"
        label="API 地址"
        rules={[{ required: true, message: '请输入 API 地址' }]}
      >
        <Input placeholder="https://api.example.com/articles" />
      </Form.Item>
      <Form.Item
        name="field_mapping"
        label="字段映射"
        tooltip="JSON 格式，映射 API 响应字段到文章字段"
      >
        <TextArea
          rows={6}
          placeholder={JSON.stringify(DEFAULT_API_CONFIG.mapping, null, 2)}
        />
      </Form.Item>
      <Form.Item name="headers_config" label="请求头">
        <TextArea rows={2} placeholder='{"Authorization": "Bearer token"}' />
      </Form.Item>
      <Form.Item name="delay_min" label="最小延迟(秒)">
        <InputNumber min={0} />
      </Form.Item>
      <Form.Item name="delay_max" label="最大延迟(秒)">
        <InputNumber min={0} />
      </Form.Item>
      <Form.Item name="user_agent" label="User-Agent">
        <Input />
      </Form.Item>
      <Button type="link" onClick={() => fillDefaultConfig('api')}>
        填充默认配置
      </Button>
    </>
  )

  // 渲染 Playwright 模式配置
  const renderPlaywrightFields = () => (
    <>
      <Form.Item
        name="source_url"
        label="列表页 URL"
        tooltip="新闻列表页面URL，如: https://example.com/news"
      >
        <Input placeholder="https://example.com/news" />
      </Form.Item>

      <Form.Item
        name="detail_url_pattern"
        label="详情页 URL 匹配 (正则)"
      >
        <Input placeholder="如: https://example.com/article/.*" />
      </Form.Item>

      <Form.Item
        name="extract_config"
        label="抓取配置 (JSON)"
        tooltip={
          <div style={{ maxWidth: 500 }}>
            <div>
              <Text>两阶段抓取：</Text>
            </div>
            <ol style={{ paddingLeft: 16, margin: '8px 0', fontSize: 12 }}>
              <li>从列表页提取文章链接+基本信息 → 存入数据库（待抓取状态）</li>
              <li>遍历待抓取文章 → 访问详情页 → 提取完整内容 → 保存为markdown</li>
            </ol>
            <div style={{ marginTop: 8 }}>
              <Text strong>max_items:</Text>
              <Text type="secondary"> 列表页抓取数量，默认3条，设为更大值或移除此字段可抓取全部</Text>
            </div>
            <Text type="secondary" style={{ marginTop: 4, display: 'block' }}>配置示例：</Text>
            <pre style={{ fontSize: 11, background: '#f5f5f5', padding: 8, marginTop: 4, overflow: 'auto', maxHeight: 300 }}>
{JSON.stringify(DEFAULT_PLAYWRIGHT_CONFIG, null, 2)}
            </pre>
          </div>
        }
      >
        <TextArea
          rows={12}
          style={{ fontFamily: 'monospace' }}
          placeholder={JSON.stringify(DEFAULT_PLAYWRIGHT_CONFIG, null, 2)}
        />
      </Form.Item>

      <Space>
        <Button type="link" onClick={() => fillDefaultConfig('playwright')}>
          填充默认配置
        </Button>
      </Space>

      <Form.Item name="exclude_patterns" label="排除 URL 模式" style={{ marginTop: 16 }}>
        <TextArea rows={2} placeholder='["/tag/", "/category/"]' />
      </Form.Item>

      <Form.Item name="delay_min" label="最小延迟(秒)">
        <InputNumber min={0} />
      </Form.Item>
      <Form.Item name="delay_max" label="最大延迟(秒)">
        <InputNumber min={0} />
      </Form.Item>
      <Form.Item name="user_agent" label="User-Agent">
        <Input />
      </Form.Item>
    </>
  )

  return (
    <Modal
      title={rule ? '编辑规则' : '新建规则'}
      open={visible}
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={700}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
          <Input placeholder="给规则起个名字" />
        </Form.Item>

        <Form.Item label="抓取方式">
          <Segmented
            options={SOURCE_TYPE_OPTIONS}
            value={sourceType}
            onChange={(value) => handleSourceTypeChange(value as string)}
          />
        </Form.Item>

        {sourceType === 'rss' && renderRssFields()}
        {sourceType === 'api' && renderApiFields()}
        {sourceType === 'playwright' && renderPlaywrightFields()}

        <Form.Item name="cron_expression" label="定时表达式" tooltip="Cron 格式，如: 0 0 * * * 表示每天 0 点">
          <Input placeholder="0 0 * * *" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
