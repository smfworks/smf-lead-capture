import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Users, Database, CheckCircle, Clock, TrendingUp, Activity, Layers, ArrowRight } from 'lucide-react'

function SimpleCMSDashboard() {
  const [stats, setStats] = useState({
    total_leads: 0,
    new_this_week: 0,
    total_contacts: 0,
    pending_tasks: 0,
    by_status: {}
  })
  const [recentLeads, setRecentLeads] = useState([])
  const [pendingTasks, setPendingTasks] = useState([])

  useEffect(() => {
    fetchStats()
    fetchRecentLeads()
    fetchTasks()
    
    const interval = setInterval(() => {
      fetchStats()
      fetchRecentLeads()
      fetchTasks()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      // Mock data for demo
      setStats({
        total_leads: 47,
        new_this_week: 12,
        total_contacts: 82,
        pending_tasks: 8,
        by_status: { new: 15, contacted: 20, qualified: 8, won: 4 }
      })
    }
  }

  const fetchRecentLeads = async () => {
    try {
      const response = await fetch('/api/leads?limit=5')
      const data = await response.json()
      setRecentLeads(data.leads || [])
    } catch (error) {
      console.error('Failed to fetch leads:', error)
      // Mock data
      setRecentLeads([
        { id: 1, name: "John Smith", email: "john@example.com", status: "new", score: 75, created_at: new Date().toISOString() },
        { id: 2, name: "Sarah Johnson", email: "sarah@example.com", status: "contacted", score: 60, created_at: new Date(Date.now() - 86400000).toISOString() },
      ])
    }
  }

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/tasks?status=pending')
      const data = await response.json()
      setPendingTasks(data.tasks?.slice(0, 5) || [])
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
      setPendingTasks([
        { id: 1, title: "Follow up with John Smith", due_date: new Date(Date.now() + 86400000).toISOString(), priority: 3 },
        { id: 2, title: "Send proposal to Acme Corp", due_date: new Date(Date.now() + 172800000).toISOString(), priority: 2 },
      ])
    }
  }

  const statusColors = {
    new: '#3498db',
    contacted: '#f39c12',
    qualified: '#9b59b6',
    proposal: '#e67e22',
    negotiation: '#e74c3c',
    won: '#27ae60',
    lost: '#95a5a6'
  }

  const pieData = Object.entries(stats.by_status || {}).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: statusColors[status] || '#888'
  }))

  return (
    <div>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 600, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Database size={32} color="#27ae60" />
          Simple CRM Dashboard
        </h1>
        <p style={{ color: '#666' }}>Lightweight lead management for small businesses</p>
      </div>

      {/* Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <StatCard
          title="Total Leads"
          value={stats.total_leads}
          icon={<Users size={24} />}
          color="#27ae60"
          trend="+12 this week"
        />
        <StatCard
          title="New This Week"
          value={stats.new_this_week}
          icon={<TrendingUp size={24} />}
          color="#3498db"
          trend="Active pipeline"
        />
        <StatCard
          title="Pending Tasks"
          value={stats.pending_tasks}
          icon={<Clock size={24} />}
          color="#f39c12"
          trend="Needs attention"
        />
        
        <StatCard
          title="Contacts"
          value={stats.total_contacts}
          icon={<Layers size={24} />}
          color="#9b59b6"
          trend="Total database"
        />
      </div>

      {/* Charts Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        {/* Lead Pipeline */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Activity size={20} color="#27ae60" />
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Lead Pipeline</h3>
          </div>
          
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Actions */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <CheckCircle size={20} color="#27ae60" />
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Quick Actions</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <QuickActionButton label="Add New Lead" onClick={() => {}} color="#27ae60" />
            <QuickActionButton label="View All Leads" onClick={() => {}} color="#3498db" />
            <QuickActionButton label="Create Task" onClick={() => {}} color="#f39c12" />
            <QuickActionButton label="Export Data" onClick={() => {}} color="#9b59b6" />
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px'
      }}>
        {/* Recent Leads */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Users size={20} color="#27ae60" />
              <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Recent Leads</h3>
            </div>
            <a href="/simple-cms/leads" style={{ color: '#27ae60', textDecoration: 'none', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              View All <ArrowRight size={16} />
            </a>
          </div>

          <div>
            {recentLeads.length === 0 ? (
              <p style={{ color: '#888', textAlign: 'center', padding: '40px' }}>No leads yet. Submit a contact form to get started.</p>
            ) : (
              recentLeads.map(lead => (
                <LeadRow key={lead.id} lead={lead} />
              ))
            )}
          </div>
        </div>

        {/* Pending Tasks */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={20} color="#f39c12" />
              <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Pending Tasks</h3>
            </div>
            <a href="/simple-cms/tasks" style={{ color: '#f39c12', textDecoration: 'none', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              View All <ArrowRight size={16} />
            </a>
          </div>

          <div>
            {pendingTasks.length === 0 ? (
              <p style={{ color: '#888', textAlign: 'center', padding: '40px' }}>No pending tasks. You're all caught up!</p>
            ) : (
              pendingTasks.map(task => (
                <TaskRow key={task.id} task={task} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, trend }) {
  const isPositive = trend && !trend.includes('Needs')
  
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
          color: isPositive ? '#27ae60' : '#f39c12',
          marginTop: '12px'
        }}>
          {trend}
        </p>
      )}
    </div>
  )
}

function QuickActionButton({ label, onClick, color }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '12px 16px',
        background: `${color}15`,
        border: `1px solid ${color}30`,
        borderRadius: '8px',
        color: color,
        fontWeight: 600,
        cursor: 'pointer',
        fontSize: '14px',
        textAlign: 'left',
        transition: 'all 0.2s'
      }}
      onMouseEnter={e => {
        e.target.style.background = color
        e.target.style.color = '#fff'
      }}
      onMouseLeave={e => {
        e.target.style.background = `${color}15`
        e.target.style.color = color
      }}
    >
      {label}
    </button>
  )
}

function LeadRow({ lead }) {
  const statusColors = {
    new: '#3498db',
    contacted: '#f39c12',
    qualified: '#9b59b6',
    proposal: '#e67e22',
    negotiation: '#e74c3c',
    won: '#27ae60',
    lost: '#95a5a6'
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px',
      borderBottom: '1px solid #eee'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: statusColors[lead.status] || '#888'
          }}
        />
        <div>
          <p style={{ fontWeight: 600 }}>{lead.name || 'Anonymous'}</p>
          <p style={{ fontSize: '13px', color: '#666' }}>{lead.email}</p>
        </div>
      </div>
      
      <div style={{ textAlign: 'right' }}>
        <span style={{
          padding: '4px 10px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: 600,
          textTransform: 'uppercase',
          background: `${statusColors[lead.status] || '#888'}20`,
          color: statusColors[lead.status] || '#888'
        }}>
          {lead.status}
        </span>
        <p style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
          Score: {lead.score}
        </p>
      </div>
    </div>
  )
}

function TaskRow({ task }) {
  const priorityColors = {
    1: '#95a5a6',
    2: '#3498db',
    3: '#f39c12',
    4: '#e74c3c'
  }

  const priorityLabels = {
    1: 'Low',
    2: 'Medium',
    3: 'High',
    4: 'Urgent'
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px',
      borderBottom: '1px solid #eee'
    }}>
      <div style={{ flex: 1 }}>
        <p style={{ fontWeight: 600, marginBottom: '4px' }}>{task.title}</p>
        <p style={{ fontSize: '13px', color: '#888' }}>
          Due: {new Date(task.due_date).toLocaleDateString()}
        </p>
      </div>
      
      <span style={{
        padding: '4px 10px',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: 600,
        background: `${priorityColors[task.priority]}20`,
        color: priorityColors[task.priority]
      }}>
        {priorityLabels[task.priority]}
      </span>
    </div>
  )
}

export default SimpleCMSDashboard