import { useEffect, useState } from 'react'
import { getRepositories, createRepository, deleteRepository } from '../api/client'

const EMPTY_FORM = {
  name: '', owner: '', repo_name: '', full_name: '',
  default_branch: 'main', github_url: '', notification_emails: '',
}

export default function Repositories() {
  const [repos, setRepos] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () =>
    getRepositories().then((r) => setRepos(r.data)).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => {
      const next = { ...prev, [name]: value }
      // Auto-fill full_name from owner + repo_name
      if (name === 'owner' || name === 'repo_name') {
        next.full_name = `${next.owner}/${next.repo_name}`
        if (!next.name) next.name = next.repo_name
      }
      return next
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createRepository(form)
      setForm(EMPTY_FORM)
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create repository.')
    }
  }

  const handleDelete = async (id, fullName) => {
    if (!confirm(`Delete repository "${fullName}"? This will also delete all analysis runs.`)) return
    await deleteRepository(id)
    load()
  }

  if (loading) return <div className="text-gray-500 py-12 text-center">Loading...</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          {showForm ? 'Cancel' : '+ Add Repository'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-gray-200 rounded-xl p-5 mb-6 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          {error && (
            <div className="col-span-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
              {error}
            </div>
          )}
          {[
            { name: 'owner', label: 'Owner (GitHub username / org)', required: true },
            { name: 'repo_name', label: 'Repository name', required: true },
            { name: 'name', label: 'Display name', required: true },
            { name: 'full_name', label: 'Full name (owner/repo)', required: true },
            { name: 'default_branch', label: 'Default branch', required: true },
            { name: 'github_url', label: 'GitHub URL', required: true },
          ].map(({ name, label, required }) => (
            <div key={name}>
              <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
              <input
                name={name}
                value={form[name]}
                onChange={handleChange}
                required={required}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          ))}
          <div className="col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Notification emails (comma-separated, optional — overrides global .env)
            </label>
            <input
              name="notification_emails"
              value={form.notification_emails}
              onChange={handleChange}
              placeholder="dev@example.com, manager@example.com"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div className="col-span-2 flex justify-end">
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm font-medium"
            >
              Save Repository
            </button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {repos.length === 0 ? (
          <div className="px-5 py-8 text-gray-400 text-sm text-center">No repositories yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs uppercase">
                <th className="px-4 py-2 text-left">Full Name</th>
                <th className="px-4 py-2 text-left">Branch</th>
                <th className="px-4 py-2 text-left">Notification Emails</th>
                <th className="px-4 py-2 text-left">Active</th>
                <th className="px-4 py-2 text-left">Added</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {repos.map((repo) => (
                <tr key={repo.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">
                    <a
                      href={repo.github_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:underline"
                    >
                      {repo.full_name}
                    </a>
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{repo.default_branch}</td>
                  <td className="px-4 py-2 text-xs text-gray-500">
                    {repo.notification_emails || <span className="italic text-gray-300">global</span>}
                  </td>
                  <td className="px-4 py-2">
                    <span className={repo.is_active ? 'text-green-600' : 'text-gray-400'}>
                      {repo.is_active ? '✓' : '✗'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-400">
                    {new Date(repo.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleDelete(repo.id, repo.full_name)}
                      className="text-red-500 hover:text-red-700 text-xs font-medium"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
