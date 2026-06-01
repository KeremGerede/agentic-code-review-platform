import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Repositories ──────────────────────────────────────────────────────────────
export const getRepositories = () => client.get('/api/repositories')
export const createRepository = (data) => client.post('/api/repositories', data)
export const getRepository = (id) => client.get(`/api/repositories/${id}`)
export const deleteRepository = (id) => client.delete(`/api/repositories/${id}`)

// ── Rules ─────────────────────────────────────────────────────────────────────
export const getRules = (repositoryId) =>
  client.get('/api/rules', { params: repositoryId ? { repository_id: repositoryId } : {} })
export const createRule = (data) => client.post('/api/rules', data)
export const updateRule = (id, data) => client.put(`/api/rules/${id}`, data)
export const deleteRule = (id) => client.delete(`/api/rules/${id}`)
export const toggleRule = (id) => client.patch(`/api/rules/${id}/toggle`)

// ── Analysis ──────────────────────────────────────────────────────────────────
export const getAnalysisRuns = () => client.get('/api/analysis')
export const getAnalysisRun = (id) => client.get(`/api/analysis/${id}`)
export const getRepositoryAnalysis = (repositoryId) =>
  client.get(`/api/repositories/${repositoryId}/analysis`)

export default client
