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
  source_url: '列表页URL，例如：https://example.com/news',
  max_items: '最大抓取数量，默认3条',
  render: '渲染方式：\n• http：直接HTTP请求，速度快，适用于静态内容（XML、JSON、Markdown等）\n• browser：浏览器渲染抓取，适用于JS加载的动态页面\n\n💡 不设置时自动推断：\n• content_type 为 xml/json/markdown/text → http\n• content_type 为 html 或未设置 → browser',
  content_type: '内容格式：\n• html：HTML 网页（默认）\n• xml：XML 格式（RSS/Atom）\n• json：JSON API 接口\n• markdown：Markdown 文件（如 GitHub README）\n• text：纯文本\n\n💡 不设置时默认 html',
  extract_config: '两阶段抓取配置（JSON格式）：\n\n第一阶段【列表页】：\n• url：列表页URL\n• selector：文章容器选择器\n• attr：链接属性，默认 href\n• type：提取类型，attribute（默认，从属性提取）或 text（从文本提取）\n• max_items：最大抓取数量，默认3条\n• url_filters：URL过滤配置（可选）\n  - include：正则表达式，白名单匹配\n  - exclude：字符串数组，黑名单排除\n• item_fields：基本信息提取（标题、摘要、图片等）\n\n第二阶段【详情页】：\n• 访问每篇文章链接\n• 提取完整标题、内容、作者、发布时间等\n• 自动转Markdown保存\n\n【URL过滤配置示例】\n{\n  "url_filters": {\n    "include": "https://example\\.com/article/.*",\n    "exclude": ["/tag/", "/category/", "/sponsored/"]\n  }\n}',
  delay_min: '抓取请求之间的最小等待时间（秒）\n\n设置延迟防止请求过快被封，例如设为1表示每次请求后至少等待1秒',
  delay_max: '抓取请求之间的最大等待时间（秒）\n\n与min配合使用，随机等待min~max秒。例如1-3秒表示每次等待1-3秒',
  user_agent: '自定义User-Agent字符串\n\n不设置则使用浏览器默认UA。可用于伪装成特定浏览器或移动端',
  cron_expression: 'Cron定时表达式，定义自动抓取计划\n\n格式：分 时 日 月 周\n• 0 8 * * *：每天早上8点\n• */30 * * * *：每30分钟\n• 0 * * * *：每小时\n• 0 0 * * 0：每周日午夜',
  status: '规则状态：\n• disabled：禁用，不执行定时任务\n• enabled：启用，按cron_expression定时执行',
  proxy_config: '代理服务器配置（JSON格式）\n\n格式：{"server": "http://proxy:8080", "username": "user", "password": "pass"}\n用于需要代理访问的网站',
}

// 认证配置表单组件
interface AuthConfigFormProps {
  authType: string
  value?: any
  onChange?: (value: any) => void
}

const AuthConfigForm: React.FC<AuthConfigFormProps> = ({ authType, value, onChange }) => {
  const updateValue = (newValue: any) => {
    onChange?.(newValue)
  }

  if (authType === 'none') {
    return <Text type="secondary">无需认证配置</Text>
  }

  if (authType === 'basic') {
    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <Input
          placeholder="用户名"
          value={value?.username || ''}
          onChange={(e) => updateValue({ ...value, username: e.target.value })}
          style={{ width: 200 }}
        />
        <Input.Password
          placeholder="密码"
          value={value?.password || ''}
          onChange={(e) => updateValue({ ...value, password: e.target.value })}
          style={{ width: 200 }}
        />
      </Space>
    )
  }

  if (authType === 'bearer') {
    return (
      <Input
        placeholder="Token"
        value={value?.token || ''}
        onChange={(e) => updateValue({ token: e.target.value })}
        style={{ width: 300 }}
      />
    )
  }

  if (authType === 'custom') {
    const headersObj: Record<string, string> = value?.headers || {}

    const updateHeaderValue = (key: string, val: string) => {
      const newHeaders = { ...headersObj }
      if (val) {
        newHeaders[key] = val
      } else {
        delete newHeaders[key]
      }
      updateValue({ ...value, headers: newHeaders })
    }

    const addHeader = () => {
      const newKey = `header_${Date.now()}`
      updateValue({
        ...value,
        headers: { ...headersObj, [newKey]: '' }
      })
    }

    const removeHeader = (key: string) => {
      const newHeaders = { ...headersObj }
      delete newHeaders[key]
      updateValue({ ...value, headers: newHeaders })
    }

    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {Object.entries(headersObj).map(([key, val]) => (
          <Space key={key}>
            <Input
              placeholder="Key"
              value={key}
              onChange={(e) => {
                const newHeaders: Record<string, string> = {}
                Object.entries(headersObj).forEach(([k, v]) => {
                  newHeaders[k === key ? e.target.value : k] = v
                })
                updateValue({ ...value, headers: newHeaders })
              }}
              style={{ width: 180 }}
            />
            <Input
              placeholder="Value"
              value={val}
              onChange={(e) => updateHeaderValue(key, e.target.value)}
              style={{ width: 250 }}
            />
            <Button type="text" danger onClick={() => removeHeader(key)}>删除</Button>
          </Space>
        ))}
        <Button type="dashed" onClick={addHeader}>+ 添加请求头</Button>
      </Space>
    )
  }

  return null
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
    selector: '.article-item',
    attr: 'href',
    type: 'attribute',
    max_items: 3,
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
  list: {
    url: '',
    max_items: 10
  },
  mapping: {
    title: 'title',
    link: 'link',
    content: 'content:encoded',
    description: 'description',
    author: 'author',
    date: 'pubDate'
  }
}

// 默认的 API 配置模板（合并到 extract_config）
const DEFAULT_API_CONFIG = {
  list: {
    url: '',
    max_items: 10
  },
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
  const [render, setRender] = useState<string>('browser')
  const [contentType, setContentType] = useState<string>('html')
  const [authType, setAuthType] = useState<string>('none')
  const [authConfigValue, setAuthConfigValue] = useState<any>(null)
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
      setAuthType(rule.auth_type || 'none')
      // 从 extract_config 中提取 source_url 和 max_items
      if (rule.extract_config) {
        try {
          const config = typeof rule.extract_config === 'string'
            ? JSON.parse(rule.extract_config)
            : rule.extract_config
          if (config?.list) {
            if (config.list.url) {
              form.setFieldValue('source_url', config.list.url)
            }
            if (config.list.max_items !== undefined) {
              form.setFieldValue('max_items', config.list.max_items)
            }
          }
        } catch {
        }
      }
      // 初始化认证配置
      if (rule.auth_config) {
        try {
          const config = typeof rule.auth_config === 'string'
            ? JSON.parse(rule.auth_config)
            : rule.auth_config
          if (rule.auth_type === 'custom' && config?.headers && typeof config.headers === 'object') {
            const headersArray = Object.entries(config.headers).map(([key, value]) => ({ key, value: value as string }))
            setAuthConfigValue({ ...config, headers: headersArray })
          } else {
            setAuthConfigValue(config)
          }
        } catch {
          setAuthConfigValue(null)
        }
      } else {
        setAuthConfigValue(null)
      }
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

      // 将 source_url 和 max_items 合并到 extract_config
      if (values.extract_config) {
        try {
          const config = typeof values.extract_config === 'string'
            ? JSON.parse(values.extract_config)
            : values.extract_config
          if (!config.list) {
            config.list = {}
          }
          if (values.source_url) {
            config.list.url = values.source_url
          }
          if (values.max_items !== undefined) {
            config.list.max_items = values.max_items
          }
          values.extract_config = JSON.stringify(config)
        } catch {
        }
      } else if (values.source_url || values.max_items !== undefined) {
        const config: any = { list: {} }
        if (values.source_url) {
          config.list.url = values.source_url
        }
        if (values.max_items !== undefined) {
          config.list.max_items = values.max_items
        }
        values.extract_config = JSON.stringify(config)
      }

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
    if (value === 'http') {
      setContentType('html')
      form.setFieldValue('content_type', 'html')
    } else {
      setContentType('html')
      form.setFieldValue('content_type', 'html')
    }
  }

  const handleContentTypeChange = (value: string) => {
    setContentType(value)
    form.setFieldValue('content_type', value)
    if (value === 'xml' || value === 'json' || value === 'markdown' || value === 'text') {
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
        name="max_items"
        label="最大抓取数量"
        tooltip={FIELD_TIPS.max_items}
      >
        <InputNumber min={1} max={100} defaultValue={3} />
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
    </>
  )

  // 渲染 XML/RSS 配置
  const renderXmlFields = () => (
    <>
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
      <Button type="link" onClick={() => fillDefaultConfig('json')}>
        填充默认配置
      </Button>
    </>
  )

  // 渲染 Markdown 配置
  const renderMarkdownFields = () => (
    <>
      <Form.Item
        name="extract_config"
        label="抓取配置"
        tooltip="包含 list.url 等配置"
      >
        <TextArea
          rows={4}
          placeholder='{"list": {"url": "https://raw.githubusercontent.com/.../README.md"}}'
          style={{ fontFamily: 'monospace' }}
        />
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
            options={render === 'http' ? CONTENT_TYPE_OPTIONS : [{ label: 'HTML', value: 'html' }]}
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
          name="auth_type"
          label="认证类型"
        >
          <Select
            onChange={(value) => setAuthType(value)}
            options={[
              { label: '无认证', value: 'none' },
              { label: 'Basic认证', value: 'basic' },
              { label: 'Bearer Token', value: 'bearer' },
              { label: '自定义', value: 'custom' },
            ]}
          />
        </Form.Item>

        <Form.Item label="认证配置">
          <AuthConfigForm
            authType={authType}
            value={authConfigValue}
            onChange={(val) => {
              setAuthConfigValue(val)
              form.setFieldValue('auth_config', val ? JSON.stringify(val) : undefined)
            }}
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
