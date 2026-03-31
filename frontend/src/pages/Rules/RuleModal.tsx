import { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, InputNumber, Segmented, Button, Space, Typography, Checkbox, Switch, Divider } from 'antd'
import { createRule, updateRule, getRuleEffectiveTagSchema } from '../../api'

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
  render: '渲染方式：\n• http：直接HTTP请求，速度快，适用于静态内容（XML、JSON、Markdown等）\n• browser：浏览器渲染抓取，适用于JS加载的动态页面\n\n💡 不设置时自动推断：\n• content_type 为 xml/json/markdown/text → http\n• content_type 为 html 或未设置 → browser',
  content_type: '内容格式：\n• html：HTML 网页（默认）\n• xml：XML 格式（RSS/Atom）\n• json：JSON API 接口\n• markdown：Markdown 文件（如 GitHub README）\n• text：纯文本\n\n💡 不设置时默认 html',
  source_url: '要抓取的网页URL，例如：\n• HTML：https://example.com/news\n• RSS：https://example.com/feed.xml\n• API：https://api.example.com/articles\n• Markdown：https://raw.githubusercontent.com/.../README.md',
  detail_url_pattern: '正则表达式，用于过滤有效的文章链接。\n例如：https://example.com/article/\\d+ 会只匹配形如 /article/123 的URL\n用于排除分页、标签页等非文章链接',
  extract_config: '两阶段抓取配置（JSON格式）：\n\n第一阶段【列表页】：\n• url：列表页URL\n• selector：文章容器选择器\n• link_attr：链接属性，默认 href\n• max_items：最大抓取数量，默认3条\n• item_fields：基本信息提取（标题、摘要、图片等）\n\n第二阶段【详情页】：\n• 访问每篇文章链接\n• 提取完整标题、内容、作者、发布时间等\n• 自动转Markdown保存',
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

// 内容类型选项
const CONTENT_TYPE_OPTIONS = [
  { label: 'HTML', value: 'html' },
  { label: 'XML (RSS)', value: 'xml' },
  { label: 'JSON API', value: 'json' },
  { label: 'Markdown', value: 'markdown' },
  { label: '纯文本', value: 'text' },
]

// 渲染方式选项
const RENDER_OPTIONS = [
  { label: 'HTTP 直接请求', value: 'http' },
  { label: '浏览器渲染', value: 'browser' },
]

// 翻译语言选项
const TRANSLATION_LANGUAGE_OPTIONS = [
  { label: '中文', value: 'zh' },
  { label: '英文', value: 'en' },
  { label: '日文', value: 'ja' },
  { label: '韩文', value: 'ko' },
  { label: '法文', value: 'fr' },
  { label: '德文', value: 'de' },
  { label: '西班牙文', value: 'es' },
  { label: '俄文', value: 'ru' },
  { label: '阿拉伯文', value: 'ar' },
  { label: '葡萄牙文', value: 'pt' },
  { label: '意大利文', value: 'it' },
  { label: '越南文', value: 'vi' },
  { label: '泰文', value: 'th' },
  { label: '印尼文', value: 'id' },
]

// 翻译字段选项
const TRANSLATION_FIELD_OPTIONS = [
  { label: '标题', value: 'title' },
  { label: '摘要', value: 'summary' },
  { label: '正文', value: 'content' },
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

// 默认的 RSS 配置模板（合并到 extract_config）
const DEFAULT_RSS_CONFIG = {
  mapping: {
    title: 'title',
    link: 'link',
    content: 'content:encoded',
    description: 'description',
    author: 'author',
    date: 'pubDate'
  },
  list: {
    max_items: 10
  }
}

// 默认的 API 配置模板（合并到 extract_config）
const DEFAULT_API_CONFIG = {
  mapping: {
    title: 'title',
    url: 'url',
    content: 'body',
    author: 'author.name',
    date: 'created_at'
  },
  list: {
    max_items: 10
  }
}

export default function RuleModal({ visible, rule, onClose, onSuccess }: RuleModalProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [render, setRender] = useState<string>('browser')
  const [contentType, setContentType] = useState<string>('html')
  const [translationFormData, setTranslationFormData] = useState({
    target_lang: 'zh',
    source_lang: '',
    fields: ['summary', 'content'] as string[],
    concurrency: 3,
    generate_tags: false,
    tag_schema: [] as string[],
    max_tags: 3,
  })
  const [effectiveTagConfig, setEffectiveTagConfig] = useState<{
    tag_schema: string[]
    generate_tags: boolean
  }>({ tag_schema: [], generate_tags: false })

  useEffect(() => {
    if (visible && rule) {
      form.setFieldsValue(rule)
      setRender(rule.render || 'browser')
      setContentType(rule.content_type || 'html')
      // 初始化翻译配置
      if (rule.translation_config) {
        try {
          const config = typeof rule.translation_config === 'string'
            ? JSON.parse(rule.translation_config)
            : rule.translation_config
          setTranslationFormData({
            target_lang: config.target_lang || '',
            source_lang: config.source_lang || '',
            fields: config.fields || ['summary', 'content'],
            concurrency: config.concurrency || 3,
            generate_tags: config.generate_tags || false,
            tag_schema: config.tag_schema || [],
            max_tags: config.max_tags || 3,
          })
        } catch {
          setTranslationFormData({
            target_lang: 'zh',
            source_lang: '',
            fields: ['summary', 'content'],
            concurrency: 3,
            generate_tags: false,
            tag_schema: [],
            max_tags: 3,
          })
        }
      } else {
        setTranslationFormData({
          target_lang: 'zh',
          source_lang: '',
          fields: ['summary', 'content'],
          concurrency: 3,
          generate_tags: false,
          tag_schema: [],
          max_tags: 3,
        })
      }
      // 获取有效的标签配置
      fetchEffectiveTagConfig()
    } else if (visible) {
      form.resetFields()
      setRender('browser')
      setContentType('html')
      setTranslationFormData({
        target_lang: 'zh',
        source_lang: '',
        fields: ['summary', 'content'],
        concurrency: 3,
        generate_tags: false,
        tag_schema: [],
        max_tags: 3,
      })
      form.setFieldsValue({
        render: 'browser',
        content_type: 'html',
        delay_min: 1,
        delay_max: 3,
        status: 'disabled',
      })
      // 获取有效的标签配置
      fetchEffectiveTagConfig()
    }
  }, [visible, rule])

  // 获取规则的有效标签配置
  const fetchEffectiveTagConfig = async () => {
    if (rule) {
      try {
        const res = await getRuleEffectiveTagSchema(rule.id)
        setEffectiveTagConfig(res.data)
      } catch (error) {
        console.error('获取标签配置失败', error)
      }
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // 处理翻译配置 - 选择目标语言即启用翻译
      if (translationFormData.target_lang) {
        const transConfig: any = {
          target_lang: translationFormData.target_lang,
          source_lang: translationFormData.source_lang,
          fields: translationFormData.fields,
          concurrency: translationFormData.concurrency,
        }
        // 如果启用了打标签
        if (translationFormData.generate_tags) {
          transConfig.generate_tags = true
        }
        values.translation_config = JSON.stringify(transConfig)
      } else {
        values.translation_config = undefined
      }
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

  const handleRenderChange = (value: string) => {
    setRender(value)
    form.setFieldValue('render', value)
    // 根据 render 自动推断 content_type
    if (value === 'http') {
      setContentType('html')
      form.setFieldValue('content_type', 'html')
    }
  }

  const handleContentTypeChange = (value: string) => {
    setContentType(value)
    form.setFieldValue('content_type', value)
    // 根据 content_type 自动推断 render
    if (value === 'xml') {
      setRender('http')
      form.setFieldValue('render', 'http')
    } else if (value === 'json') {
      setRender('http')
      form.setFieldValue('render', 'http')
    } else if (value === 'markdown') {
      setRender('http')
      form.setFieldValue('render', 'http')
    } else if (value === 'text') {
      setRender('http')
      form.setFieldValue('render', 'http')
    }
  }

  // 填充默认配置
  const fillDefaultConfig = (type: string) => {
    if (type === 'playwright' || type === 'browser') {
      form.setFieldValue('extract_config', JSON.stringify(DEFAULT_PLAYWRIGHT_CONFIG, null, 2))
    } else if (type === 'rss' || type === 'xml') {
      form.setFieldValue('field_mapping', JSON.stringify(DEFAULT_RSS_CONFIG, null, 2))
    } else if (type === 'api' || type === 'json') {
      form.setFieldValue('field_mapping', JSON.stringify(DEFAULT_API_CONFIG.mapping, null, 2))
    }
  }

  // 渲染 HTML/Markdown 配置
  const renderHtmlFields = () => (
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
        tooltip={FIELD_TIPS.extract_config}
      >
        <TextArea
          rows={12}
          style={{ fontFamily: 'monospace' }}
          placeholder={JSON.stringify(DEFAULT_PLAYWRIGHT_CONFIG, null, 2)}
        />
      </Form.Item>

      <Space>
        <Button type="link" onClick={() => fillDefaultConfig('browser')}>
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

  // 渲染 XML/RSS 配置
  const renderXmlFields = () => (
    <>
      <Form.Item
        name="source_url"
        label="XML/RSS 链接"
        tooltip={FIELD_TIPS.source_url}
        rules={[{ required: true, message: '请输入 XML/RSS 链接' }]}
      >
        <Input placeholder="https://example.com/feed.xml" />
      </Form.Item>

      <Form.Item
        name="extract_config"
        label="抓取配置"
        tooltip="包含字段映射和最大抓取数量配置"
      >
        <TextArea
          rows={8}
          placeholder={JSON.stringify(DEFAULT_RSS_CONFIG, null, 2)}
          style={{ fontFamily: 'monospace' }}
        />
      </Form.Item>
      <Button type="link" onClick={() => fillDefaultConfig('xml')}>
        填充默认配置
      </Button>
    </>
  )

  // 渲染 JSON API 配置
  const renderJsonFields = () => (
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
        name="extract_config"
        label="抓取配置"
        tooltip="包含字段映射和最大抓取数量配置"
      >
        <TextArea
          rows={8}
          placeholder={JSON.stringify(DEFAULT_API_CONFIG, null, 2)}
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
      <Button type="link" onClick={() => fillDefaultConfig('json')}>
        填充默认配置
      </Button>
    </>
  )

  // 渲染 Markdown 配置
  const renderMarkdownFields = () => (
    <>
      <Form.Item
        name="source_url"
        label="Markdown 文件 URL"
        tooltip={FIELD_TIPS.source_url}
        rules={[{ required: true, message: '请输入 Markdown 文件 URL' }]}
      >
        <Input placeholder="https://raw.githubusercontent.com/.../README.md" />
      </Form.Item>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        用于提取 GitHub README 等 Markdown 文件中的链接
      </Text>
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
          label="渲染方式"
          tooltip={FIELD_TIPS.render}
        >
          <Segmented
            options={RENDER_OPTIONS}
            value={render}
            onChange={(value) => handleRenderChange(value as string)}
          />
        </Form.Item>

        <Form.Item
          label="内容格式"
          tooltip={FIELD_TIPS.content_type}
        >
          <Segmented
            options={CONTENT_TYPE_OPTIONS}
            value={contentType}
            onChange={(value) => handleContentTypeChange(value as string)}
          />
        </Form.Item>

        {contentType === 'html' && renderHtmlFields()}
        {contentType === 'xml' && renderXmlFields()}
        {contentType === 'json' && renderJsonFields()}
        {contentType === 'markdown' && renderMarkdownFields()}

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

        {/* 翻译配置 */}
        <Form.Item
          label="翻译"
          tooltip="对抓取的摘要、正文等内容进行翻译"
        >
          <Space direction="vertical" size="small">
            <Select
              value={translationFormData.target_lang}
              onChange={(value) => setTranslationFormData(prev => ({ ...prev, target_lang: value }))}
              options={TRANSLATION_LANGUAGE_OPTIONS}
              placeholder="选择目标语言（留空则不翻译）"
              style={{ width: 200 }}
              allowClear
            />
            {translationFormData.target_lang && (
              <>
                <Select
                  value={translationFormData.source_lang}
                  onChange={(value) => setTranslationFormData(prev => ({ ...prev, source_lang: value }))}
                  options={[
                    { label: '自动检测', value: '' },
                    ...TRANSLATION_LANGUAGE_OPTIONS
                  ]}
                  placeholder="源语言（留空自动检测）"
                  style={{ width: 200 }}
                  allowClear
                />
                <Checkbox.Group
                  value={translationFormData.fields}
                  onChange={(checkedValues) => setTranslationFormData(prev => ({ ...prev, fields: checkedValues as string[] }))}
                  options={TRANSLATION_FIELD_OPTIONS}
                />
                <Space>
                  <span>并发数：</span>
                  <InputNumber
                    min={1}
                    max={10}
                    value={translationFormData.concurrency}
                    onChange={(value) => setTranslationFormData(prev => ({ ...prev, concurrency: value || 3 }))}
                    style={{ width: 80 }}
                  />
                  <span style={{ color: '#999' }}>1-10，避免限流</span>
                </Space>

                <Divider style={{ margin: '8px 0' }} />

                {/* 标签配置 */}
                <Space>
                  <span>自动打标签：</span>
                  <Switch
                    checked={translationFormData.generate_tags}
                    onChange={(checked) => setTranslationFormData(prev => ({ ...prev, generate_tags: checked }))}
                  />
                  {translationFormData.generate_tags && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      共 {effectiveTagConfig.tag_schema.length} 个标签可用
                    </Text>
                  )}
                </Space>

                {translationFormData.generate_tags && translationFormData.target_lang && (
                  <div style={{ marginLeft: 24, marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      标签池：{effectiveTagConfig.tag_schema.length > 0
                        ? effectiveTagConfig.tag_schema.slice(0, 5).join(', ') + (effectiveTagConfig.tag_schema.length > 5 ? '...' : '')
                        : '暂无标签，请先在标签管理中添加'
                      }
                    </Text>
                  </div>
                )}
              </>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}
