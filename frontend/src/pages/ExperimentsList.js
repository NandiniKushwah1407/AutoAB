import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { experimentsAPI } from '../api';

function ExperimentsList() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    try {
      setLoading(true);
      const response = await experimentsAPI.getAll();
      setExperiments(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (id) => {
    try {
      await experimentsAPI.start(id);
      loadExperiments();
    } catch (err) {
      alert('Failed to start: ' + err.message);
    }
  };

  const handleStop = async (id) => {
    if (!window.confirm('Stop this experiment?')) return;
    try {
      await experimentsAPI.stop(id);
      loadExperiments();
    } catch (err) {
      alert('Failed to stop: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this experiment? This cannot be undone.')) return;
    try {
      await experimentsAPI.delete(id);
      loadExperiments();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      DRAFT: 'badge-default',
      RUNNING: 'badge-info',
      ANALYSIS: 'badge-warning',
      COMPLETED: 'badge-success',
      STOPPED: 'badge-danger',
    };
    return badges[status] || 'badge-default';
  };

  if (loading) {
    return <div className="container"><div className="loading">Loading experiments...</div></div>;
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">Failed to load experiments: {error}</div>
        <button className="btn btn-primary" onClick={loadExperiments}>Retry</button>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
          <h1>Experiments</h1>
          <p style={{ color: '#6b7280' }}>{experiments.length} total</p>
        </div>
        <Link to="/create">
          <button className="btn btn-primary">+ Create Experiment</button>
        </Link>
      </div>

      {experiments.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <h3>No experiments yet</h3>
            <p>Create your first A/B test to start collecting data and analyzing results</p>
            <Link to="/create">
              <button className="btn btn-primary">Create Your First Experiment</button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-2">
          {experiments.map((exp) => (
            <div key={exp.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                <h3 style={{ margin: 0 }}>{exp.name}</h3>
                <span className={`badge ${getStatusBadge(exp.status)}`}>{exp.status}</span>
              </div>
              <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '15px' }}>
                {exp.description || 'No description'}
              </p>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '15px' }}>
                <div><strong>Version A:</strong> {new URL(exp.url_a).hostname}</div>
                <div><strong>Version B:</strong> {new URL(exp.url_b).hostname}</div>
                <div><strong>Metric:</strong> {exp.primary_metric} | <strong>Duration:</strong> {exp.duration_days} days</div>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <Link to={`/experiment/${exp.id}`} style={{ flex: 1 }}>
                  <button className="btn btn-primary" style={{ width: '100%' }}>View Details</button>
                </Link>
                {exp.status === 'DRAFT' && (
                  <button className="btn btn-secondary btn-sm" onClick={() => handleStart(exp.id)}>Start</button>
                )}
                {exp.status === 'RUNNING' && (
                  <button className="btn btn-danger btn-sm" onClick={() => handleStop(exp.id)}>Stop</button>
                )}
                {(exp.status === 'DRAFT' || exp.status === 'STOPPED') && (
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(exp.id)}>Delete</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ExperimentsList;
