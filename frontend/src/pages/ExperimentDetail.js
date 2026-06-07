import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { experimentsAPI, analysisAPI } from '../api';

function ExperimentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [experiment, setExperiment] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const loadData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const [expData, resultsData] = await Promise.all([
        experimentsAPI.getOne(id),
        analysisAPI.getResults(id).catch(() => null),
      ]);
      setExperiment(expData.data);
      setResults(resultsData?.data);
    } catch (err) {
      console.error('Failed to load:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (experiment?.status === 'RUNNING') {
        loadData(true);
      }
    }, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleStart = async () => {
    try {
      await experimentsAPI.start(id);
      loadData();
    } catch (err) {
      alert('Failed to start: ' + err.message);
    }
  };

  const handleStop = async () => {
    if (!window.confirm('Stop this experiment?')) return;
    try {
      await experimentsAPI.stop(id);
      loadData();
    } catch (err) {
      alert('Failed to stop: ' + err.message);
    }
  };

  const handleGenerateReport = async () => {
    try {
      await experimentsAPI.generateReport(id);
      loadData();
    } catch (err) {
      alert('Failed to generate report: ' + err.message);
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

  const formatPercent = (num) => (num * 100).toFixed(2) + '%';
  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  if (loading) {
    return <div className="container"><div className="loading">Loading experiment...</div></div>;
  }

  if (!experiment) {
    return (
      <div className="container">
        <div className="card">
          <p>Experiment not found</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>Back to Experiments</button>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/')}>← Back</button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '15px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <h1>{experiment.name}</h1>
              <span className={`badge ${getStatusBadge(experiment.status)}`}>{experiment.status}</span>
            </div>
            <p style={{ color: '#6b7280' }}>{experiment.description}</p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => loadData()}>Refresh</button>
            {experiment.status === 'DRAFT' && (
              <button className="btn btn-primary btn-sm" onClick={handleStart}>Start</button>
            )}
            {experiment.status === 'RUNNING' && (
              <button className="btn btn-danger btn-sm" onClick={handleStop}>Stop</button>
            )}
            {['COMPLETED', 'STOPPED'].includes(experiment.status) && !experiment.llm_report && (
              <button className="btn btn-primary btn-sm" onClick={handleGenerateReport}>Generate AI Report</button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #e5e7eb' }}>
        <div style={{ display: 'flex', gap: '20px' }}>
          {['overview', 'results', 'diff', 'report'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '10px 15px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                borderBottom: activeTab === tab ? '2px solid #3b82f6' : 'none',
                fontWeight: activeTab === tab ? '600' : '400',
                color: activeTab === tab ? '#3b82f6' : '#6b7280',
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div>
          {results && results.control && results.treatment ? (
            <div className="stats-grid">
              {[
                { label: 'Conversion Rate', key: 'conversion_rate', format: formatPercent },
                { label: 'Avg Revenue', key: 'avg_revenue', format: (v) => `$${v.toFixed(2)}` },
                { label: 'CTR', key: 'ctr', format: formatPercent },
                { label: 'Users', key: 'users_count', format: formatNumber },
              ].map(({ label, key, format }) => (
                <div key={key} className="stat-card">
                  <div className="stat-label">{label}</div>
                  <div className="stat-value">{format(results.treatment[key] || 0)}</div>
                  <div className="stat-delta">
                    Control: {format(results.control[key] || 0)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card">
              <p style={{ textAlign: 'center', color: '#6b7280' }}>No data yet. Start the experiment to collect metrics.</p>
            </div>
          )}
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && (
        <div>
          {results ? (
            <div className="card">
              <h3>Statistical Analysis</h3>
              {results.recommendation && (
                <div style={{ padding: '15px', background: '#eff6ff', borderRadius: '8px', marginBottom: '20px' }}>
                  <strong>Recommendation:</strong> {results.recommendation}
                </div>
              )}
              {results.tests && Object.keys(results.tests).map(testName => {
                const test = results.tests[testName];
                return (
                  <div key={testName} style={{ padding: '10px 0', borderBottom: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{testName}</strong>
                      <span>p-value: {test.p_value?.toFixed(4) || 'N/A'}</span>
                    </div>
                    {test.significant !== undefined && (
                      <span className={`badge ${test.significant ? 'badge-success' : 'badge-default'}`}>
                        {test.significant ? 'Significant' : 'Not Significant'}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="card">
              <p style={{ textAlign: 'center', color: '#6b7280' }}>No results yet. Need more data.</p>
            </div>
          )}
        </div>
      )}

      {/* Diff Tab */}
      {activeTab === 'diff' && (
        <div>
          {experiment.llm_diff ? (
            <div className="card">
              <h3>AI-Detected Changes</h3>
              <p style={{ color: '#6b7280', marginBottom: '20px' }}>{experiment.llm_diff.summary}</p>
              
              {experiment.llm_diff.changes_detected && (
                <div style={{ marginBottom: '20px' }}>
                  <h4>Changes Detected:</h4>
                  <ul>
                    {experiment.llm_diff.changes_detected.map((change, i) => (
                      <li key={i}>{change}</li>
                    ))}
                  </ul>
                </div>
              )}

              {experiment.llm_diff.hypotheses && (
                <div style={{ marginBottom: '20px' }}>
                  <h4>Hypotheses:</h4>
                  <ul>
                    {experiment.llm_diff.hypotheses.map((hyp, i) => (
                      <li key={i}>{hyp}</li>
                    ))}
                  </ul>
                </div>
              )}

              {experiment.llm_diff.risk_factors && experiment.llm_diff.risk_factors.length > 0 && (
                <div className="error">
                <h4>Risk Factors:</h4>
                  <ul>
                    {experiment.llm_diff.risk_factors.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <p style={{ textAlign: 'center', color: '#6b7280' }}>LLM diff analysis in progress...</p>
            </div>
          )}
        </div>
      )}

      {/* Report Tab */}
      {activeTab === 'report' && (
        <div>
          {experiment.llm_report ? (
            <div className="card">
              <h3>AI-Generated Report</h3>
              <div style={{ padding: '15px', background: '#f0fdf4', borderRadius: '8px', marginBottom: '20px' }}>
                <strong>{experiment.llm_report.headline}</strong>
                <p style={{ margin: '10px 0' }}>Confidence: {(experiment.llm_report.confidence * 100).toFixed(0)}%</p>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <h4>Verdict:</h4>
                <p>{experiment.llm_report.verdict}</p>
              </div>

              {experiment.llm_report.what_changed && (
                <div style={{ marginBottom: '20px' }}>
                  <h4>What Changed:</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{experiment.llm_report.what_changed}</p>
                </div>
              )}

              {experiment.llm_report.what_happened && (
                <div style={{ marginBottom: '20px' }}>
                  <h4>What Happened:</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{experiment.llm_report.what_happened}</p>
                </div>
              )}

              {experiment.llm_report.recommendation && (
                <div style={{ marginBottom: '20px' }}>
                  <h4>Recommendation:</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{experiment.llm_report.recommendation}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <p style={{ textAlign: 'center', color: '#6b7280' }}>No AI report yet. Generate one after stopping the experiment.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ExperimentDetail;
