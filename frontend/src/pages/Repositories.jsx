import { useEffect, useState } from 'react'
import { getRepositories, deleteRepository } from '../api/client'

export default function Repositories() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    getRepositories()
      .then((r) => setRepos(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const handleDelete = async (id, fullName) => {
    if (!confirm(`Delete repository "${fullName}"? This will also delete all analysis runs.`)) return
    await deleteRepository(id)
    load()
  }

  if (loading) {
    return <div className="text-gray-500 py-12 text-center">Loading...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
          <p className="text-sm text-gray-500 mt-1">
            Repositories are detected automatically when a GitHub push webhook is received.
          </p>
        </div>

        <button
          onClick={load}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {repos.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <p className="text-gray-500 text-sm font-medium">No repositories detected yet.</p>
            <p className="text-gray-400 text-sm mt-2">
              Push a commit to a GitHub repository that has the webhook configured.
              After the webhook reaches the backend, the repository will appear here automatically.
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs uppercase">
                <th className="px-4 py-2 text-left">Full Name</th>
                <th className="px-4 py-2 text-left">Owner</th>
                <th className="px-4 py-2 text-left">Repo</th>
                <th className="px-4 py-2 text-left">Default Branch</th>
                <th className="px-4 py-2 text-left">Notification Emails</th>
                <th className="px-4 py-2 text-left">Active</th>
                <th className="px-4 py-2 text-left">Detected At</th>
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

                  <td className="px-4 py-2 text-gray-600">{repo.owner}</td>
                  <td className="px-4 py-2 text-gray-600">{repo.repo_name}</td>
                  <td className="px-4 py-2 font-mono text-xs">{repo.default_branch}</td>

                  <td className="px-4 py-2 text-xs text-gray-500">
                    {repo.notification_emails || (
                      <span className="italic text-gray-300">global .env recipients</span>
                    )}
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