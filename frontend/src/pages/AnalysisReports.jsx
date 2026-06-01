import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAnalysisRuns, getRepositories } from '../api/client'
import SeverityBadge from '../components/SeverityBadge'

export default function AnalysisReports() {
  const [runs, setRuns] = useState([])
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getAnalysisRuns(), getRepositories()])
      .then(([r, repos]) => { setRuns(r.data); setRepos(repos.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-500 py-12 text-center">Loading...</div>

  const repoMap = Object.fromEntries(repos.map((r) => [r.id, r.full_name]))

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analysis Reports</h1>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {runs.length === 0 ? (
          <div className="px-5 py-8 text-gray-400 text-sm text-center">
            No analysis runs yet. Configure a GitHub webhook and push a commit.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs uppercase">
                <th className="px-4 py-2 text-left">Repository</th>
                <th className="px-4 py-2 text-left">Branch</th>
                <th className="px-4 py-2 text-left">Commit</th>
                <th className="px-4 py-2 text-left">Author</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Risk</th>
                <th className="px-4 py-2 text-left">Findings</th>
                <th className="px-4 py-2 text-left">Email</th>
                <th className="px-4 py-2 text-left">Date</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2 text-xs font-medium text-gray-700">
                    {repoMap[run.repository_id] || `#${run.repository_id}`}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{run.branch}</td>
                  <td className="px-4 py-2 font-mono text-xs">{run.commit_sha?.slice(0, 7)}</td>
                  <td className="px-4 py-2 text-xs">{run.author || '—'}</td>
                  <td className="px-4 py-2"><SeverityBadge value={run.status} /></td>
                  <td className="px-4 py-2">
                    {run.risk_level ? <SeverityBadge value={run.risk_level} /> : '—'}
                  </td>
                  <td className="px-4 py-2 text-center">{run.total_findings ?? '—'}</td>
                  <td className="px-4 py-2"><SeverityBadge value={run.email_status} /></td>
                  <td className="px-4 py-2 text-gray-400 text-xs">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Link
                      to={`/analysis/${run.id}`}
                      className="text-indigo-600 hover:underline text-xs font-medium"
                    >
                      View →
                    </Link>
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
