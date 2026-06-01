import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRepositories, getRules, getAnalysisRuns } from '../api/client'
import StatCard from '../components/StatCard'
import SeverityBadge from '../components/SeverityBadge'

export default function Dashboard() {
  const [repos, setRepos] = useState([])
  const [rules, setRules] = useState([])
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getRepositories(), getRules(), getAnalysisRuns()])
      .then(([r, ru, an]) => {
        setRepos(r.data)
        setRules(ru.data)
        setRuns(an.data)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-500 py-12 text-center">Loading dashboard...</div>

  // Finding counts by severity across all runs
  const severityCounts = { critical: 0, high: 0, warning: 0, info: 0 }
  runs.forEach((run) => {
    ;(run.findings || []).forEach((f) => {
      const k = f.severity?.toLowerCase()
      if (k in severityCounts) severityCounts[k]++
    })
  })

  const latest = runs.slice(0, 10)

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Repositories" value={repos.length} color="indigo" />
        <StatCard label="Rules" value={rules.length} color="green" />
        <StatCard label="Analysis Runs" value={runs.length} color="indigo" />
        <StatCard
          label="Total Findings"
          value={runs.reduce((s, r) => s + (r.total_findings || 0), 0)}
          color="yellow"
        />
      </div>

      {/* Severity breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Critical Findings" value={severityCounts.critical} color="red" />
        <StatCard label="High Findings" value={severityCounts.high} color="yellow" />
        <StatCard label="Warnings" value={severityCounts.warning} color="yellow" />
        <StatCard label="Info" value={severityCounts.info} color="gray" />
      </div>

      {/* Latest runs */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-4 border-b border-gray-100 font-semibold text-gray-700">
          Latest Analysis Runs
        </div>
        {latest.length === 0 ? (
          <div className="px-5 py-8 text-gray-400 text-sm text-center">
            No analysis runs yet. Push a commit to a connected repository.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs uppercase">
                <th className="px-4 py-2 text-left">Repository</th>
                <th className="px-4 py-2 text-left">Branch</th>
                <th className="px-4 py-2 text-left">Commit</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Risk</th>
                <th className="px-4 py-2 text-left">Findings</th>
                <th className="px-4 py-2 text-left">Date</th>
              </tr>
            </thead>
            <tbody>
              {latest.map((run) => (
                <tr key={run.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">
                    <Link to={`/analysis/${run.id}`} className="text-indigo-600 hover:underline">
                      #{run.repository_id}
                    </Link>
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{run.branch}</td>
                  <td className="px-4 py-2 font-mono text-xs">{run.commit_sha?.slice(0, 7)}</td>
                  <td className="px-4 py-2">
                    <SeverityBadge value={run.status} />
                  </td>
                  <td className="px-4 py-2">
                    {run.risk_level ? <SeverityBadge value={run.risk_level} /> : '—'}
                  </td>
                  <td className="px-4 py-2">{run.total_findings ?? '—'}</td>
                  <td className="px-4 py-2 text-gray-400">
                    {new Date(run.created_at).toLocaleDateString()}
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
