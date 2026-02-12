import React, { useState, useEffect } from 'react';
import { TrendingUp, Users, Award, AlertCircle } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { analyticsAPI } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

const Analytics = () => {
  const [sentimentTrends, setSentimentTrends] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [qualityMetrics, setQualityMetrics] = useState(null);
  const [riskAlerts, setRiskAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [trends, leaders, quality, alerts] = await Promise.all([
        analyticsAPI.getSentimentTrends(7),
        analyticsAPI.getLeaderboard(10),
        analyticsAPI.getQualityMetrics(),
        analyticsAPI.getRiskAlerts(10),
      ]);

      setSentimentTrends(trends);
      setLeaderboard(leaders);
      setQualityMetrics(quality);
      setRiskAlerts(alerts);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const sentimentChartData = {
    labels: sentimentTrends.map((d) => new Date(d.date).toLocaleDateString()),
    datasets: [
      {
        label: 'Positive',
        data: sentimentTrends.map((d) => d.positive),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
      },
      {
        label: 'Neutral',
        data: sentimentTrends.map((d) => d.neutral),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
      },
      {
        label: 'Negative',
        data: sentimentTrends.map((d) => d.negative),
        borderColor: 'rgb(251, 146, 60)',
        backgroundColor: 'rgba(251, 146, 60, 0.1)',
      },
      {
        label: 'Angry',
        data: sentimentTrends.map((d) => d.angry),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
      },
    ],
  };

  const qualityChartData = qualityMetrics
    ? {
        labels: Object.keys(qualityMetrics.average_scores || {}),
        datasets: [
          {
            label: 'Average Score',
            data: Object.values(qualityMetrics.average_scores || {}),
            backgroundColor: [
              'rgba(59, 130, 246, 0.8)',
              'rgba(34, 197, 94, 0.8)',
              'rgba(251, 146, 60, 0.8)',
              'rgba(168, 85, 247, 0.8)',
              'rgba(236, 72, 153, 0.8)',
            ],
          },
        ],
      }
    : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Analytics & Insights</h1>

        {/* Sentiment Trends */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp size={20} />
            Sentiment Trends (Last 7 Days)
          </h2>
          <div className="h-80">
            <Line
              data={sentimentChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Quality Metrics */}
          {qualityMetrics && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Quality Metrics</h2>
              <div className="h-80">
                {qualityChartData && (
                  <Bar
                    data={qualityChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 30,
                        },
                      },
                    }}
                  />
                )}
              </div>
              <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {qualityMetrics.risk_distribution?.low || 0}
                  </div>
                  <div className="text-sm text-gray-600">Low Risk</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {qualityMetrics.risk_distribution?.medium || 0}
                  </div>
                  <div className="text-sm text-gray-600">Medium Risk</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {qualityMetrics.risk_distribution?.high || 0}
                  </div>
                  <div className="text-sm text-gray-600">High Risk</div>
                </div>
              </div>
            </div>
          )}

          {/* Agent Leaderboard */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Award size={20} />
              Top Performers
            </h2>
            <div className="space-y-3">
              {leaderboard.map((agent, index) => (
                <div
                  key={agent.agent_id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                        index === 0
                          ? 'bg-yellow-500'
                          : index === 1
                          ? 'bg-gray-400'
                          : index === 2
                          ? 'bg-orange-600'
                          : 'bg-blue-500'
                      }`}
                    >
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-semibold">{agent.agent_name}</div>
                      <div className="text-sm text-gray-600">{agent.total_calls} calls</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600">{agent.average_score}</div>
                    <div className="text-xs text-gray-500">avg score</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk Alerts */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertCircle size={20} className="text-red-500" />
            Recent Risk Alerts
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Time
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Agent
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Customer
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Sentiment
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Score
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Summary
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {riskAlerts.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                      No risk alerts - Great job! 🎉
                    </td>
                  </tr>
                ) : (
                  riskAlerts.map((alert) => (
                    <tr key={alert.call_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">
                        {new Date(alert.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium">{alert.agent_name}</td>
                      <td className="px-4 py-3 text-sm">{alert.customer_number}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            alert.sentiment === 'angry'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-orange-100 text-orange-800'
                          }`}
                        >
                          {alert.sentiment}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-red-600">
                        {alert.score}/100
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                        {alert.summary || 'N/A'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
