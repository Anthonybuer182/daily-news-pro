import { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, InputNumber, Segmented, Button, Space, Typography, Checkbox, Switch, Divider, Tooltip } from 'antd'
import { QuestionCircleOutlined } from '@ant-design/icons'
import { createRule, updateRule, getRuleEffectiveTagSchema, getTags } from '../../api'

const { TextArea } = Input
const { Text } = Typography

interface RuleModalProps {
  visible: boolean
  rule: any
  onClose: () => void
  onSuccess: () => void
}

// 认证配置表单组件
interface AuthConfigFormProps {
  authType: string
  value?: any
  onChange?: (value: any) => void
}

const AuthConfigForm: React.FC<AuthConfigFormProps> = ({ authType, value, onChange }) => {
  const updateValue = (newValue: any) => onChange?.(newValue)

  if (authType === 'none') return <Text type="secondary">无需认证配置</Text>

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
    const addHeader = () => updateValue({ ...value, headers: { ...headersObj, [`header_${Date.now()}`]: '' } })
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
                Object.entries(headersObj).forEach(([k, v]) => { newHeaders[k === key ? e.target.value : k] = v })
                updateValue({ ...value, headers: newHeaders })
              }}
              style={{ width: 180 }}
            />
            <Input
              placeholder="Value"
              value={val}
              onChange={(e) => {
                updateValue({ ...value, headers: { ...headersObj, [key]: e.target.value } })
              }}
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

const CONTENT_TYPE_OPTIONS = [
  { label: 'HTML', value: 'html' },
  { label: 'XML (RSS)', value: 'xml' },
  { label: 'JSON API', value: 'json' },
  { label: 'Markdown', value: 'markdown' },
  { label: '纯文本', value: 'text' },
]

const RENDER_OPTIONS = [
  { label: '静态抓取（HTTP）', value: 'static' },
  { label: '动态抓取（Playwright）', value: 'dynamic' },
]

const TRANSLATION_LANGUAGE_OPTIONS = [
  { label: '中文', value: 'zh' }, { label: '英文', value: 'en' },
  { label: '日文', value: 'ja' }, { label: '韩文', value: 'ko' },
  { label: '法文', value: 'fr' }, { label: '德文', value: 'de' },
  { label: '西班牙文', value: 'es' }, { label: '俄文', value: 'ru' },
  { label: '阿拉伯文', value: 'ar' }, { label: '葡萄牙文', value: 'pt' },
  { label: '意大利文', value: 'it' }, { label: '越南文', value: 'vi' },
  { label: '泰文', value: 'th' }, { label: '印尼文', value: 'id' },
]

const TRANSLATION_FIELD_OPTIONS = [
  { label: '标题', value: 'title' },
  { label: '摘要', value: 'summary' },
  { label: '正文', value: 'content' },
]

// 从 extract_config 中剥离系统管理字段，返回用于展示在 textarea 的剩余提取配置
function extractDisplayConfig(extractConfig: any): string {
  if (!extractConfig || typeof extractConfig !== 'object') return ''
  const display: any = { ...extractConfig }
  if (display.list) {
    const { url: _u, fetch_mode: _fm, content_type: _ct, max_items: _m, request: _req, ...restList } = display.list
    if (Object.keys(restList).length > 0) {
      display.list = restList
    } else {
      delete display.list
    }
  }
  return Object.keys(display).length > 0 ? JSON.stringify(display, null, 2) : ''
}

// 从 list.request 中剥离 auth，返回用于展示在 request textarea 的剩余请求配置
function extractRequestDisplay(request: any): string {
  if (!request || typeof request !== 'object') return ''
  const { auth: _a, ...rest } = request
  return Object.keys(rest).length > 0 ? JSON.stringify(rest, null, 2) : ''
}

export default function RuleModal({ visible, rule, onClose, onSuccess }: RuleModalProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [render, setRender] = useState<string>('dynamic')
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
      // 解析 extract_config
      let extractConfig: any = {}
      if (rule.extract_config) {
        try { extractConfig = typeof rule.extract_config === 'string' ? JSON.parse(rule.extract_config) : rule.extract_config } catch { /* ignore */ }
      }
      const listConfig = extractConfig.list || {}
      const requestConfig = listConfig.request || {}
      const auth = requestConfig.auth

      // 填充系统管理字段
      form.setFieldsValue({
        ...rule,
        source_url: listConfig.url || '',
        max_items: listConfig.max_items ?? 10,
        request_config_raw: extractRequestDisplay(requestConfig),
        extract_config_display: extractDisplayConfig(extractConfig),
      })
      setRender(listConfig.fetch_mode || 'dynamic')
      setContentType(listConfig.content_type || 'html')

      // 认证
      if (auth?.type && auth.type !== 'none') {
        setAuthType(auth.type)
        setAuthConfigValue(auth)
      } else {
        setAuthType('none')
        setAuthConfigValue(null)
      }

      // 翻译配置
      if (rule.translation_config) {
        try {
          const tc = typeof rule.translation_config === 'string' ? JSON.parse(rule.translation_config) : rule.translation_config
          setTranslationFormData({
            target_lang: tc.target_lang || '',
            source_lang: tc.source_lang || '',
            fields: tc.fields || ['summary', 'content'],
            concurrency: tc.concurrency || 3,
            generate_tags: tc.generate_tags || false,
            tag_schema: tc.tag_schema || [],
            max_tags: tc.max_tags || 3,
          })
        } catch { /* ignore */ }
      } else {
        resetTranslation()
      }
      fetchEffectiveTagConfig()
    } else if (visible) {
      form.resetFields()
      setRender('dynamic')
      setContentType('html')
      setAuthType('none')
      setAuthConfigValue(null)
      resetTranslation()
      form.setFieldsValue({ delay_min: 1, delay_max: 3, status: 'disabled', max_items: 10 })
      fetchEffectiveTagConfig()
    }
  }, [visible, rule])

  const resetTranslation = () => setTranslationFormData({
    target_lang: 'zh', source_lang: '', fields: ['summary', 'content'],
    concurrency: 3, generate_tags: false, tag_schema: [], max_tags: 3,
  })

  const fetchEffectiveTagConfig = async () => {
    try {
      if (rule) {
        const res = await getRuleEffectiveTagSchema(rule.id)
        setEffectiveTagConfig(res.data)
      } else {
        const res = await getTags()
        const tagNames = (res.data || []).map((t: any) => t.name)
        setEffectiveTagConfig(prev => ({ ...prev, tag_schema: tagNames }))
      }
    } catch { /* ignore */ }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // 构建 extract_config：将系统管理字段合并进 list
      let extractConfig: any = {}
      try { extractConfig = JSON.parse(values.extract_config_display || '{}') } catch { /* ignore */ }

      extractConfig.list = extractConfig.list || {}
      extractConfig.list.url = values.source_url
      extractConfig.list.fetch_mode = render
      extractConfig.list.content_type = contentType
      extractConfig.list.max_items = values.max_items

      // 构建 request：raw 配置 + auth
      let reqConfig: any = {}
      try { reqConfig = JSON.parse(values.request_config_raw || '{}') } catch { /* ignore */ }
      if (authType !== 'none') {
        const auth: any = { type: authType }
        if (authType === 'bearer') auth.token = authConfigValue?.token || ''
        else if (authType === 'basic') { auth.username = authConfigValue?.username || ''; auth.password = authConfigValue?.password || '' }
        else if (authType === 'custom') auth.headers = authConfigValue?.headers || {}
        reqConfig.auth = auth
      } else {
        delete reqConfig.auth
      }
      if (Object.keys(reqConfig).length > 0) {
        extractConfig.list.request = reqConfig
      } else {
        delete extractConfig.list.request
      }

      values.extract_config = JSON.stringify(extractConfig)

      // 翻译配置
      if (translationFormData.target_lang) {
        values.translation_config = JSON.stringify({
          target_lang: translationFormData.target_lang,
          source_lang: translationFormData.source_lang,
          fields: translationFormData.fields,
          concurrency: translationFormData.concurrency,
          ...(translationFormData.generate_tags ? { generate_tags: true } : {}),
        })
      } else {
        values.translation_config = undefined
      }

      // 清理不需要提交的临时字段
      delete values.source_url
      delete values.max_items
      delete values.request_config_raw
      delete values.extract_config_display

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
    if (value === 'dynamic') {
      setContentType('html')
    }
  }

  const handleContentTypeChange = (value: string) => {
    setContentType(value)
  }

  const applyExtractTemplate = () => {
    let tpl: object

    if (render === 'dynamic') {
      tpl = {
        list: {
          selector: 'article a, .news-item a',
          wait_for: '.news-list, article',
          url_filters: { exclude: ['/tag/', '/category/', '/page/'] },
        },
        detail: {
          fetch_mode: 'dynamic',
          wait_for: 'article, .post-body',
          fields: {
            title: { selector: 'h1', type: 'text' },
            summary: { selector: '.summary, .description, meta[name="description"]', attr: 'content', type: 'text' },
            content: { selector: 'article, .post-body, .entry-content', type: 'html' },
            author: { selector: '.author, .byline', type: 'text' },
            published_at: { selector: 'time, .publish-date', attr: 'datetime', type: 'text' },
          },
        },
      }
    } else if (contentType === 'xml') {
      tpl = {
        list: {
          item_selector: 'item, entry',
          fields: {
            title: { selector: 'title', type: 'text' },
            summary: { selector: 'description, summary', type: 'text' },
            content: { selector: 'content, encoded', type: 'html' },
            link: { selector: 'link', type: 'text' },
            published_at: { selector: 'pubDate, published, updated', type: 'text' },
          },
        },
      }
    } else if (contentType === 'json') {
      tpl = {
        list: {
          json_path: '$.data.list[*]',
          url_field: 'url',
          fields: {
            title: { json_path: '$.title' },
            summary: { json_path: '$.summary' },
            content: { json_path: '$.content' },
            author: { json_path: '$.author.name' },
            published_at: { json_path: '$.created_at' },
          },
        },
      }
    } else if (contentType === 'markdown' || contentType === 'text') {
      tpl = {
        list: {
          selector: 'a[href]',
          url_filters: { exclude: ['/tag/', '/category/'] },
        },
        detail: {
          fields: {
            title: { selector: 'h1', type: 'text' },
            content: { selector: 'body', type: 'text' },
          },
        },
      }
    } else {
      // static + html
      tpl = {
        list: {
          selector: 'article a, .news-item a, h2 a',
          url_filters: { exclude: ['/tag/', '/category/', '/page/'] },
        },
        detail: {
          fields: {
            title: { selector: 'h1', type: 'text' },
            summary: { selector: '.summary, .description, meta[name="description"]', attr: 'content', type: 'text' },
            content: { selector: 'article, .post-body, .entry-content', type: 'html' },
            author: { selector: '.author, .byline', type: 'text' },
            published_at: { selector: 'time, .publish-date', attr: 'datetime', type: 'text' },
          },
        },
      }
    }

    const current = form.getFieldValue('extract_config_display')
    if (current && current.trim()) {
      if (!window.confirm('当前已有配置内容，确定要覆盖为模板吗？')) return
    }
    form.setFieldValue('extract_config_display', JSON.stringify(tpl, null, 2))
  }

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
        {/* ── 基本信息 ── */}
        <Form.Item name="name" label="规则名称" tooltip="为规则设置一个便于识别的名称" rules={[{ required: true, message: '请输入规则名称' }]}>
          <Input placeholder="给规则起个名字，如：科技新闻头条" />
        </Form.Item>

        <Form.Item name="source_url" label="来源 URL" tooltip="新闻列表页的网址，爬虫将从此页面抓取文章链接" rules={[{ required: true, message: '请输入来源 URL' }]}>
          <Input placeholder="https://example.com/news" />
        </Form.Item>

        {/* ── 抓取方式 ── */}
        <Form.Item label="抓取方式" required tooltip="静态抓取速度快，适合普通 HTML/RSS/JSON；动态抓取通过浏览器渲染，适合需要 JavaScript 才能加载内容的页面">
          <Segmented
            options={RENDER_OPTIONS}
            value={render}
            onChange={(value) => handleRenderChange(value as string)}
          />
        </Form.Item>

        <Form.Item label="内容格式" required tooltip="指定来源页面返回的数据格式，静态模式下支持 HTML/XML/JSON/Markdown 等多种格式，动态模式仅支持 HTML">
          <Segmented
            options={render === 'static' ? CONTENT_TYPE_OPTIONS : [{ label: 'HTML', value: 'html' }]}
            value={contentType}
            onChange={(value) => handleContentTypeChange(value as string)}
          />
        </Form.Item>

        <Form.Item name="max_items" label="最大抓取数量" tooltip="每次执行时最多抓取的文章条数，建议 10-50 条，过大可能导致抓取超时">
          <InputNumber min={1} max={500} />
        </Form.Item>

        {/* ── 提取配置（选择器、字段映射等） ── */}
        <Form.Item
          name="extract_config_display"
          label={
            <Space size={4}>
              <span>提取配置 (JSON)</span>
              <Button
                type="link"
                size="small"
                style={{ padding: 0, height: 'auto', fontSize: 12 }}
                onClick={applyExtractTemplate}
              >
                使用{render === 'dynamic' ? '动态' : contentType === 'xml' ? 'RSS/XML' : contentType === 'json' ? 'JSON API' : contentType === 'markdown' ? 'Markdown' : contentType === 'text' ? '纯文本' : '静态 HTML'}模板
              </Button>
            </Space>
          }
          tooltip="配置列表项选择器、详情页字段提取等。URL/抓取方式/内容格式/请求配置由上方表单管理，无需在此重复填写。"
        >
          <TextArea
            rows={10}
            style={{ fontFamily: 'monospace' }}
            placeholder={`{\n  "list": {\n    "selector": "article a",\n    "url_filters": {"exclude": ["/tag/"]}\n  },\n  "detail": {\n    "fields": {\n      "title": {"selector": "h1", "type": "text"},\n      "content": {"selector": "article", "type": "html"}\n    }\n  }\n}`}
          />
        </Form.Item>

        {/* ── HTTP 请求配置（仅 fetch_mode=static 时需要） ── */}
        {render === 'static' && (
          <>
            <Form.Item
              name="request_config_raw"
              label="请求配置 (JSON)"
              tooltip="HTTP 请求的方法、请求头、请求体、超时等。认证信息通过下方认证字段配置。"
            >
              <TextArea
                rows={5}
                style={{ fontFamily: 'monospace' }}
                placeholder={`{\n  "method": "POST",\n  "headers": {"Content-Type": "application/json"},\n  "body": {"type": "graphql", "query": "..."},\n  "timeout": 30\n}`}
              />
            </Form.Item>

            <Form.Item label="认证类型" tooltip="访问目标 URL 时所需的认证方式，无认证则留空">
              <Select
                value={authType}
                onChange={(value) => { setAuthType(value); setAuthConfigValue(null) }}
                options={[
                  { label: '无认证', value: 'none' },
                  { label: 'Basic认证', value: 'basic' },
                  { label: 'Bearer Token', value: 'bearer' },
                  { label: '自定义', value: 'custom' },
                ]}
              />
            </Form.Item>

            <Form.Item label="认证配置" tooltip="填写对应认证方式所需的账号密码或 Token 等凭据">
              <AuthConfigForm
                authType={authType}
                value={authConfigValue}
                onChange={(val) => setAuthConfigValue(val)}
              />
            </Form.Item>
          </>
        )}

        {/* ── 定时与调度 ── */}
        <Form.Item name="status" label="规则状态" tooltip="启用后规则将按定时表达式自动执行；禁用则暂停调度，可随时重新启用">
          <Select options={[{ label: '禁用', value: 'disabled' }, { label: '启用', value: 'enabled' }]} />
        </Form.Item>

        <Form.Item name="cron_expression" label="定时表达式" tooltip='Cron 格式调度表达式，例如 "0 8 * * *" 表示每天早上 8 点执行，留空则不自动调度'>
          <Input placeholder="0 8 * * *" />
        </Form.Item>

        {/* ── 网络配置 ── */}
        <Form.Item name="delay_min" label="最小延迟(秒)" tooltip="每条文章请求之间的最小等待时间（秒），用于控制抓取频率，防止触发目标网站的限流">
          <InputNumber min={0} />
        </Form.Item>

        <Form.Item name="delay_max" label="最大延迟(秒)" tooltip="每条文章请求之间的最大等待时间（秒），实际延迟将在最小值到最大值之间随机取值，模拟人类访问">
          <InputNumber min={0} />
        </Form.Item>

        <Form.Item name="user_agent" label="User-Agent" tooltip="请求时携带的浏览器标识字符串，留空则使用系统默认值，可自定义以绕过某些 UA 检测">
          <Input placeholder="不设置则使用浏览器默认UA" />
        </Form.Item>

        <Form.Item name="proxy_config" label="代理配置" tooltip='通过代理服务器发起请求，格式示例：{"server": "http://host:port"}，支持 HTTP/SOCKS 协议'>
          <TextArea
            rows={2}
            placeholder='{"server": "http://proxy:8080"}'
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>

        {/* ── 翻译配置 ── */}
        <Form.Item label="翻译" tooltip="对抓取的摘要、正文等内容进行翻译">
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
                  options={[{ label: '自动检测', value: '' }, ...TRANSLATION_LANGUAGE_OPTIONS]}
                  placeholder="源语言（留空自动检测）"
                  style={{ width: 200 }}
                  allowClear
                />
                <Checkbox.Group
                  value={translationFormData.fields}
                  onChange={(v) => setTranslationFormData(prev => ({ ...prev, fields: v as string[] }))}
                  options={TRANSLATION_FIELD_OPTIONS}
                />
                <Space>
                  <Space size={4}>
                    <span>并发数</span>
                    <Tooltip title="同时翻译的文章数量，数值越大速度越快，但可能超过 AI 接口的速率限制导致报错">
                      <QuestionCircleOutlined style={{ color: '#00000073', fontSize: 14, cursor: 'help' }} />
                    </Tooltip>
                  </Space>
                  <InputNumber
                    min={1} max={10}
                    value={translationFormData.concurrency}
                    onChange={(v) => setTranslationFormData(prev => ({ ...prev, concurrency: v || 3 }))}
                    style={{ width: 80 }}
                  />
                  <span style={{ color: '#999' }}>1-10，避免限流</span>
                </Space>

                <Divider style={{ margin: '8px 0' }} />

                <Space>
                  <Space size={4}>
                    <span>自动打标签</span>
                    <Tooltip title="翻译完成后由 AI 自动为文章打上分类标签，标签来自规则或全局标签库">
                      <QuestionCircleOutlined style={{ color: '#00000073', fontSize: 14, cursor: 'help' }} />
                    </Tooltip>
                  </Space>
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
              </>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}
