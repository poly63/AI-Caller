import React, { useState, useEffect } from 'react';
import { Phone, TrendingUp, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const API_URL = 'http://localhost:8000/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentCalls, setRecentCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, callsRes] = await Promise.all([
        fetch(`${API_URL}/analytics/dashboard`),
        fetch(`${API_URL}/calls/?limit=10`)
      ]);
      
      const statsData = await statsRes.json();
      const callsData = await callsRes.json();
      
      setStats(statsData);
      setRecentCalls(callsData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  const sentimentColors = {
    positive: '#10b981',
    neutral: '#3b82f6',
    negative: '#f59e0b',
    angry: '#ef4444'
  };

  const sentimentData = {
    labels: Object.keys(stats?.sentiment_distribution || {}),
    datasets: [{
      data: Object.values(stats?.sentiment_distribution || {}),
      backgroundColor: Object.keys(stats?.sentiment_distribution || {}).map(
        key => sentimentColors[key] || '#6b7280'
      )
    }]
  };

  const getRiskBadge = (risk) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800'
    };
    return colors[risk] || 'bg-gray-100 text-gray-800';
  };

  const getSentimentBadge = (sentiment) => {
    const colors = {
      positive: 'bg-green-100 text-green-800',
      neutral: 'bg-blue-100 text-blue-800',
      negative: 'bg-orange-100 text-orange-800',
      angry: 'bg-red-100 text-red-800'
    };
    return colors[sentiment] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">SmartCall AI Dashboard</h1>
          <p className="text-gray-600 mt-2">Real-time call intelligence and analytics</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Calls"
            value={stats?.total_calls || 0}
            icon={Phone}
            color="blue"
          />
          <StatCard
            title="Active Calls"
            value={stats?.active_calls || 0}
            icon={Users}
            color="green"
          />
          <StatCard
            title="Avg Score"
            value={`${stats?.average_score || 0}/100`}
            icon={TrendingUp}
            color="purple"
          />
          <StatCard
            title="Calls Today"
            value={stats?.calls_today || 0}
            icon={CheckCircle}
            color="indigo"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Sentiment Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Sentiment Distribution</h2>
            <div className="h-64 flex items-center justify-center">
              <Doughnut data={sentimentData} options={{ maintainAspectRatio: false }} />
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Quick Stats</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b">
                <span className="text-gray-600">Average Sentiment Score</span>
                <span className="font-semibold">{(stats?.average_sentiment || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b">
                <span className="text-gray-600">Total Calls</span>
                <span className="font-semibold">{stats?.total_calls || 0}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b">
                <span className="text-gray-600">Calls Today</span>
                <span className="font-semibold">{stats?.calls_today || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Active Now</span>
                <span className="font-semibold text-green-600">{stats?.active_calls || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Calls */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold">Recent Calls</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Agent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sentiment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentCalls.map((call) => (
                  <tr key={call.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {call.agent_name || call.agent_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{call.customer_number}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {call.duration ? `${Math.floor(call.duration / 60)}m ${call.duration % 60}s` : '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold">
                        {call.score ? `${call.score}/100` : '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {call.sentiment && (
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSentimentBadge(call.sentiment)}`}>
                          {call.sentiment}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {call.risk_level && (
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskBadge(call.risk_level)}`}>
                          {call.risk_level}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        call.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {call.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    indigo: 'bg-indigo-500'
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`${colorClasses[color]} p-3 rounded-lg`}>
          <Icon className="text-white" size={24} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
