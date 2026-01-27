import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { userService } from '../services/api';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    resource_type: 'database',
    config: {},
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (user?.is_admin) {
      navigate('/admin');
    }
    fetchRequests();
  }, [user, navigate]);

  const fetchRequests = async () => {
    try {
      const data = await userService.getMyRequests();
      setRequests(data);
    } catch (err) {
      console.error('Error fetching requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      let config = {};
      if (formData.resource_type === 'database') {
        config = {
          engine: formData.engine || 'postgres',
          size: formData.size || 'small',
        };
      } else if (formData.resource_type === 's3') {
        config = {
          region: formData.region || 'us-east-1',
          public: formData.public === 'true',
        };
      } else if (formData.resource_type === 'k8s_namespace') {
        config = {
          cluster: formData.cluster || 'default',
          quota: formData.quota || 'standard',
        };
      }

      await userService.submitRequest(formData.name, formData.resource_type, config);
      setSuccess('Request submitted successfully!');
      setShowModal(false);
      setFormData({ name: '', resource_type: 'database', config: {} });
      fetchRequests();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit request');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getStatusClass = (status) => `status status-${status}`;

  return (
    <div>
      <nav className="navbar">
        <h1>InfraUtomater</h1>
        <div className="user-info">
          <span>Welcome, {user?.username}</span>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="container dashboard">
        <div className="dashboard-header">
          <h2>My Resource Requests</h2>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Request
          </button>
        </div>

        {success && <div className="alert alert-success">{success}</div>}
        {error && <div className="alert alert-error">{error}</div>}

        <div className="card">
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading requests...</p>
            </div>
          ) : requests.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#888', padding: '40px' }}>
              No requests yet. Click "New Request" to create one.
            </p>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((req) => (
                    <tr key={req.id}>
                      <td>{req.id}</td>
                      <td>{req.name}</td>
                      <td>{req.resource_type}</td>
                      <td>
                        <span className={getStatusClass(req.status)}>{req.status}</span>
                      </td>
                      <td>{new Date(req.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>New Resource Request</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Resource Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="e.g., my-database, my-bucket"
                />
              </div>

              <div className="form-group">
                <label>Resource Type</label>
                <select
                  value={formData.resource_type}
                  onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                >
                  <option value="database">Database (RDS)</option>
                  <option value="s3">S3 Bucket</option>
                  <option value="k8s_namespace">K8s Namespace</option>
                </select>
              </div>

              {formData.resource_type === 'database' && (
                <>
                  <div className="form-group">
                    <label>Engine</label>
                    <select
                      value={formData.engine || 'postgres'}
                      onChange={(e) => setFormData({ ...formData, engine: e.target.value })}
                    >
                      <option value="postgres">PostgreSQL</option>
                      <option value="mysql">MySQL</option>
                      <option value="mariadb">MariaDB</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Size</label>
                    <select
                      value={formData.size || 'small'}
                      onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                    >
                      <option value="small">Small (db.t3.micro)</option>
                      <option value="medium">Medium (db.t3.small)</option>
                      <option value="large">Large (db.t3.medium)</option>
                    </select>
                  </div>
                </>
              )}

              {formData.resource_type === 's3' && (
                <>
                  <div className="form-group">
                    <label>Region</label>
                    <select
                      value={formData.region || 'us-east-1'}
                      onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                    >
                      <option value="us-east-1">US East (N. Virginia)</option>
                      <option value="us-west-2">US West (Oregon)</option>
                      <option value="eu-west-1">EU (Ireland)</option>
                      <option value="ap-south-1">Asia Pacific (Mumbai)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Public Access</label>
                    <select
                      value={formData.public || 'false'}
                      onChange={(e) => setFormData({ ...formData, public: e.target.value })}
                    >
                      <option value="false">No (Private)</option>
                      <option value="true">Yes (Public)</option>
                    </select>
                  </div>
                </>
              )}

              {formData.resource_type === 'k8s_namespace' && (
                <>
                  <div className="form-group">
                    <label>Cluster</label>
                    <input
                      type="text"
                      value={formData.cluster || ''}
                      onChange={(e) => setFormData({ ...formData, cluster: e.target.value })}
                      placeholder="default"
                    />
                  </div>
                  <div className="form-group">
                    <label>Resource Quota</label>
                    <select
                      value={formData.quota || 'standard'}
                      onChange={(e) => setFormData({ ...formData, quota: e.target.value })}
                    >
                      <option value="small">Small (1 CPU, 2Gi RAM)</option>
                      <option value="standard">Standard (2 CPU, 4Gi RAM)</option>
                      <option value="large">Large (4 CPU, 8Gi RAM)</option>
                    </select>
                  </div>
                </>
              )}

              <button type="submit" className="btn btn-primary">
                Submit Request
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
