import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Rules
export const getRules = (params?: any) => api.get('/rules', { params })
export const getRule = (id: number) => api.get(`/rules/${id}`)
export const createRule = (data: any) => api.post('/rules', data)
export const updateRule = (id: number, data: any) => api.put(`/rules/${id}`, data)
export const deleteRule = (id: number) => api.delete(`/rules/${id}`)
export const batchDeleteRules = (ids: number[]) => api.post('/rules/batch-delete', { ids })
export const enableRule = (id: number) => api.post(`/rules/${id}/enable`)
export const disableRule = (id: number) => api.post(`/rules/${id}/disable`)
export const runRule = (id: number) => api.post(`/rules/${id}/run`)
export const batchRunRules = (ids: number[]) => api.post('/rules/batch-run', ids)
export const getRuleLevels = (id: number) => api.get(`/rules/${id}/levels`)
export const createRuleLevel = (ruleId: number, data: any) => api.post(`/rules/${ruleId}/levels`, data)
export const updateRuleLevel = (ruleId: number, levelId: number, data: any) => api.put(`/rules/${ruleId}/levels/${levelId}`, data)
export const deleteRuleLevel = (ruleId: number, levelId: number) => api.delete(`/rules/${ruleId}/levels/${levelId}`)
export const analyzePage = (url: string, type: string) => api.post('/rules/analyze', { url, analyze_type: type })

// Jobs
export const getJobs = (params?: any) => api.get('/jobs', { params })
export const getJob = (id: number) => api.get(`/jobs/${id}`)
export const createJob = (data: any) => api.post('/jobs', data)
export const batchDeleteJobs = (ids: number[]) => api.post('/jobs/batch-delete', { ids })
export const batchRunJobs = (ids: number[]) => api.post('/jobs/batch-run', ids)

// Articles - 扩展现有接口
export const getArticles = (params?: {
  skip?: number;
  limit?: number;
  rule_id?: number;
  status?: string;
  keyword?: string;
  start_date?: string;
  end_date?: string;
  source?: string;       // 来源名称
  time_range?: string;   // today, week, month
  tags?: string;         // 逗号分隔的标签列表
}) => api.get('/articles', { params });

export const getTags = () => api.get('/articles/tags');

export const getArticle = (id: number) => api.get(`/articles/${id}`)
export const getArticleMarkdown = (id: number) => api.get(`/articles/${id}/markdown`)
export const deleteArticle = (id: number) => api.delete(`/articles/${id}`)
export const batchDeleteArticles = (ids: number[]) => api.post('/articles/batch-delete', { ids })

// Preview
export const previewCrawl = (url: string, ruleId?: number) => api.post('/preview', { url, rule_id: ruleId })

// Health
export const healthCheck = () => api.get('/health')

// Channels
export const getChannels = () => api.get('/channels')
export const getChannel = (id: number) => api.get(`/channels/${id}`)
export const createChannel = (data: any) => api.post('/channels', data)
export const updateChannel = (id: number, data: any) => api.put(`/channels/${id}`, data)
export const deleteChannel = (id: number) => api.delete(`/channels/${id}`)
export const addChannelWebhook = (channelId: number, data: any) => api.post(`/channels/${channelId}/webhooks`, data)
export const deleteChannelWebhook = (channelId: number, webhookId: number) => api.delete(`/channels/${channelId}/webhooks/${webhookId}`)
export const testChannel = (channelId: number) => api.post(`/channels/${channelId}/test`)
export const sendNow = () => api.post('/channels/send-now')

// Logs
export const getLogs = (params?: {
  skip?: number;
  limit?: number;
  job_id?: number;
  level?: string;
  start_time?: string;
  end_time?: string;
}) => api.get('/logs', { params });

export default api
