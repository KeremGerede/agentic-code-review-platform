import { useEffect, useState } from 'react'
import { getRules, createRule, updateRule, deleteRule, toggleRule, getRepositories } from '../api/client'
import SeverityBadge from '../components/SeverityBadge'

const CATEGORIES = ['security', 'code_quality', 'architecture', 'testing', 'performance', 'maintainability', 'style', 'other']
const SEVERITIES = ['info', 'warning', 'high', 'critical']

const EMPTY_FORM = {
  title: '', description: '', category: 'other',
  severity: 'warning', is_enabled: true, repository_id: '',
}

export default function Rules() {
  const [rules, setRules] = useState([])
  const [repos, setRepos] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  const load = () =>
    Promise.all([getRules(), getRepositories()]).then(([r, repos]) => {
      setRules(r.data)
      setRepos(repos.data)
    })

  useEffect(() => { load() }, [])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const openCreate = () => {
    setForm(EMPTY_FORM)
    setEditingId(null)
    setShowForm(true)
    setError('')
  }

  const openEdit = (rule) => {
    setForm({
      title: rule.title,
      description: rule.description,
      category: rule.category,
      severity: rule.severity,
      is_enabled: rule.is_enabled,
      repository_id: rule.repository_id ?? '',
    })
    setEditingId(rule.id)
    setShowForm(true)
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    const payload = {
      ...form,
      repository_id: form.repository_id === '' ? null : Number(form.repository_id),
    }
    try {
      if (editingId) {
        await updateRule(editingId, payload)
      } else {
        await createRule(payload)
      }
      setShowForm(false)
      setEditingId(null)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save rule.')
    }
  }

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete rule "${title}"?`)) return
    await deleteRule(id)
    load()
  }

  const handleToggle = async (id) => {
    await toggleRule(id)
    load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Rules</h1>
        <button
          onClick={openCreate}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          + Add Rule
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-gray-200 rounded-xl p-5 mb-6 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <div className="col-span-2 font-semibold text-gray-700">
            {editingId ? 'Edit Rule' : 'New Rule'}
          </div>
          {error && (
            <div className="col-span-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
              {error}
            </div>
          )}
          <div className="col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
            <input
              name="title" value={form.title} onChange={handleChange} required
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div className="col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">Description *</label>
            <textarea
              name="description" value={form.description} onChange={handleChange} required rows={3}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
            <select
              name="category" value={form.category} onChange={handleChange}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
            <select
              name="severity" value={form.severity} onChange={handleChange}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Repository (optional — blank = global)</label>
            <select
              name="repository_id" value={form.repository_id} onChange={handleChange}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="">Global (all repositories)</option>
              {repos.map((r) => <option key={r.id} value={r.id}>{r.full_name}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2 self-end pb-1">
            <input
              type="checkbox" name="is_enabled" checked={form.is_enabled}
              onChange={handleChange} id="is_enabled"
              className="w-4 h-4 accent-indigo-600"
            />
            <label htmlFor="is_enabled" className="text-sm text-gray-700">Enabled</label>
          </div>
          <div className="col-span-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => { setShowForm(false); setEditingId(null) }}
              className="border border-gray-300 text-gray-600 px-4 py-2 rounded-lg text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm font-medium"
            >
              {editingId ? 'Update Rule' : 'Create Rule'}
            </button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {rules.length === 0 ? (
          <div className="px-5 py-8 text-gray-400 text-sm text-center">No rules yet. Add a rule above.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs uppercase">
                <th className="px-4 py-2 text-left">Title</th>
                <th className="px-4 py-2 text-left">Category</th>
                <th className="px-4 py-2 text-left">Severity</th>
                <th className="px-4 py-2 text-left">Scope</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => {
                const repoName = repos.find((r) => r.id === rule.repository_id)?.full_name
                return (
                  <tr key={rule.id} className={`border-t border-gray-100 ${rule.is_enabled ? '' : 'opacity-50'} hover:bg-gray-50`}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-800">{rule.title}</div>
                      <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">{rule.description}</div>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{rule.category}</td>
                    <td className="px-4 py-3"><SeverityBadge value={rule.severity} /></td>
                    <td className="px-4 py-3 text-xs">
                      {repoName ? (
                        <span className="bg-indigo-50 text-indigo-700 border border-indigo-200 rounded px-1.5 py-0.5">{repoName}</span>
                      ) : (
                        <span className="text-gray-400 italic">global</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <SeverityBadge value={rule.is_enabled ? 'completed' : 'failed'} label={rule.is_enabled ? 'Enabled' : 'Disabled'} />
                    </td>
                    <td className="px-4 py-3 text-right flex justify-end gap-2 flex-wrap">
                      <button
                        onClick={() => handleToggle(rule.id)}
                        className="text-xs text-indigo-600 hover:underline"
                      >
                        {rule.is_enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        onClick={() => openEdit(rule)}
                        className="text-xs text-gray-600 hover:underline"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(rule.id, rule.title)}
                        className="text-xs text-red-500 hover:underline"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
