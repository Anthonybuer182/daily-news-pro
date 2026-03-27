import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Form, Input, Button, message, Space, Select, Breadcrumb } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import '@uiw/react-md-editor/markdown-editor.css'
import '@uiw/react-md-editor/markdown.css'
import { getArticle, getArticleMarkdown, updateArticle, getTags } from '../../api'
import MDEditor from '@uiw/react-md-editor'

const { TextArea } = Input

export function Edit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()
  const [markdownContent, setMarkdownContent] = useState('')
  const [availableTags, setAvailableTags] = useState<string[]>([])

  useEffect(() => {
    if (!id) {
      message.error('文章ID无效')
      navigate('/articles')
      return
    }
    // Load article data and tags in parallel
    Promise.all([
      getArticle(Number(id)),
      getArticleMarkdown(Number(id)),
      getTags()
    ]).then(([articleRes, markdownRes, tagsRes]) => {
      const article = articleRes.data
      form.setFieldsValue({
        title: article.title,
        author: article.author,
        summary: article.summary,
        cover_image: article.cover_image,
        tags: article.tags || []
      })
      setMarkdownContent(markdownRes.data.content || '')
      const tagNames = (tagsRes.data || []).map((t: any) => t.name)
      setAvailableTags(tagNames)
    }).catch(() => {
      message.error('加载文章失败')
      navigate('/articles')
    })
  }, [id])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      await updateArticle(Number(id), {
        ...values,
        markdown_content: markdownContent
      })
      message.success('保存成功')
      navigate('/articles')
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单必填项')
      } else {
        message.error('保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { title: <a onClick={() => navigate('/articles')}>文章管理</a> },
          { title: '编辑文章' }
        ]}
        style={{ marginBottom: 16 }}
      />

      <Card>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            title: '',
            author: '',
            summary: '',
            cover_image: '',
            tags: []
          }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="文章标题" maxLength={500} />
          </Form.Item>

          <Form.Item name="author" label="作者">
            <Input placeholder="作者" maxLength={255} style={{ width: 200 }} />
          </Form.Item>

          <Form.Item name="cover_image" label="封面图片">
            <Input placeholder="封面图片 URL" style={{ width: 400 }} />
          </Form.Item>

          <Form.Item name="summary" label="摘要">
            <TextArea placeholder="文章摘要" rows={3} />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Select
              mode="multiple"
              placeholder="选择标签"
              style={{ width: 300 }}
              options={availableTags.map(t => ({ label: t, value: t }))}
            />
          </Form.Item>

          <Form.Item label="正文">
            <div data-color-mode="light">
              <MDEditor
                value={markdownContent}
                onChange={(value) => setMarkdownContent(value || '')}
                height={400}
                preview="edit"
              />
            </div>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/articles')}
              >
                取消
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={saving}
                onClick={handleSave}
              >
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Edit