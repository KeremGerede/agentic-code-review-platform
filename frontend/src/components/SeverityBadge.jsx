const SEVERITY_STYLES = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high:     'bg-orange-100 text-orange-800 border-orange-200',
  warning:  'bg-yellow-100 text-yellow-800 border-yellow-200',
  info:     'bg-gray-100 text-gray-700 border-gray-200',
  // risk level aliases
  medium:   'bg-yellow-100 text-yellow-800 border-yellow-200',
  low:      'bg-green-100 text-green-800 border-green-200',
  // status aliases
  sent:     'bg-green-100 text-green-800 border-green-200',
  failed:   'bg-red-100 text-red-800 border-red-200',
  pending:  'bg-gray-100 text-gray-600 border-gray-200',
  running:  'bg-blue-100 text-blue-800 border-blue-200',
  completed:'bg-green-100 text-green-800 border-green-200',
}

export default function SeverityBadge({ value, label }) {
  const key = (value || '').toLowerCase()
  const style = SEVERITY_STYLES[key] || 'bg-gray-100 text-gray-600 border-gray-200'
  return (
    <span className={`inline-block border rounded-full px-2.5 py-0.5 text-xs font-semibold ${style}`}>
      {label || value || '—'}
    </span>
  )
}
