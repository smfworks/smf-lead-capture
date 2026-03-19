import React, { useState, useEffect } from 'react'
import { Search, Filter, Plus, Phone, Mail, Building, Calendar, MoreVertical, ChevronLeft, ChevronRight } from 'lucide-react'

function SimpleCMSLeads() {
  const [leads, setLeads] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedLead, setSelectedLead] = useState(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    fetchLeads()
  }, [currentPage, statusFilter])

  const fetchLeads = async () => {
    try {
      const status = statusFilter !== 'all' ? `?status=${statusFilter}` : ''
      const response = await fetch(`/api/leads${status}`)
      const data = await response.json()
      setLeads(data.leads || [])
    } catch (error) {
      console.error('Failed to fetch leads:', error)
      // Mock data
      setLeads([
        { id: 1, name: 'John Smith', email: 'john@acme.com', phone: '+1-555-0101', company: 'Acme Corp', status: 'new', score: 75, created_at: '2026-03-19T10:00:00Z', service_interest: 'AI Automation', budget: '$10k-$25k' },
        { id: 2, name: 'Sarah Johnson', email: 'sarah@tech.co', phone: '+1-555-0102', company: 'Tech Solutions', status: 'contacted', score: 60, created_at: '2026-03-18T15:30:00Z', service_interest: 'Lead Capture', budget: '$5k-$10k' },
        { id: 3, name: 'Mike Davis', email: 'mike@startup.io', phone: '+1-555-0103', company: 'Startup Inc', status: 'qualified', score: 85, created_at: '2026-03-17T09:15:00Z', service_interest: 'Custom Development', budget: '$25k+' },
      ])
    }
  }

  const filteredLeads = leads.filter(lead => 
    lead.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.company?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const statusColors = {
    new: { bg: '#3498db20', text: '#3498db' },
    contacted: { bg: '#f39c1220', text: '#f39c12' },
    qualified: { bg: '#9b59b620', text: '#9b59b6' },
    proposal: { bg: '#e67e2220', text: '#e67e22' },
    negotiation: { bg: '#e74c3c20', text: '#e74c3c' },
    won: { bg: '#27ae6020', text: '#27ae60' },
    lost: { bg: '#95a5a620', text: '#95a5a6' }
  }

  return (
    <div>
      <div style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 600, marginBottom: '8px' }}>All Leads</h1>
            <p style={{ color: '#666' }}>Manage your leads and track their progress</p>
          </div>
          
          <button
            onClick={() => setShowModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 20px',
              background: '#27ae60',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Plus size={18} />
            Add Lead
          </button>
        </div>

        {/* Filters */}
        <div style={{
          display: 'flex',
          gap: '16px',
          background: 'white',
          padding: '16px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#888' }} />
            <input
              type="text"
              placeholder="Search leads..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px 10px 40px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '14px'
              }}
            />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={18} color="#666" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '10px 16px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              <option value="all">All Status</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="qualified">Qualified</option>
              <option value="proposal">Proposal</option>
              <option value="negotiation">Negotiation</option>
              <option value="won">Won</option>
              <option value="lost">Lost</option>
            </select>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        overflow: 'hidden'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e9ecef' }}>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Name</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Contact</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Company</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Status</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Score</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Date</th>
              <th style={{ padding: '16px', textAlign: 'center', fontWeight: 600, color: '#495057', fontSize: '13px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredLeads.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ padding: '40px', textAlign: 'center', color: '#888' }}>
                  No leads found. Add your first lead to get started.
                </td>
              </tr>
            ) : (
              filteredLeads.map(lead => (
                <tr 
                  key={lead.id} 
                  style={{ borderBottom: '1px solid #e9ecef', cursor: 'pointer' }}
                  onClick={() => setSelectedLead(lead)}
                  onMouseEnter={e => e.currentTarget.style.background = '#f8f9fa'}
                  onMouseLeave={e => e.currentTarget.style.background = 'white'}
                >
                    <td style={{ padding: '16px' }}>
                      <div>
                        <p style={{ fontWeight: 600, marginBottom: '4px' }}>{lead.name || 'Anonymous'}</p>
                        {lead.service_interest && (
                          <p style={{ fontSize: '12px', color: '#27ae60' }}>{lead.service_interest}</p>
                        )}
                      </div>
                    </td>
                    
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <a href={`mailto:${lead.email}`} style={{ color: '#3498db', textDecoration: 'none', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Mail size={14} /> {lead.email}
                        </a>
                        {lead.phone && (
                          <a href={`tel:${lead.phone}`} style={{ color: '#27ae60', textDecoration: 'none', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Phone size={14} /> {lead.phone}
                          </a>
                        )}
                      </div>
                    </td>
                    
                    <td style={{ padding: '16px' }}>
                      {lead.company && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Building size={16} color="#888" />
                          <span>{lead.company}</span>
                        </div>
                      )}
                    </td>
                    
                    <td style={{ padding: '16px' }}>
                      <span style={{
                        padding: '6px 12px',
                        borderRadius: '20px',
                        fontSize: '12px',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        background: statusColors[lead.status]?.bg || '#eee',
                        color: statusColors[lead.status]?.text || '#666'
                      }}>
                        {lead.status}
                      </span>
                    </td>
                    
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          width: '40px',
                          height: '6px',
                          background: '#e9ecef',
                          borderRadius: '3px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${lead.score}%`,
                            height: '100%',
                            background: lead.score >= 70 ? '#e74c3c' : lead.score >= 40 ? '#f39c12' : '#3498db',
                            borderRadius: '3px'
                          }} />
                        </div>
                        <span style={{ fontWeight: 600, fontSize: '14px' }}>{lead.score}</span>
                      </div>
                    </td>
                    
                    <td style={{ padding: '16px', color: '#666', fontSize: '14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Calendar size={14} />
                        {new Date(lead.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>
                    </td>
                    
                    <td style={{ padding: '16px', textAlign: 'center' }}>
                      <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888' }}>
                        <MoreVertical size={18} />
                      </button>
                    </td>
                  </tr>
              ))
            )}
          </tbody>
        </table>
        
        {/* Pagination */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px',
          borderTop: '1px solid #e9ecef'
        }}>
          <p style={{ color: '#666', fontSize: '14px' }}>
            Showing {filteredLeads.length} of {filteredLeads.length} leads
          </p>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(p => p - 1)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                background: 'white',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                opacity: currentPage === 1 ? 0.5 : 1
              }}
            >
              <ChevronLeft size={16} /> Prev
            </button>
            
            <button
              onClick={() => setCurrentPage(p => p + 1)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <LeadDetailModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}
    </div>
  )
}

function LeadDetailModal({ lead, onClose }) {
  return (
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
    onClick={onClose}
    >
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '30px',
        width: '90%',
        maxWidth: '600px',
        maxHeight: '80vh',
        overflow: 'auto'
      }}
      onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 600 }}>{lead.name || 'Anonymous'}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer' }}>×</button>
        </div>

        <div style={{ display: 'grid', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Email</label>
            <p>{lead.email}</p>
          </div>

          {lead.phone && (
            <div>
              <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Phone</label>
              <p>{lead.phone}</p>
            </div>
          )}

          {lead.company && (
            <div>
              <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Company</label>
              <p>{lead.company}</p>
            </div>
          )}

          <div>
            <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Status</label>
            <p style={{ textTransform: 'capitalize' }}>{lead.status}</p>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Score</label>
            <p>{lead.score}/100</p>
          </div>

          {lead.budget && (
            <div>
              <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Budget</label>
              <p>{lead.budget}</p>
            </div>
          )}

          <div>
            <label style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', fontWeight: 600 }}>Created</label>
            <p>{new Date(lead.created_at).toLocaleString()}</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '24px', paddingTop: '24px', borderTop: '1px solid #eee' }}>
          <a
            href={`mailto:${lead.email}`}
            style={{
              flex: 1,
              padding: '12px 20px',
              background: '#3498db',
              color: 'white',
              borderRadius: '8px',
              textDecoration: 'none',
              textAlign: 'center',
              fontWeight: 600
            }}
          >
            Send Email
          </a>
          
          {lead.phone && (
            <a
              href={`tel:${lead.phone}`}
              style={{
                flex: 1,
                padding: '12px 20px',
                background: '#27ae60',
                color: 'white',
                borderRadius: '8px',
                textDecoration: 'none',
                textAlign: 'center',
                fontWeight: 600
              }}
            >
              Call
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default SimpleCMSLeads