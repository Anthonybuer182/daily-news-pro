import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Rules
export const getRules = () => api.get('/rules')
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

// Articles
export const getArticles = (params?: any) => api.get('/articles', { params })
export const getArticle = (id: number) => api.get(`/articles/${id}`)
export const getArticleMarkdown = (id: number) => api.get(`/articles/${id}/markdown`)
export const deleteArticle = (id: number) => api.delete(`/articles/${id}`)
export const batchDeleteArticles = (ids: number[]) => api.post('/articles/batch-delete', { ids })

// Preview
export const previewCrawl = (url: string, ruleId?: number) => api.post('/preview', { url, rule_id: ruleId })

// Health
export const healthCheck = () => api.get('/health')

export default api
