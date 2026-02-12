import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Home, BarChart3, Phone, Settings } from 'lucide-react';
import Dashboard from './Dashboard';
import Analytics from './pages/Analytics';
import CallDetails from './pages/CallDetails';
import CallList from './components/CallList';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-2">
                <Phone className="text-blue-600" size={32} />
                <span className="text-2xl font-bold text-gray-900">SmartCall AI</span>
              </div>
              
              <div className="flex gap-6">
                <NavLink to="/" icon={Home} label="Dashboard" />
                <NavLink to="/analytics" icon={BarChart3} label="Analytics" />
                <NavLink to="/calls" icon={Phone} label="Calls" />
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/calls" element={<CallListPage />} />
          <Route path="/calls/:callId" element={<CallDetails />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

const NavLink = ({ to, icon: Icon, label }) => {
  return (
    <Link
      to={to}
      className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
    >
      <Icon size={20} />
      <span className="font-medium">{label}</span>
    </Link>
  );
};

const CallListPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Call Management</h1>
        <CallList />
      </div>
    </div>
  );
};

export default App;
