import React, { useState, useEffect } from 'react'
import { CheckCircle, Clock, Calendar, AlertCircle, Plus, ChevronRight, Trash2, Edit3 } from 'lucide-react'

function SimpleCMSTasks() {
  const [tasks, setTasks] = useState([])
  const [filter, setFilter] = useState('all') // all, pending, completed
  const [showAddModal, setShowAddModal] = useState(false)
  const [newTask, setNewTask] = useState({ title: '', description: '', due_date: '', priority: 2 })

  useEffect(() => {
    fetchTasks()
  }, [filter])

  const fetchTasks = async () => {
    try {
      const status = filter !== 'all' ? `?status=${filter}` : ''
      const response = await fetch(`/api/tasks${status}`)
      const data = await response.json()
      setTasks(data.tasks || [])
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
      // Mock data
      setTasks([
        { id: 1, title: "Follow up with John Smith", description: "Send pricing info", due_date: "2026-03-20", status: "pending", priority: 3 },
        { id: 2, title: "Prepare proposal for Acme Corp", description: "Include custom features", due_date: "2026-03-22", status: "pending", priority: 2 },
        { id: 3, title: "Call Sarah Johnson", description: "Discuss timeline", due_date: "2026-03-19", status: "completed", priority: 1 },
      ])
    }
  }

  const completeTask = async (taskId) => {
    try {
      await fetch(`/api/tasks/${taskId}/complete`, { method: 'PATCH' })
      fetchTasks()
    } catch (error) {
      console.error('Failed to complete task:', error)
      setTasks(tasks.map(t => t.id === taskId ? { ...t, status: 'completed' } : t))
    }
  }

  const addTask = async () => {
    if (!newTask.title) return
    
    try {
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTask)
      })
      setShowAddModal(false)
      setNewTask({ title: '', description: '', due_date: '', priority: 2 })
      fetchTasks()
    } catch (error) {
      console.error('Failed to add task:', error)
      setTasks([...tasks, { ...newTask, id: Date.now(), status: 'pending' }])
      setShowAddModal(false)
    }
  }

  const priorityLabels = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Urgent' }
  const priorityColors = { 1: '#95a5a6', 2: '#3498db', 3: '#f39c12', 4: '#e74c3c' }

  const filteredTasks = tasks.filter(task => {
    if (filter === 'pending') return task.status !== 'completed'
    if (filter === 'completed') return task.status === 'completed'
    return true
  })

  const pendingCount = tasks.filter(t => t.status !== 'completed').length
  const overdueCount = tasks.filter(t => {
    if (t.status === 'completed') return false
    const due = new Date(t.due_date)
    const today = new Date()
    return due < today
  }).length

  return (
    <div>
      <div style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 600, marginBottom: '8px' }}>Tasks</h1>
            <p style={{ color: '#666' }}>Track follow-ups and manage your to-do list</p>
          </div>
          
          <button
            onClick={() => setShowAddModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 20px',
              background: '#f39c12',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Plus size={18} />
            Add Task
          </button>
        </div>

        {/* Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#f39c1220',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#f39c12'
            }}>
              <Clock size={24} />
            </div>
            
            <div>
              <p style={{ color: '#666', fontSize: '14px' }}>Pending</p>
              <p style={{ fontSize: '28px', fontWeight: 700 }}>{pendingCount}</p>
            </div>
          </div>

          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: overdueCount > 0 ? '#e74c3c20' : '#27ae6020',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: overdueCount > 0 ? '#e74c3c' : '#27ae60'
            }}>
              <AlertCircle size={24} />
            </div>
            
            <div>
              <p style={{ color: '#666', fontSize: '14px' }}>Overdue</p>
              <p style={{ fontSize: '28px', fontWeight: 700, color: overdueCount > 0 ? '#e74c3c' : 'inherit' }}>{overdueCount}</p>
            </div>
          </div>

          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#27ae6020',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#27ae60'
            }}>
              <CheckCircle size={24} />
            </div>
            
            <div>
              <p style={{ color: '#666', fontSize: '14px' }}>Completed</p>
              <p style={{ fontSize: '28px', fontWeight: 700 }}>{tasks.filter(t => t.status === 'completed').length}</p>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{
          display: 'flex',
          gap: '8px',
          background: 'white',
          padding: '8px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          width: 'fit-content'
        }}>
          {['all', 'pending', 'completed'].map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              style={{
                padding: '8px 20px',
                borderRadius: '8px',
                border: 'none',
                background: filter === tab ? '#f39c12' : 'transparent',
                color: filter === tab ? 'white' : '#666',
                fontWeight: 600,
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tasks List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredTasks.length === 0 ? (
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '60px',
            textAlign: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
          }}>
            <CheckCircle size={48} color="#27ae60" style={{ marginBottom: '16px' }} />
            <p style={{ color: '#666', fontSize: '18px' }}>No tasks here. You're all caught up!</p>
          </div>
        ) : (
          filteredTasks.map(task => (
            <TaskCard 
              key={task.id} 
              task={task} 
              onComplete={() => completeTask(task.id)}
              priorityLabels={priorityLabels}
              priorityColors={priorityColors}
            />
          ))
        )}
      </div>

      {/* Add Task Modal */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
        onClick={() => setShowAddModal(false)}
        >
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '30px',
            width: '90%',
            maxWidth: '500px'
          }}
          onClick={e => e.stopPropagation()}
          >
            <h2 style={{ marginBottom: '24px' }}>Add New Task</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Title *</label>
                <input
                  type="text"
                  value={newTask.title}
                  onChange={e => setNewTask({ ...newTask, title: e.target.value })}
                  placeholder="What needs to be done?"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '8px'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Description</label>
                <textarea
                  value={newTask.description}
                  onChange={e => setNewTask({ ...newTask, description: e.target.value })}
                  placeholder="Add details..."
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    minHeight: '80px'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Due Date</label>
                  <input
                    type="date"
                    value={newTask.due_date}
                    onChange={e => setNewTask({ ...newTask, due_date: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '1px solid #ddd',
                      borderRadius: '8px'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Priority</label>
                  <select
                    value={newTask.priority}
                    onChange={e => setNewTask({ ...newTask, priority: parseInt(e.target.value) })}
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '1px solid #ddd',
                      borderRadius: '8px'
                    }}
                  >
                    <option value={1}>Low</option>
                    <option value={2}>Medium</option>
                    <option value={3}>High</option>
                    <option value={4}>Urgent</option>
                  </select>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                onClick={() => setShowAddModal(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              
              <button
                onClick={addTask}
                disabled={!newTask.title}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '8px',
                  background: '#f39c12',
                  color: 'white',
                  fontWeight: 600,
                  cursor: newTask.title ? 'pointer' : 'not-allowed',
                  opacity: newTask.title ? 1 : 0.5
                }}
              >
                Add Task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TaskCard({ task, onComplete, priorityLabels, priorityColors }) {
  const isOverdue = task.status !== 'completed' && task.due_date && new Date(task.due_date) < new Date()

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      opacity: task.status === 'completed' ? 0.6 : 1
    }}>
      {/* Checkbox */}
      <button
        onClick={onComplete}
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          border: task.status === 'completed' ? '2px solid #27ae60' : '2px solid #ddd',
          background: task.status === 'completed' ? '#27ae60' : 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}
      >
        {task.status === 'completed' && <CheckCircle size={16} color="white" />}
      </button>

      {/* Content */}
      <div style={{ flex: 1 }}>
        <p style={{
          fontWeight: 600,
          textDecoration: task.status === 'completed' ? 'line-through' : 'none',
          marginBottom: '4px'
        }}>
          {task.title}
        </p>
        
        {task.description && (
          <p style={{ fontSize: '14px', color: '#888', marginBottom: '8px' }}>{task.description}</p>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '13px',
            color: isOverdue ? '#e74c3c' : '#888'
          }}>
            <Calendar size={14} />
            {task.due_date ? new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'No due date'}
            {isOverdue && <span style={{ marginLeft: '4px', fontWeight: 600 }}>(Overdue)</span>}
          </span>

          <span style={{
            padding: '4px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 600,
            background: `${priorityColors[task.priority]}20`,
            color: priorityColors[task.priority]
          }}>
            {priorityLabels[task.priority]}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888' }}>
          <Edit3 size={18} />
        </button>
        <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#e74c3c' }}>
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  )
}

export default SimpleCMSTasks