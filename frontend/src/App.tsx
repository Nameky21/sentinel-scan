import { Route, Routes } from 'react-router-dom'

import { NavBar } from './components/NavBar'
import { HistoryPage } from './pages/HistoryPage'
import { NewScanPage } from './pages/NewScanPage'
import { ScanDetailPage } from './pages/ScanDetailPage'

export default function App() {
  return (
    <div className="min-h-full">
      <NavBar />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <Routes>
          <Route path="/" element={<NewScanPage />} />
          <Route path="/scans/:scanId" element={<ScanDetailPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
    </div>
  )
}
