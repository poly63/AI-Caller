import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Phone, User, Clock, TrendingUp, AlertTriangle } from 'lucide-react';
import { CallWebSocket, callsAPI } from '../services/api';

const CallDetails = () => {
  const { callId } = useParams();
  const navigate = useNavigate();
  const [call, setCall] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveInput, setLiveInput] = useState('');
  const [liveEvents, setLiveEvents] = useState([]);
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('en');
  const [speaker, setSpeaker] = useState('agent');
  const wsRef = useRef(null);

  useEffect(() => {
    fetchCallDetails();
  }, [callId]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);

  const fetchCallDetails = async () => {
    try {
      setLoading(true);
      const data = await callsAPI.getCall(callId);
      setCall(data);
    } catch (error) {
      console.error('Error fetching call details:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const connectLiveSocket = () => {
    if (wsRef.current?.isConnected()) return;
    const stream = new CallWebSocket(callId);
    wsRef.current = stream;
    stream.connect(
      (message) => {
        setWsConnected(true);
        if (message?.type === 'transcript' || message?.type === 'config_ack') {
          setLiveEvents((prev) => [message, ...prev].slice(0, 80));
        }
      },
      () => {
        setWsConnected(false);
      },
      () => {
        setWsConnected(false);
      }
    );
    setTimeout(() => {
      stream.send({ type: 'config', speaker, source_lang: sourceLang, target_lang: targetLang });
    }, 300);
  };

  const disconnectLiveSocket = () => {
    wsRef.current?.disconnect();
    setWsConnected(false);
  };

  const sendLiveChunk = () => {
    const text = liveInput.trim();
    if (!text || !wsRef.current?.isConnected()) return;
    wsRef.current.send({
      type: 'transcript',
      speaker,
      source_lang: sourceLang,
      target_lang: targetLang,
      text,
      timestamp: Date.now() / 1000,
    });
    setLiveInput('');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading call details...</div>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">Call not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft size={20} />
          Back to Dashboard
        </button>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Call Details</h1>
              <p className="text-gray-500 mt-1">ID: {call.id}</p>
            </div>
            {call.score && (
              <div className="text-center">
                <div className={`text-5xl font-bold ${getScoreColor(call.score)}`}>
                  {call.score}
                </div>
                <div className="text-sm text-gray-500 mt-1">Overall Score</div>
              </div>
            )}
          </div>

          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="flex items-start gap-3">
              <User className="text-blue-500 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-500">Agent</p>
                <p className="text-lg font-semibold">{call.agent_name || call.agent_id}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Phone className="text-green-500 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-500">Customer</p>
                <p className="text-lg font-semibold">{call.customer_number}</p>
                {call.customer_name && (
                  <p className="text-sm text-gray-600">{call.customer_name}</p>
                )}
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Clock className="text-purple-500 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-500">Duration</p>
                <p className="text-lg font-semibold">{formatDuration(call.duration)}</p>
                <p className="text-sm text-gray-600">
                  {new Date(call.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Sentiment & Risk */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4">Sentiment Analysis</h3>
              <div className="flex items-center justify-between">
                <span className="text-lg capitalize">{call.sentiment || 'N/A'}</span>
                <span className="text-2xl font-bold">
                  {call.sentiment_score ? call.sentiment_score.toFixed(2) : 'N/A'}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle size={18} />
                Risk Level
              </h3>
              <div className="flex items-center justify-between">
                <span
                  className={`text-lg capitalize px-3 py-1 rounded-full ${
                    call.risk_level === 'high'
                      ? 'bg-red-100 text-red-800'
                      : call.risk_level === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}
                >
                  {call.risk_level || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Score Breakdown */}
          {call.score && (
            <div className="bg-gray-50 rounded-lg p-6 mb-8">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <TrendingUp size={18} />
                Score Breakdown
              </h3>
              <div className="space-y-4">
                <ScoreBar label="Greeting Quality" score={call.greeting_quality} max={10} />
                <ScoreBar label="Compliance" score={call.compliance_score} max={20} />
                <ScoreBar label="Customer Satisfaction" score={call.customer_satisfaction} max={30} />
                <ScoreBar label="Call Clarity" score={call.call_clarity} max={20} />
                <ScoreBar label="Resolution" score={call.resolution_score} max={20} />
              </div>
            </div>
          )}

          {/* Summary */}
          {call.summary && (
            <div className="bg-blue-50 rounded-lg p-6 mb-8">
              <h3 className="font-semibold mb-2">AI Summary</h3>
              <p className="text-gray-700">{call.summary}</p>
              {call.detected_intent && (
                <div className="mt-4">
                  <span className="text-sm font-medium text-gray-600">Detected Intent: </span>
                  <span className="text-sm text-gray-900">{call.detected_intent}</span>
                </div>
              )}
            </div>
          )}

          {/* Transcript */}
          {call.transcript && (
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4">Transcript</h3>
              <div className="bg-white rounded p-4 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                  {call.transcript}
                </pre>
              </div>
            </div>
          )}

          {/* Live Translate */}
          <div className="bg-gray-50 rounded-lg p-6 mt-8">
            <h3 className="font-semibold mb-4">Live Translate Stream</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              <input
                className="border rounded px-3 py-2 text-sm"
                value={speaker}
                onChange={(e) => setSpeaker(e.target.value)}
                placeholder="speaker (agent/customer)"
              />
              <input
                className="border rounded px-3 py-2 text-sm"
                value={sourceLang}
                onChange={(e) => setSourceLang(e.target.value)}
                placeholder="source lang"
              />
              <input
                className="border rounded px-3 py-2 text-sm"
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                placeholder="target lang"
              />
            </div>
            <div className="flex gap-3 mb-3">
              <button
                onClick={connectLiveSocket}
                className="px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-60"
                disabled={wsConnected}
              >
                Connect
              </button>
              <button
                onClick={disconnectLiveSocket}
                className="px-4 py-2 rounded bg-gray-200 text-gray-800 text-sm disabled:opacity-60"
                disabled={!wsConnected}
              >
                Disconnect
              </button>
              <span className={`text-sm self-center ${wsConnected ? 'text-green-600' : 'text-gray-500'}`}>
                {wsConnected ? 'Live connected' : 'Disconnected'}
              </span>
            </div>
            <div className="flex gap-2 mb-4">
              <input
                className="flex-1 border rounded px-3 py-2 text-sm"
                placeholder="Type transcript chunk and send..."
                value={liveInput}
                onChange={(e) => setLiveInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') sendLiveChunk();
                }}
              />
              <button
                onClick={sendLiveChunk}
                className="px-4 py-2 rounded bg-emerald-600 text-white text-sm disabled:opacity-60"
                disabled={!wsConnected || !liveInput.trim()}
              >
                Send
              </button>
            </div>
            <div className="bg-white rounded border max-h-72 overflow-y-auto p-3 space-y-2">
              {liveEvents.length === 0 && <p className="text-sm text-gray-500">No live events yet.</p>}
              {liveEvents.map((item, idx) => (
                <div key={`${item.timestamp || 't'}-${idx}`} className="text-sm border-b pb-2">
                  <div className="font-medium text-gray-700">
                    {item.speaker || '-'} {item.type === 'transcript' ? 'said:' : item.type}
                  </div>
                  {item.text && <div className="text-gray-800">{item.text}</div>}
                  {item.translated_text && (
                    <div className="text-blue-700">Translated: {item.translated_text}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Flags */}
          {(call.escalation_required || call.contains_profanity) && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="font-semibold text-red-800 mb-2">⚠️ Alerts</h3>
              <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
                {call.escalation_required && <li>Escalation Required</li>}
                {call.contains_profanity && <li>Contains Profanity</li>}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ScoreBar = ({ label, score, max }) => {
  const percentage = (score / max) * 100;
  const color = percentage >= 80 ? 'bg-green-500' : percentage >= 60 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium">{label}</span>
        <span className="text-gray-600">
          {score}/{max}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
};

export default CallDetails;
