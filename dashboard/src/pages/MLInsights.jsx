import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Brain, Target, Zap, TrendingUp, Activity, Users, Clock, AlertCircle } from 'lucide-react'

function MLInsights() {
  const [mlStats, setMlStats] = useState({
    total_scored: 0,
    model_accuracy: 0,
    avg_score: 0,
    hot_leads_predicted: 0
  })
  const [featureImportance, setFeatureImportance] = useState([])
  const [scoreDistribution, setScoreDistribution] = useState([])
  const [predictionHistory, setPredictionHistory] = useState([])
  const [rules, setRules] = useState([])

  useEffect(() => {
    fetchMLStats()
    fetchFeatureImportance()
    fetchScoreDistribution()
    fetchRules()
    
    const interval = setInterval(fetchMLStats, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [])

  const fetchMLStats = async () => {
    try {
      // Mock data - would come from API
      setMlStats({
        total_scored: 1247,
        model_accuracy: 0.89,
        avg_score: 52,
        hot_leads_predicted: 156
      })
      
      // Mock prediction history
      setPredictionHistory([
        { date: 'Mon', actual: 85, predicted: 82 },
        { date: 'Tue', actual: 78, predicted: 80 },
        { date: 'Wed', actual: 92, predicted: 88 },
        { date: 'Thu', actual: 76, predicted: 79 },
        { date: 'Fri', actual: 89, predicted: 86 },
        { date: 'Sat', actual: 65, predicted: 68 },
        { date: 'Sun', actual: 71, predicted: 74 }
      ])
    } catch (error) {
      console.error('Failed to fetch ML stats:', error)
    }
  }

  const fetchFeatureImportance = async () => {
    try {
      const response = await fetch('/api/v1/ml/features')
      const data = await response.json()
      
      // Transform for chart
      const importance = Object.entries(data.feature_importance || {})
        .map(([name, value]) => ({ name, value: value * 100 }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
      
      setFeatureImportance(importance)
    } catch (error) {
      console.error('Failed to fetch features:', error)
      // Mock data
      setFeatureImportance([
        { name: 'has_phone', value: 18.5 },
        { name: 'urgency_keywords', value: 15.2 },
        { name: 'source_score', value: 12.8 },
        { name: 'qualification_completeness', value: 11.3 },
        { name: 'budget_mentioned', value: 9.7 },
        { name: 'message_length', value: 8.4 },
        { name: 'email_domain', value: 7.2 },
        { name: 'timeline_mentioned', value: 6.9 },
        { name: 'business_hours', value: 5.1 },
        { name: 'exclamation_count', value: 4.9 }
      ])
    }
  }

  const fetchScoreDistribution = async () => {
    // Mock data
    setScoreDistribution([
      { range: '0-20', count: 45, color: '#48dbfb' },
      { range: '21-40', count: 78, color: '#74b9ff' },
      { range: '41-60', count: 112, color: '#a29bfe' },
      { range: '61-80', count: 156, color: '#fdcb6e' },
      { range: '81-100', count: 89, color: '#ff6b6b' }
    ])
  }

  const fetchRules = async () => {
    try {
      const response = await fetch('/api/v1/routing/rules')
      const data = await response.json()
      setRules(data.rules || [])
    } catch (error) {
      console.error('Failed to fetch rules:', error)
      // Mock data
      setRules([
        { id: 'vip_customers', name: 'VIP Customer Routing', priority: 100, enabled: true, matches: 23 },
        { id: 'hot_leads', name: 'Hot Lead Priority', priority: 90, enabled: true, matches: 156 },
        { id: 'urgent_keywords', name: 'Urgent Request', priority: 95, enabled: true, matches: 12 },
        { id: 'after_hours', name: 'After Hours Auto-Reply', priority: 80, enabled: true, matches: 89 },
        { id: 'local_leads', name: 'Local Lead Priority', priority: 70, enabled: true, matches: 45 }
      ])
    }
  }

  const trainModel = async () => {
    try {
      // Show training status
      alert('Model training initiated. This may take a few minutes...')
      
      const response = await fetch('/api/v1/ml/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ leads: [], labels: [] }) // Would need actual data
      })
      
      const result = await response.json()
      alert(`Training complete! Accuracy: ${(result.test_accuracy * 100).toFixed(1)}%`)
    } catch (error) {
      alert('Training failed. Check console for details.')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 600, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Brain size={32} color="#9b59b6" />
          ML Insights
        </h1>
        <p style={{ color: '#666' }}>Machine learning scoring and smart routing analytics</p>
      </div>

      {/* ML Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <StatCard
          title="Total Scored"
          value={mlStats.total_scored}
          icon={<Target size={24} />}
          color="#9b59b6"
          trend="+23 this week"
        />
        <StatCard
          title="Model Accuracy"
          value={`${(mlStats.model_accuracy * 100).toFixed(0)}%`}
          icon={<Activity size={24} />}
          color="#27ae60"
          trend="Trained on 1.2K leads"
        />
        <StatCard
          title="Avg Score"
          value={mlStats.avg_score}
          icon={<TrendingUp size={24} />}
          color="#3498db"
          trend="Baseline: 50"
        />
        <StatCard
          title="Hot Predictions"
          value={mlStats.hot_leads_predicted}
          icon={<Zap size={24} />}
          color="#e74c3c"
          trend="12% conversion rate"
        />
      </div>

      {/* Charts Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        {/* Score Distribution */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Users size={20} color="#9b59b6" />
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Score Distribution</h3>
          </div>
          
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={scoreDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {scoreDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Feature Importance */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Brain size={20} color="#9b59b6" />
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Feature Importance</h3>
          </div>
          
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={featureImportance} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} />
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Bar dataKey="value" fill="#9b59b6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Prediction Accuracy */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '30px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="#9b59b6" />
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Prediction Accuracy</h3>
          </div>
          
          <button
            onClick={trainModel}
            style={{
              padding: '8px 16px',
              background: '#9b59b6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            <Brain size={16} style={{ marginRight: '6px' }} />
            Retrain Model
          </button>
        </div>
        
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={predictionHistory}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[60, 100]} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="actual" stroke="#3498db" fill="#3498b520" name="Actual Conversion" />
            <Area type="monotone" dataKey="predicted" stroke="#9b59b6" fill="#9b59b620" name="Predicted Score" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Routing Rules */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <Clock size={20} color="#9b59b6" />
          <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Smart Routing Rules</h3>
        </div>

        <div>
          {rules.map((rule) => (
            <div
              key={rule.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px',
                borderBottom: '1px solid #eee',
                background: rule.enabled ? 'transparent' : '#f8f8f8'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <p style={{ fontWeight: 600 }}>{rule.name}</p>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 600,
                      background: rule.enabled ? '#27ae6020' : '#e74c3c20',
                      color: rule.enabled ? '#27ae60' : '#e74c3c'
                    }}
                  >
                    {rule.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
                <p style={{ fontSize: '13px', color: '#888', marginTop: '4px' }}>
                  Priority: {rule.priority} • {rule.matches || 0} matches this month
                </p>
              </div>
              
              <div style={{ textAlign: 'right' }}>
                <button
                  style={{
                    padding: '6px 12px',
                    background: 'transparent',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px'
                  }}
                >
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, trend }) {
  const isPositive = trend && !trend.includes('failed')
  
  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      borderLeft: `4px solid ${color}`
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ color: '#666', fontSize: '14px', marginBottom: '8px' }}>{title}</p>
          <p style={{ fontSize: '32px', fontWeight: 700, color: '#1a1a2e' }}>{value}</p>
        </div>
        <div style={{ color: color }}>{icon}</div>
      </div>
      
      {trend && (
        <p style={{
          fontSize: '14px',
          color: isPositive ? '#27ae60' : '#e74c3c',
          marginTop: '12px'
        }}>
          {trend}
        </p>
      )}
    </div>
  )
}

export default MLInsights