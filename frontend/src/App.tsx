import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Processes from './pages/Processes'
import ProcessDetail from './pages/ProcessDetail'
import Approvals from './pages/Approvals'
import Metrics from './pages/Metrics'
import NewProcess from './pages/NewProcess'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/processes" element={<Processes />} />
        <Route path="/processes/:id" element={<ProcessDetail />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/new" element={<NewProcess />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
