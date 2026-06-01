import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Repositories from './pages/Repositories'
import Rules from './pages/Rules'
import AnalysisReports from './pages/AnalysisReports'
import AnalysisDetail from './pages/AnalysisDetail'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/repositories" element={<Repositories />} />
            <Route path="/rules" element={<Rules />} />
            <Route path="/analysis" element={<AnalysisReports />} />
            <Route path="/analysis/:id" element={<AnalysisDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
