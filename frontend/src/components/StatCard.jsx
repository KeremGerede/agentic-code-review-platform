export default function StatCard({ label, value, color = 'indigo' }) {
  const colorMap = {
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    gray: 'bg-gray-50 border-gray-200 text-gray-700',
  }

  return (
    <div className={`rounded-xl border p-5 ${colorMap[color] || colorMap.indigo}`}>
      <div className="text-3xl font-bold">{value ?? '—'}</div>
      <div className="mt-1 text-sm font-medium opacity-75">{label}</div>
    </div>
  )
}
