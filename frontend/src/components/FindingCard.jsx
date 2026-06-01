import SeverityBadge from './SeverityBadge'

export default function FindingCard({ finding }) {
  const {
    file_path, line_number, rule_title, category,
    severity, issue, explanation, suggestion, code_snippet,
  } = finding

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <SeverityBadge value={severity} />
        <span className="text-xs text-gray-500 font-mono">
          {file_path}{line_number ? `:${line_number}` : ''}
        </span>
        <span className="text-xs text-gray-400">•</span>
        <span className="text-xs text-gray-500 italic">{category}</span>
      </div>

      <div className="font-semibold text-gray-800 mb-1">{rule_title}</div>
      <div className="text-sm text-gray-700 mb-1">
        <span className="font-medium">Issue:</span> {issue}
      </div>
      <div className="text-sm text-gray-600 mb-1">
        <span className="font-medium">Explanation:</span> {explanation}
      </div>
      <div className="text-sm text-gray-600 mb-2">
        <span className="font-medium">Suggestion:</span> {suggestion}
      </div>

      {code_snippet && (
        <pre className="bg-gray-900 text-green-300 rounded p-3 text-xs overflow-x-auto whitespace-pre-wrap">
          {code_snippet}
        </pre>
      )}
    </div>
  )
}
