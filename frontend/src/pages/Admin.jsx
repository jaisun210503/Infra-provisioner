import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/api';

const Admin = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('requests');
  const [requests, setRequests] = useState([]);
  const [teams, setTeams] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [actionType, setActionType] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newTeam, setNewTeam] = useState({ name: '', description: '' });
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedUser, setSelectedUser] = useState('');
  const [awsCredentials, setAwsCredentials] = useState([]);
  const [awsForm, setAwsForm] = useState({
    team_id: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_region: 'us-east-1',
    aws_session_token: ''
  });
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    if (user && !user.is_admin) {
      navigate('/dashboard');
    }
    if (activeTab === 'requests') {
      fetchRequests();
    } else if (activeTab === 'teams') {
      fetchTeamsAndUsers();
    } else if (activeTab === 'aws-settings') {
      fetchAWSCredentials();
      fetchTeamsAndUsers();
    }
  }, [user, navigate, filter, activeTab]);

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

  const fetchTeamsAndUsers = async () => {
    setLoading(true);
    try {
      const [teamsData, usersData] = await Promise.all([
        adminService.getTeams(),
        adminService.getUsers()
      ]);
      setTeams(teamsData);
      setUsers(usersData);
    } catch (err) {
      console.error('Error fetching teams/users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = (request, action) => {
    setSelectedRequest(request);
    setActionType(action);
    setAdminNotes('');
    setModalType('action');
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

  const handleCreateTeam = async () => {
    setError('');
    try {
      if (!newTeam.name.trim()) {
        setError('Team name is required');
        return;
      }
      await adminService.createTeam(newTeam.name, newTeam.description);
      setSuccess('Team created successfully!');
      setShowModal(false);
      setNewTeam({ name: '', description: '' });
      fetchTeamsAndUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create team');
    }
  };

  const handleAddMember = async () => {
    setError('');
    try {
      if (!selectedTeam || !selectedUser) {
        setError('Please select both a team and a user');
        return;
      }
      await adminService.addTeamMember(selectedTeam, selectedUser);
      setSuccess('User added to team successfully!');
      setShowModal(false);
      setSelectedTeam('');
      setSelectedUser('');
      fetchTeamsAndUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add member');
    }
  };

  const fetchAWSCredentials = async () => {
    setLoading(true);
    try {
      const data = await adminService.getAWSCredentials();
      setAwsCredentials(data);
    } catch (err) {
      console.error('Error fetching AWS credentials:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAWSCredentials = async () => {
    setError('');
    setSuccess('');
    try {
      if (!awsForm.aws_access_key_id || !awsForm.aws_secret_access_key) {
        setError('AWS Access Key ID and Secret Access Key are required');
        return;
      }

      await adminService.createAWSCredentials(awsForm);
      setSuccess('AWS credentials saved successfully!');
      setAwsForm({
        team_id: '',
        aws_access_key_id: '',
        aws_secret_access_key: '',
        aws_region: 'us-east-1',
        aws_session_token: ''
      });
      setTestResult(null);
      fetchAWSCredentials();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save credentials');
    }
  };

  const handleTestAWSCredentials = async () => {
    setError('');
    setSuccess('');
    setTestResult(null);
    try {
      if (!awsForm.aws_access_key_id || !awsForm.aws_secret_access_key) {
        setError('Please enter credentials to test');
        return;
      }

      const result = await adminService.testAWSCredentials(awsForm);
      setTestResult(result);

      if (result.success) {
        setSuccess('Credentials are valid!');
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to test credentials');
    }
  };

  const handleDeleteAWSCredentials = async (teamId) => {
    if (!confirm('Are you sure you want to delete these credentials?')) {
      return;
    }

    setError('');
    setSuccess('');
    try {
      await adminService.deleteAWSCredentials(teamId);
      setSuccess('Credentials deleted successfully!');
      fetchAWSCredentials();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete credentials');
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

  const usersWithoutTeam = users.filter(u => !u.team_id);

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
          <h2>
            {activeTab === 'requests' && 'Resource Requests'}
            {activeTab === 'teams' && 'Team Management'}
            {activeTab === 'aws-settings' && 'AWS Settings'}
          </h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className={`btn ${activeTab === 'requests' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('requests')}
            >
              Requests
            </button>
            <button
              className={`btn ${activeTab === 'teams' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('teams')}
            >
              Teams
            </button>
            <button
              className={`btn ${activeTab === 'aws-settings' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('aws-settings')}
            >
              AWS Settings
            </button>
          </div>
        </div>

        {success && <div className="alert alert-success">{success}</div>}

        {activeTab === 'requests' && (
          <>
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
          </>
        )}

        {activeTab === 'teams' && (
          <>
            <div className="stats">
              <div className="stat-card">
                <div className="number">{teams.length}</div>
                <div className="label">Total Teams</div>
              </div>
              <div className="stat-card">
                <div className="number">{users.length}</div>
                <div className="label">Total Users</div>
              </div>
              <div className="stat-card">
                <div className="number">{usersWithoutTeam.length}</div>
                <div className="label">Users Without Team</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <button
                className="btn btn-primary"
                onClick={() => { setModalType('createTeam'); setShowModal(true); setError(''); }}
              >
                + Create Team
              </button>
              <button
                className="btn btn-success"
                onClick={() => { setModalType('addMember'); setShowModal(true); setError(''); }}
              >
                + Add User to Team
              </button>
            </div>

            <div className="card">
              <h3>Teams</h3>
              {loading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Loading teams...</p>
                </div>
              ) : teams.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                  No teams created yet.
                </p>
              ) : (
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {teams.map((team) => (
                        <tr key={team.id}>
                          <td>{team.id}</td>
                          <td>{team.name}</td>
                          <td>{team.description || '-'}</td>
                          <td>{new Date(team.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="card" style={{ marginTop: '20px' }}>
              <h3>Users</h3>
              {loading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Loading users...</p>
                </div>
              ) : users.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                  No users registered yet.
                </p>
              ) : (
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Team ID</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id}>
                          <td>{u.id}</td>
                          <td>{u.username}</td>
                          <td>{u.email}</td>
                          <td>
                            {u.team_id ? (
                              <span className="status status-approved">{u.team_id}</span>
                            ) : (
                              <span className="status status-pending">None</span>
                            )}
                          </td>
                          <td>{new Date(u.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'aws-settings' && (
          <>
            <div className="card">
              <h3>Configure AWS Credentials</h3>
              <p style={{ color: '#888', marginBottom: '20px' }}>
                Provide AWS credentials for Terraform to provision resources.
                Configure per-team credentials or leave team blank for global default.
              </p>

              {error && <div className="alert alert-error">{error}</div>}
              {success && <div className="alert alert-success">{success}</div>}

              <div className="form-group">
                <label>Team (optional - leave blank for global default)</label>
                <select
                  value={awsForm.team_id}
                  onChange={(e) => setAwsForm({ ...awsForm, team_id: e.target.value })}
                >
                  <option value="">-- Global Default --</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>{team.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>AWS Access Key ID *</label>
                <input
                  type="text"
                  value={awsForm.aws_access_key_id}
                  onChange={(e) => setAwsForm({ ...awsForm, aws_access_key_id: e.target.value })}
                  placeholder="AKIAIOSFODNN7EXAMPLE"
                />
              </div>

              <div className="form-group">
                <label>AWS Secret Access Key *</label>
                <input
                  type="password"
                  value={awsForm.aws_secret_access_key}
                  onChange={(e) => setAwsForm({ ...awsForm, aws_secret_access_key: e.target.value })}
                  placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                />
              </div>

              <div className="form-group">
                <label>AWS Region</label>
                <select
                  value={awsForm.aws_region}
                  onChange={(e) => setAwsForm({ ...awsForm, aws_region: e.target.value })}
                >
                  <option value="us-east-1">US East (N. Virginia)</option>
                  <option value="us-west-2">US West (Oregon)</option>
                  <option value="eu-west-1">EU (Ireland)</option>
                  <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                </select>
              </div>

              <div className="form-group">
                <label>AWS Session Token (optional)</label>
                <input
                  type="password"
                  value={awsForm.aws_session_token}
                  onChange={(e) => setAwsForm({ ...awsForm, aws_session_token: e.target.value })}
                  placeholder="For temporary credentials only"
                />
              </div>

              {testResult && (
                <div className={`alert ${testResult.success ? 'alert-success' : 'alert-error'}`}>
                  <strong>{testResult.message}</strong>
                  {testResult.account_id && (
                    <div style={{ marginTop: '10px', fontSize: '12px' }}>
                      <div>Account ID: {testResult.account_id}</div>
                      <div>User ARN: {testResult.user_arn}</div>
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button className="btn btn-primary" onClick={handleSaveAWSCredentials}>
                  Save Credentials
                </button>
                <button className="btn btn-secondary" onClick={handleTestAWSCredentials}>
                  Test Connection
                </button>
              </div>
            </div>

            <div className="card" style={{ marginTop: '20px' }}>
              <h3>Configured Credentials</h3>
              {loading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Loading credentials...</p>
                </div>
              ) : awsCredentials.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                  No AWS credentials configured yet.
                </p>
              ) : (
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Team</th>
                        <th>Region</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {awsCredentials.map((cred) => (
                        <tr key={cred.id}>
                          <td>
                            {cred.team_id ? (
                              teams.find(t => t.id === cred.team_id)?.name || `Team ${cred.team_id}`
                            ) : (
                              <span className="status status-approved">Global Default</span>
                            )}
                          </td>
                          <td>{cred.aws_region}</td>
                          <td>{new Date(cred.created_at).toLocaleDateString()}</td>
                          <td>
                            <button
                              className="btn btn-danger btn-small"
                              onClick={() => handleDeleteAWSCredentials(cred.team_id)}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {showModal && modalType === 'action' && selectedRequest && (
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

      {showModal && modalType === 'createTeam' && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Team</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="form-group">
              <label>Team Name *</label>
              <input
                type="text"
                value={newTeam.name}
                onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                placeholder="Enter team name"
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newTeam.description}
                onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                placeholder="Optional description"
                rows={3}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn btn-primary" onClick={handleCreateTeam}>
                Create Team
              </button>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showModal && modalType === 'addMember' && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add User to Team</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="form-group">
              <label>Select Team *</label>
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
              >
                <option value="">-- Select a team --</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Select User *</label>
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
              >
                <option value="">-- Select a user --</option>
                {usersWithoutTeam.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username} ({u.email})
                  </option>
                ))}
              </select>
              {usersWithoutTeam.length === 0 && (
                <p style={{ color: '#888', fontSize: '12px', marginTop: '5px' }}>
                  All users are already in teams.
                </p>
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn btn-success" onClick={handleAddMember}>
                Add to Team
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
