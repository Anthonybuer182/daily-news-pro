import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, List, Tag, Spin } from 'antd'
import { getRules, getJobs, getArticles } from '../../api'
import dayjs from 'dayjs'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    rulesCount: 0,
    articlesCount: 0,
    jobsCount: 0,
    successRate: 0,
  })
  const [recentJobs, setRecentJobs] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [rulesRes, jobsRes] = await Promise.all([
        getRules(),
        getJobs({ limit: 5 }),
      ])
      await getArticles({ limit: 1 })

      const rules = rulesRes.data
      const jobs = jobsRes.data

      const successJobs = jobs.filter((j: any) => j.status === 'success').length
      const successRate = jobs.length > 0 ? Math.round((successJobs / jobs.length) * 100) : 0

      setStats({
        rulesCount: rules.length,
        articlesCount: rules.reduce((acc: number, r: any) => acc + (r.articles?.length || 0), 0),
        jobsCount: jobs.length,
        successRate,
      })
      setRecentJobs(jobs)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      failed: 'red',
      running: 'blue',
      pending: 'orange',
    }
    return colors[status] || 'default'
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />
  }

  return (
    <div>
      <h1>仪表盘</h1>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic title="规则总数" value={stats.rulesCount} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="文章总数" value={stats.articlesCount} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="任务总数" value={stats.jobsCount} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="成功率" value={stats.successRate} suffix="%" />
          </Card>
        </Col>
      </Row>

      <Card title="最近任务" style={{ marginTop: 16 }}>
        <List
          dataSource={recentJobs}
          renderItem={(item: any) => (
            <List.Item>
              <List.Item.Meta
                title={`任务 #${item.id}`}
                description={dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}
              />
              <Tag color={getStatusColor(item.status)}>{item.status}</Tag>
              <span style={{ marginLeft: 16 }}>
                成功: {item.success_count} / 失败: {item.failed_count}
              </span>
            </List.Item>
          )}
        />
      </Card>
    </div>
  )
}
