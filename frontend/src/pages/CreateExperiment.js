import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { experimentsAPI } from '../api';

function CreateExperiment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: URLs, 2: Analysis, 3: Select Tests
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [diffAnalysis, setDiffAnalysis] = useState(null);
  const [recommendedMetrics, setRecommendedMetrics] = useState([]);
  const [selectedMetrics, setSelectedMetrics] = useState(['conversion_rate']);
  const [customMetric, setCustomMetric] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    url_a: '',
    url_b: '',
  });

  const handleAnalyzeChanges = async () => {
    if (!formData.url_a || !formData.url_b) {
      alert('Please enter both URLs');
      return;
    }
    
    try {
      setAnalyzing(true);
      
      // Call the new analyze endpoint (doesn't create experiment yet)
      const response = await experimentsAPI.analyze({
        url_a: formData.url_a,
        url_b: formData.url_b,
      });
      
      if (response.data.success && response.data.analysis) {
        setDiffAnalysis(response.data.analysis);
        
        // Set recommended metrics from LLM analysis
        if (response.data.analysis.recommended_metrics) {
          setRecommendedMetrics(response.data.analysis.recommended_metrics);
          setSelectedMetrics(response.data.analysis.recommended_metrics.slice(0, 3)); // Select top 3
        }
        setStep(2);
      } else {
        alert('Analysis completed but no results available');
      }
      
    } catch (err) {
      alert('Failed to analyze: ' + err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleStartTesting = async () => {
    try {
      setLoading(true);
      
      // Create the experiment with all info
      const createResponse = await experimentsAPI.create({
        name: formData.name,
        description: formData.description || '',
        url_a: formData.url_a,
        url_b: formData.url_b,
        primary_metric: selectedMetrics[0] || 'conversion_rate',
        alpha: 0.05,
        min_detectable_effect: 0.10,
        power: 0.80,
        duration_days: 14,
      });
      
      const experimentId = createResponse.data.id;
      
      // Update with selected metrics
      await experimentsAPI.update(experimentId, {
        selected_metrics: selectedMetrics,
      });
      
      // Start the experiment
      await experimentsAPI.start(experimentId);
      
      navigate(`/experiment/${experimentId}`);
    } catch (err) {
      alert('Failed to start testing: ' + err.message);
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleMetric = (metric) => {
    setSelectedMetrics(prev => 
      prev.includes(metric) 
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const addCustomMetric = () => {
    if (customMetric && !selectedMetrics.includes(customMetric)) {
      setSelectedMetrics([...selectedMetrics, customMetric]);
      setCustomMetric('');
    }
  };

  const availableMetrics = [
    { value: 'conversion_rate', label: 'Conversion Rate' },
    { value: 'avg_revenue', label: 'Average Revenue' },
    { value: 'ctr', label: 'Click-Through Rate' },
    { value: 'avg_session_duration', label: 'Session Duration' },
    { value: 'bounce_rate', label: 'Bounce Rate' },
  ];

  return (
    <div className="container">
      <div style={{ marginBottom: '30px' }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/')}>
          ← Back to Experiments
        </button>
        <h1>Create New A/B Test</h1>
        <p style={{ color: '#6b7280' }}>Intelligent change detection and test recommendations powered by AI</p>
        
        {/* Progress Steps */}
        <div style={{ display: 'flex', gap: '20px', marginTop: '20px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ 
              width: '32px', height: '32px', borderRadius: '50%', 
              background: step >= 1 ? '#8b5cf6' : '#e5e7eb',
              color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 'bold'
            }}>1</div>
            <span style={{ color: step >= 1 ? '#8b5cf6' : '#6b7280' }}>Enter URLs</span>
          </div>
          <div style={{ width: '40px', height: '2px', background: step >= 2 ? '#8b5cf6' : '#e5e7eb' }}></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ 
              width: '32px', height: '32px', borderRadius: '50%', 
              background: step >= 2 ? '#8b5cf6' : '#e5e7eb',
              color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 'bold'
            }}>2</div>
            <span style={{ color: step >= 2 ? '#8b5cf6' : '#6b7280' }}>Review Changes</span>
          </div>
          <div style={{ width: '40px', height: '2px', background: step >= 3 ? '#8b5cf6' : '#e5e7eb' }}></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ 
              width: '32px', height: '32px', borderRadius: '50%', 
              background: step >= 3 ? '#8b5cf6' : '#e5e7eb',
              color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 'bold'
            }}>3</div>
            <span style={{ color: step >= 3 ? '#8b5cf6' : '#6b7280' }}>Select Tests</span>
          </div>
        </div>
      </div>

      {/* Step 1: Enter URLs */}
      {step === 1 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Step 1: Enter Your URLs</h3>
            <p className="card-description">We'll automatically analyze the differences between versions</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div className="form-group">
              <label className="form-label">Experiment Name *</label>
              <input
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Red vs Blue CTA Button"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description (Optional)</label>
              <input
                type="text"
                className="form-input"
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Brief description of what you're testing"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Version A URL (Control) *</label>
              <input
                type="url"
                className="form-input"
                value={formData.url_a}
                onChange={(e) => handleChange('url_a', e.target.value)}
                placeholder="http://localhost:3001"
              />
              <small style={{ color: '#6b7280' }}>The original/baseline version</small>
            </div>

            <div className="form-group">
              <label className="form-label">Version B URL (Treatment) *</label>
              <input
                type="url"
                className="form-input"
                value={formData.url_b}
                onChange={(e) => handleChange('url_b', e.target.value)}
                placeholder="http://localhost:3002"
              />
              <small style={{ color: '#6b7280' }}>The new version with changes to test</small>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '20px' }}>
            <button 
              type="button" 
              className="btn btn-primary" 
              onClick={handleAnalyzeChanges} 
              disabled={analyzing || !formData.url_a || !formData.url_b}
              style={{ width: '300px' }}
            >
              {analyzing ? 'Analyzing Differences...' : 'Analyze Changes'}
            </button>
          </div>

          {analyzing && (
            <div style={{ textAlign: 'center', marginTop: '15px', color: '#6b7280', fontSize: '14px' }}>
              <p>AI is comparing both versions...</p>
              <p>This may take 10-30 seconds</p>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Review Changes */}
      {step === 2 && diffAnalysis && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">AI-Detected Changes</h3>
            <p className="card-description">Review what's different between your versions</p>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <p style={{ fontSize: '16px', marginBottom: '15px' }}><strong>{diffAnalysis.summary}</strong></p>
            
            {diffAnalysis.changes_detected && diffAnalysis.changes_detected.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '14px', marginBottom: '10px', color: '#374151' }}>Changes Detected:</h4>
                <ul style={{ paddingLeft: '20px', color: '#6b7280' }}>
                  {diffAnalysis.changes_detected.map((change, i) => (
                    <li key={i} style={{ marginBottom: '8px' }}>{change}</li>
                  ))}
                </ul>
              </div>
            )}

            {diffAnalysis.hypotheses && diffAnalysis.hypotheses.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '14px', marginBottom: '10px', color: '#374151' }}>AI Hypotheses:</h4>
                <ul style={{ paddingLeft: '20px', color: '#6b7280' }}>
                  {diffAnalysis.hypotheses.map((hyp, i) => (
                    <li key={i} style={{ marginBottom: '8px' }}>{hyp}</li>
                  ))}
                </ul>
              </div>
            )}

            {diffAnalysis.risk_factors && diffAnalysis.risk_factors.length > 0 && (
              <div className="error">
                <h4 style={{ fontSize: '14px', marginBottom: '10px' }}>Risk Factors:</h4>
                <ul style={{ paddingLeft: '20px' }}>
                  {diffAnalysis.risk_factors.map((risk, i) => (
                    <li key={i} style={{ marginBottom: '8px' }}>{risk}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-secondary" onClick={() => setStep(1)}>
              ← Back
            </button>
            <button className="btn btn-primary" onClick={() => setStep(3)} style={{ flex: 1 }}>
              Continue to Test Selection →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Select Tests */}
      {step === 3 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Select Metrics to Test</h3>
            <p className="card-description">Choose which metrics you want to track (recommended based on changes)</p>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ fontSize: '14px', marginBottom: '15px', color: '#374151' }}>Available Metrics:</h4>
            <div style={{ display: 'grid', gap: '10px' }}>
              {availableMetrics.map(metric => (
                <div 
                  key={metric.value}
                  onClick={() => toggleMetric(metric.value)}
                  style={{
                    padding: '15px',
                    border: selectedMetrics.includes(metric.value) ? '2px solid #8b5cf6' : '1px solid #e5e7eb',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    background: selectedMetrics.includes(metric.value) ? '#f5f3ff' : 'white',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    transition: 'all 0.2s'
                  }}
                >
                  <input 
                    type="checkbox" 
                    checked={selectedMetrics.includes(metric.value)}
                    onChange={() => {}}
                    style={{ width: '18px', height: '18px' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '600', color: '#111827' }}>{metric.label}</div>
                    {recommendedMetrics.includes(metric.value) && (
                      <span className="badge badge-success" style={{ fontSize: '10px', marginTop: '4px' }}>
                        ✓ Recommended by AI
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Custom metric input */}
          <div style={{ marginBottom: '20px', padding: '15px', background: '#f9fafb', borderRadius: '8px' }}>
            <h4 style={{ fontSize: '14px', marginBottom: '10px', color: '#374151' }}>Add Custom Metric:</h4>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                className="form-input"
                value={customMetric}
                onChange={(e) => setCustomMetric(e.target.value)}
                placeholder="e.g., add_to_cart_rate"
                style={{ flex: 1 }}
              />
              <button className="btn btn-secondary" onClick={addCustomMetric}>
                Add
              </button>
            </div>
          </div>

          {selectedMetrics.length === 0 && (
            <div className="error" style={{ marginBottom: '20px' }}>
              Please select at least one metric to test
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-secondary" onClick={() => setStep(2)}>
              ← Back
            </button>
            <button 
              className="btn btn-primary" 
              onClick={handleStartTesting}
              disabled={loading || selectedMetrics.length === 0}
              style={{ flex: 1 }}
            >
              {loading ? 'Starting Testing...' : 'Run Testing'}
            </button>Starting Testing...' : '
          </div>

          {loading && (
            <div style={{ textAlign: 'center', marginTop: '15px', color: '#6b7280', fontSize: '14px' }}>
              <p>Starting experiment and beginning data collection...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CreateExperiment;
