import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, Layers, Sliders, ImageOff } from 'lucide-react';
import { uploadPdf } from '../api';

export function Sidebar({ topK, setTopK, excludeImages, setExcludeImages, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadStatus({ type: 'info', message: 'Parsing with Docling & extracting diagrams...' });

    try {
      const result = await uploadPdf(file);
      setUploadStatus({
        type: 'success',
        message: `Indexed ${result.total_chunks} chunks (${result.text_chunks} text/tables, ${result.image_chunks} diagrams) into Qdrant!`,
      });
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: err.message || 'Failed to upload and index document.',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <aside className="sidebar">
      <div>
        <div className="section-label">Document Ingestion</div>
        <div
          className="dropzone"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf"
            style={{ display: 'none' }}
          />
          <div className="dropzone-icon">
            <UploadCloud size={20} />
          </div>
          <div className="dropzone-title">
            {file ? file.name : 'Upload Technical PDF'}
          </div>
          <div className="dropzone-subtitle">
            {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Click to browse manual (.pdf)'}
          </div>
        </div>

        {file && (
          <button
            className="btn-upload"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <div className="pulsing-spinner" style={{ width: 14, height: 14 }} />
                <span>Processing PDF...</span>
              </>
            ) : (
              <>
                <FileText size={16} />
                <span>Parse & Index Document</span>
              </>
            )}
          </button>
        )}

        {uploadStatus && (
          <div style={{ marginTop: 12 }} className={`upload-status-card ${uploadStatus.type}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, marginBottom: 4 }}>
              {uploadStatus.type === 'success' ? (
                <CheckCircle2 size={16} color="#10b981" />
              ) : uploadStatus.type === 'error' ? (
                <AlertTriangle size={16} color="#f43f5e" />
              ) : (
                <div className="pulsing-spinner" style={{ width: 14, height: 14 }} />
              )}
              <span>{uploadStatus.type === 'success' ? 'Indexed Successfully' : uploadStatus.type === 'error' ? 'Error' : 'Processing'}</span>
            </div>
            <div>{uploadStatus.message}</div>
          </div>
        )}
      </div>

      <div>
        <div className="section-label">Retrieval Controls</div>
        <div className="controls-card">
          <div className="control-item">
            <span className="control-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Layers size={14} /> Top Candidates (k)
            </span>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{
                background: 'var(--bg-input)',
                color: '#fff',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>
          </div>

          <div className="control-item">
            <span className="control-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ImageOff size={14} /> Exclude Diagrams
            </span>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={excludeImages}
                onChange={(e) => setExcludeImages(e.target.checked)}
              />
              <span className="slider" />
            </label>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 'auto', background: 'rgba(255,255,255,0.02)', padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: 4 }}>
          ACTIVE DOCUMENT INDEX
        </div>
        <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>
          Grundfos CM Pump Manual
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 2 }}>
          135 indexed chunks • Text, Tables, Wiring Schematics & Mountings
        </div>
      </div>
    </aside>
  );
}
