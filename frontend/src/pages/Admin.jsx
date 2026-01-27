import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/api';

const Admin = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [actionType, setActionType] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (user && !user.is_admin) {
      navigate('/dashboard');
    }
    fetchRequests();
  }, [user, navigate, filter]);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const data = await adminService.getAllRequests(filter || null);
      setRequests(data);
    } catch (err) {
      console.error('Error fetching requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = (request, action) => {
    setSelectedRequest(request);
    setActionType(action);
    setAdminNotes('');
    setShowModal(true);
  };

  const submitAction = async () => {
    setError('');
    try {
      if (actionType === 'approve') {
        await adminService.approveRequest(selectedRequest.id, adminNotes);
        setSuccess(`Request #${selectedRequest.id} approved successfully!`);
      } else {
        if (!adminNotes.trim()) {
          setError('Please provide a reason for rejection');
          return;
        }
        await adminService.rejectRequest(selectedRequest.id, adminNotes);
        setSuccess(`Request #${selectedRequest.id} rejected.`);
      }
      setShowModal(false);
      fetchRequests();
    } catch (err) {
      setError(err.response?.data?.detail || 'Action failed');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getStatusClass = (status) => `status status-${status}`;

  const stats = {
    total: requests.length,
    pending: requests.filter((r) => r.status === 'pending').length,
    approved: requests.filter((r) => r.status === 'approved').length,
    provisioned: requests.filter((r) => r.status === 'provisioned').length,
  };

  return (
    <div>
      <nav className="navbar">
        <h1>InfraUtomater Admin</h1>
        <div className="user-info">
          <span>Admin: {user?.username}</span>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="container dashboard">
        <div className="dashboard-header">
          <h2>Resource Requests</h2>
        </div>

        {success && <div className="alert alert-success">{success}</div>}

        <div className="stats">
          <div className="stat-card">
            <div className="number">{stats.total}</div>
            <div className="label">Total Requests</div>
          </div>
          <div className="stat-card">
            <div className="number">{stats.pending}</div>
            <div className="label">Pending</div>
          </div>
          <div className="stat-card">
            <div className="number">{stats.approved}</div>
            <div className="label">Approved</div>
          </div>
          <div className="stat-card">
            <div className="number">{stats.provisioned}</div>
            <div className="label">Provisioned</div>
          </div>
        </div>

        <div className="tabs">
          <button
            className={`tab ${filter === '' ? 'active' : ''}`}
            onClick={() => setFilter('')}
          >
            All
          </button>
          <button
            className={`tab ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pending
          </button>
          <button
            className={`tab ${filter === 'approved' ? 'active' : ''}`}
            onClick={() => setFilter('approved')}
          >
            Approved
          </button>
          <button
            className={`tab ${filter === 'provisioned' ? 'active' : ''}`}
            onClick={() => setFilter('provisioned')}
          >
            Provisioned
          </button>
          <button
            className={`tab ${filter === 'rejected' ? 'active' : ''}`}
            onClick={() => setFilter('rejected')}
          >
            Rejected
          </button>
        </div>

        <div className="card">
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading requests...</p>
            </div>
          ) : requests.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#888', padding: '40px' }}>
              No requests found.
            </p>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>User ID</th>
                    <th>Team ID</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((req) => (
                    <tr key={req.id}>
                      <td>{req.id}</td>
                      <td>{req.name}</td>
                      <td>{req.resource_type}</td>
                      <td>{req.user_id}</td>
                      <td>{req.team_id}</td>
                      <td>
                        <span className={getStatusClass(req.status)}>{req.status}</span>
                      </td>
                      <td>{new Date(req.created_at).toLocaleDateString()}</td>
                      <td>
                        {req.status === 'pending' && (
                          <div className="actions">
                            <button
                              className="btn btn-success btn-small"
                              onClick={() => handleAction(req, 'approve')}
                            >
                              Approve
                            </button>
                            <button
                              className="btn btn-danger btn-small"
                              onClick={() => handleAction(req, 'reject')}
                            >
                              Reject
                            </button>
                          </div>
                        )}
                        {req.status !== 'pending' && (
                          <span style={{ color: '#666' }}>-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showModal && selectedRequest && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{actionType === 'approve' ? 'Approve' : 'Reject'} Request</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div style={{ marginBottom: '20px' }}>
              <p><strong>Request ID:</strong> {selectedRequest.id}</p>
              <p><strong>Name:</strong> {selectedRequest.name}</p>
              <p><strong>Type:</strong> {selectedRequest.resource_type}</p>
              <p><strong>Config:</strong></p>
              <pre style={{
                background: 'rgba(0,0,0,0.3)',
                padding: '10px',
                borderRadius: '5px',
                fontSize: '12px',
                overflow: 'auto'
              }}>
                {JSON.stringify(selectedRequest.config, null, 2)}
              </pre>
            </div>

            <div className="form-group">
              <label>Admin Notes {actionType === 'reject' && '(Required)'}</label>
              <textarea
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                placeholder={actionType === 'approve'
                  ? 'Optional notes...'
                  : 'Please provide a reason for rejection...'}
                rows={3}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                className={`btn ${actionType === 'approve' ? 'btn-success' : 'btn-danger'}`}
                onClick={submitAction}
              >
                {actionType === 'approve' ? 'Approve' : 'Reject'}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Admin;
