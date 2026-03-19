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

// 字段提示配置
const FIELD_TIPS = {
  name: '规则的显示名称，用于识别不同的抓取任务，例如："科技新闻头条"',
  source_type: '数据源类型：\n• playwright：浏览器渲染抓取，适用于JS动态加载的页面\n• http：直接HTTP请求，速度快但无法处理JS\n• rss：RSS订阅源，自动解析标准格式',
  source_url: '要抓取的网页URL，例如：\n• 列表页：https://example.com/news\n• RSS源：https://example.com/feed.xml\n• API：https://api.example.com/articles',
  detail_url_pattern: '正则表达式，用于过滤有效的文章链接。\n例如：https://example.com/article/\\d+ 会只匹配形如 /article/123 的URL\n用于排除分页、标签页等非文章链接',
  extract_config: 'Playwright两阶段抓取配置（JSON格式）：\n\n第一阶段【列表页】：\n• url：列表页URL\n• selector：文章容器选择器\n• link_attr：链接属性，默认 href\n• max_items：最大抓取数量，默认3条\n• item_fields：基本信息提取（标题、摘要、图片等）\n\n第二阶段【详情页】：\n• 访问每篇文章链接\n• 提取完整标题、内容、作者、发布时间等\n• 自动转Markdown保存',
  field_mapping: '字段映射配置（JSON格式）：\n将源数据的字段名映射到标准文章字段\n\n标准字段：title, link, content, description, author, date\n例如：{ "title": "article_title", "author": "writer.name" }',
  exclude_patterns: '排除的URL正则表达式，多个用逗号分隔\n\n例如：["/tag/sponsored", "/category/ads", "/page/\\d+"]\n会排除所有包含 /tag/sponsored、/category/ads 或分页链接的URL',
  headers_config: '自定义HTTP请求头（JSON格式）\n\n例如：{"Referer": "https://example.com", "Accept-Language": "en-US"}\n可用于绕过简单的反爬机制',
  delay_min: '抓取请求之间的最小等待时间（秒）\n\n设置延迟防止请求过快被封，例如设为1表示每次请求后至少等待1秒',
  delay_max: '抓取请求之间的最大等待时间（秒）\n\n与min配合使用，随机等待min~max秒。例如1-3秒表示每次等待1-3秒',
  user_agent: '自定义User-Agent字符串\n\n不设置则使用浏览器默认UA。可用于伪装成特定浏览器或移动端',
  cron_expression: 'Cron定时表达式，定义自动抓取计划\n\n格式：分 时 日 月 周\n• 0 8 * * *：每天早上8点\n• */30 * * * *：每30分钟\n• 0 * * * *：每小时\n• 0 0 * * 0：每周日午夜',
  status: '规则状态：\n• disabled：禁用，不执行定时任务\n• enabled：启用，按cron_expression定时执行',
  proxy_config: '代理服务器配置（JSON格式）\n\n格式：{"server": "http://proxy:8080", "username": "user", "password": "pass"}\n用于需要代理访问的网站',
  cookie_config: 'Cookie认证配置（JSON格式）\n\n格式：{"name": "session_id", "value": "xxx"}\n用于需要登录才能访问的内容',
  auth_type: '认证类型：\n• none：无认证\n• basic：HTTP Basic认证\n• bearer：Bearer Token认证\n• cookie：Cookie认证',
  auth_config: '认证凭据配置（JSON格式）\n\n根据auth_type配置：\n• basic：{"username": "user", "password": "pass"}\n• bearer：{"token": "xxx"}\n• cookie：{"name": "session", "value": "xxx"}',
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
        tooltip={FIELD_TIPS.source_url}
        rules={[{ required: true, message: '请输入 RSS 订阅链接' }]}
      >
        <Input placeholder="https://example.com/feed.xml" />
      </Form.Item>
      <Form.Item
        name="field_mapping"
        label="字段映射"
        tooltip={FIELD_TIPS.field_mapping}
      >
        <TextArea
          rows={6}
          placeholder={JSON.stringify(DEFAULT_RSS_CONFIG, null, 2)}
          style={{ fontFamily: 'monospace' }}
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
        tooltip={FIELD_TIPS.source_url}
        rules={[{ required: true, message: '请输入 API 地址' }]}
      >
        <Input placeholder="https://api.example.com/articles" />
      </Form.Item>
      <Form.Item
        name="field_mapping"
        label="字段映射"
        tooltip={FIELD_TIPS.field_mapping}
      >
        <TextArea
          rows={6}
          placeholder={JSON.stringify(DEFAULT_API_CONFIG.mapping, null, 2)}
          style={{ fontFamily: 'monospace' }}
        />
      </Form.Item>
      <Form.Item
        name="headers_config"
        label="请求头"
        tooltip={FIELD_TIPS.headers_config}
      >
        <TextArea
          rows={2}
          placeholder='{"Authorization": "Bearer token"}'
          style={{ fontFamily: 'monospace' }}
        />
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
        tooltip={FIELD_TIPS.source_url}
      >
        <Input placeholder="https://example.com/news" />
      </Form.Item>

      <Form.Item
        name="detail_url_pattern"
        label="详情页 URL 匹配 (正则)"
        tooltip={FIELD_TIPS.detail_url_pattern}
      >
        <Input placeholder="如: https://example.com/article/.*" />
      </Form.Item>

      <Form.Item
        name="extract_config"
        label="抓取配置 (JSON)"
        tooltip={
          <div style={{ maxWidth: 500, color: '#fff', background: 'rgba(0,0,0,0.9)', padding: 12, borderRadius: 4, fontSize: 13 }}>
            <div>
              <Text strong style={{ color: '#fff' }}>两阶段抓取流程：</Text>
            </div>
            <ol style={{ paddingLeft: 16, margin: '8px 0', fontSize: 12 }}>
              <li><Text style={{ color: '#e0e0e0' }}>从列表页提取文章链接+基本信息</Text></li>
              <li><Text style={{ color: '#e0e0e0' }}>遍历待抓取文章 → 访问详情页 → 提取完整内容 → 保存为markdown</Text></li>
            </ol>
            <div style={{ marginTop: 8 }}>
              <Text strong style={{ color: '#fff' }}>list.selector:</Text>
              <Text style={{ color: '#b0b0b0' }}> 文章容器选择器，如 .article-item</Text>
            </div>
            <div style={{ marginTop: 4 }}>
              <Text strong style={{ color: '#fff' }}>list.max_items:</Text>
              <Text style={{ color: '#b0b0b0' }}> 列表页抓取数量，默认3条</Text>
            </div>
            <div style={{ marginTop: 4 }}>
              <Text strong style={{ color: '#fff' }}>detail.*:</Text>
              <Text style={{ color: '#b0b0b0' }}> 详情页内容选择器</Text>
            </div>
            <Text style={{ color: '#b0b0b0', marginTop: 8, display: 'block' }}>配置示例：</Text>
            <pre style={{ fontSize: 11, background: '#1a1a1a', color: '#52c41a', padding: 8, marginTop: 4, overflow: 'auto', maxHeight: 300, borderRadius: 4 }}>
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

      <Form.Item
        name="exclude_patterns"
        label="排除 URL 模式"
        tooltip={FIELD_TIPS.exclude_patterns}
        style={{ marginTop: 16 }}
      >
        <TextArea
          rows={2}
          placeholder='["/tag/", "/category/"]'
          style={{ fontFamily: 'monospace' }}
        />
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
        <Form.Item
          name="name"
          label="规则名称"
          tooltip={FIELD_TIPS.name}
          rules={[{ required: true, message: '请输入规则名称' }]}
        >
          <Input placeholder="给规则起个名字，如：科技新闻头条" />
        </Form.Item>

        <Form.Item
          label="抓取方式"
          tooltip={FIELD_TIPS.source_type}
        >
          <Segmented
            options={SOURCE_TYPE_OPTIONS}
            value={sourceType}
            onChange={(value) => handleSourceTypeChange(value as string)}
          />
        </Form.Item>

        {sourceType === 'rss' && renderRssFields()}
        {sourceType === 'api' && renderApiFields()}
        {sourceType === 'playwright' && renderPlaywrightFields()}

        <Form.Item
          name="status"
          label="规则状态"
          tooltip={FIELD_TIPS.status}
        >
          <Select
            options={[
              { label: '禁用', value: 'disabled' },
              { label: '启用', value: 'enabled' },
            ]}
          />
        </Form.Item>

        <Form.Item
          name="cron_expression"
          label="定时表达式"
          tooltip={FIELD_TIPS.cron_expression}
        >
          <Input placeholder="0 8 * * *" />
        </Form.Item>

        <Form.Item
          name="delay_min"
          label="最小延迟(秒)"
          tooltip={FIELD_TIPS.delay_min}
        >
          <InputNumber min={0} />
        </Form.Item>

        <Form.Item
          name="delay_max"
          label="最大延迟(秒)"
          tooltip={FIELD_TIPS.delay_max}
        >
          <InputNumber min={0} />
        </Form.Item>

        <Form.Item
          name="user_agent"
          label="User-Agent"
          tooltip={FIELD_TIPS.user_agent}
        >
          <Input placeholder="不设置则使用浏览器默认UA" />
        </Form.Item>

        <Form.Item
          name="proxy_config"
          label="代理配置"
          tooltip={FIELD_TIPS.proxy_config}
        >
          <TextArea
            rows={2}
            placeholder='{"server": "http://proxy:8080"}'
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>

        <Form.Item
          name="cookie_config"
          label="Cookie配置"
          tooltip={FIELD_TIPS.cookie_config}
        >
          <TextArea
            rows={2}
            placeholder='{"name": "session_id", "value": "xxx"}'
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>

        <Form.Item
          name="auth_type"
          label="认证类型"
          tooltip={FIELD_TIPS.auth_type}
        >
          <Select
            options={[
              { label: '无认证', value: 'none' },
              { label: 'Basic认证', value: 'basic' },
              { label: 'Bearer Token', value: 'bearer' },
              { label: 'Cookie认证', value: 'cookie' },
            ]}
          />
        </Form.Item>

        <Form.Item
          name="auth_config"
          label="认证配置"
          tooltip={FIELD_TIPS.auth_config}
        >
          <TextArea
            rows={2}
            placeholder='{"username": "user", "password": "pass"}'
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}
