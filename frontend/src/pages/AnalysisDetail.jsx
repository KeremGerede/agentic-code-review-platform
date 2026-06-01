import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getAnalysisRun, getRepository } from '../api/client'
import SeverityBadge from '../components/SeverityBadge'
import FindingCard from '../components/FindingCard'

const SEVERITY_ORDER = ['critical', 'high', 'warning', 'info']

function groupBySeverity(findings) {
  return SEVERITY_ORDER.reduce((acc, sev) => {
    const group = findings.filter((f) => f.severity === sev)
    if (group.length > 0) acc[sev] = group
    return acc
  }, {})
}

export default function AnalysisDetail() {
  const { id } = useParams()
  const [run, setRun] = useState(null)
  const [repo, setRepo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAnalysisRun(id)
      .then((r) => {
        setRun(r.data)
        return getRepository(r.data.repository_id)
      })
      .then((r) => setRepo(r.data))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="text-gray-500 py-12 text-center">Loading...</div>
  if (!run) return <div className="text-red-500 py-12 text-center">Analysis run not found.</div>

  const grouped = groupBySeverity(run.findings || [])

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-2 mb-6">
        <Link to="/analysis" className="text-indigo-500 hover:underline text-sm">
          ← Analysis Reports
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-1">Analysis Report</h1>
      <p className="text-gray-500 text-sm mb-6">Run #{run.id}</p>

      {/* Meta card */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm mb-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Repository</div>
            <div className="font-medium">{repo?.full_name || `#${run.repository_id}`}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Branch</div>
            <div className="font-mono">{run.branch}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Commit</div>
            <div className="font-mono">{run.commit_sha?.slice(0, 7)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Author</div>
            <div>{run.author || '—'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Status</div>
            <SeverityBadge value={run.status} />
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Risk Level</div>
            {run.risk_level ? <SeverityBadge value={run.risk_level} /> : <span className="text-gray-400">—</span>}
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Files Analyzed</div>
            <div>{run.total_files_analyzed}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Total Findings</div>
            <div className="font-semibold">{run.total_findings}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Email Status</div>
            <SeverityBadge value={run.email_status} />
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Created At</div>
            <div>{new Date(run.created_at).toLocaleString()}</div>
          </div>
          {run.completed_at && (
            <div>
              <div className="text-xs text-gray-500 mb-0.5">Completed At</div>
              <div>{new Date(run.completed_at).toLocaleString()}</div>
            </div>
          )}
        </div>

        {run.email_error && (
          <div className="mt-4 text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
            Email error: {run.email_error}
          </div>
        )}

        {run.summary && (
          <div className="mt-4 bg-gray-50 rounded-lg p-3 text-sm text-gray-700">
            <div className="font-medium text-xs text-gray-500 mb-1 uppercase tracking-wide">Summary</div>
            {run.summary}
          </div>
        )}
      </div>

      {/* Findings */}
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Findings ({run.total_findings})
      </h2>

      {run.total_findings === 0 ? (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-xl p-5 text-sm">
          ✅ No rule violations were found in this push.
        </div>
      ) : (
        SEVERITY_ORDER.map((sev) => {
          const group = grouped[sev]
          if (!group) return null
          return (
            <div key={sev} className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <SeverityBadge value={sev} />
                <span className="text-sm text-gray-500">{group.length} finding{group.length > 1 ? 's' : ''}</span>
              </div>
              <div className="flex flex-col gap-3">
                {group.map((f) => (
                  <FindingCard key={f.id} finding={f} />
                ))}
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
