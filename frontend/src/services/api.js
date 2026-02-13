import axios from 'axios';

const configuredBase = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
const API_BASE_URL = configuredBase.endsWith('/api') ? configuredBase : `${configuredBase}/api`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth token (if needed)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Call APIs
export const callsAPI = {
  // Start a new call
  startCall: async (callData) => {
    const response = await api.post('/calls/start', callData);
    return response.data;
  },

  // Get call by ID
  getCall: async (callId) => {
    const response = await api.get(`/calls/${callId}`);
    return response.data;
  },

  // List calls with filters
  listCalls: async (params = {}) => {
    const response = await api.get('/calls/', { params });
    return response.data;
  },

  // Update call
  updateCall: async (callId, updateData) => {
    const response = await api.patch(`/calls/${callId}`, updateData);
    return response.data;
  },

  // End call
  endCall: async (callId) => {
    const response = await api.post(`/calls/${callId}/end`);
    return response.data;
  },

  // Analyze call
  analyzeCall: async (callId) => {
    const response = await api.post(`/calls/${callId}/analyze`);
    return response.data;
  },

  // Add message to call
  addMessage: async (callId, message) => {
    const response = await api.post(`/calls/${callId}/messages`, message);
    return response.data;
  },

  // Delete call
  deleteCall: async (callId) => {
    const response = await api.delete(`/calls/${callId}`);
    return response.data;
  },
};

// Analytics APIs
export const analyticsAPI = {
  // Get dashboard stats
  getDashboard: async () => {
    const response = await api.get('/analytics/dashboard');
    return response.data;
  },

  // Get agent performance
  getAgentPerformance: async (agentId) => {
    const response = await api.get(`/analytics/agent/${agentId}`);
    return response.data;
  },

  // Get agents leaderboard
  getLeaderboard: async (limit = 10) => {
    const response = await api.get('/analytics/agents/leaderboard', {
      params: { limit },
    });
    return response.data;
  },

  // Get sentiment trends
  getSentimentTrends: async (days = 7) => {
    const response = await api.get('/analytics/sentiment-trends', {
      params: { days },
    });
    return response.data;
  },

  // Get risk alerts
  getRiskAlerts: async (limit = 20) => {
    const response = await api.get('/analytics/risk-alerts', {
      params: { limit },
    });
    return response.data;
  },

  // Get call volume
  getCallVolume: async (period = 'daily', limit = 30) => {
    const response = await api.get('/analytics/call-volume', {
      params: { period, limit },
    });
    return response.data;
  },

  // Get quality metrics
  getQualityMetrics: async () => {
    const response = await api.get('/analytics/quality-metrics');
    return response.data;
  },
};

// WebSocket connection for real-time updates
export class CallWebSocket {
  constructor(callId) {
    this.callId = callId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(onMessage, onError, onClose) {
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws');
    this.ws = new WebSocket(`${wsUrl}/calls/ws/${this.callId}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      if (onClose) onClose();
      
      // Auto-reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => {
          this.connect(onMessage, onError, onClose);
        }, 2000 * this.reconnectAttempts);
      }
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  sendBinary(buffer) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(buffer);
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default api;
