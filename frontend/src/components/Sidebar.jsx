import React, { useRef, useState } from 'react';
import {
  UploadCloud, FileText, CheckCircle2, AlertTriangle,
  Layers, Sliders, ImageOff, Trash2, X, FilePlus2, Loader2,
} from 'lucide-react';
import { uploadPdf, deleteDocument } from '../api';

export function Sidebar({ topK, setTopK, excludeImages, setExcludeImages, onUploadSuccess, indexedDocs, refreshDocs, sessionId }) {
  // Queue of File objects selected by the user
  const [fileQueue, setFileQueue] = useState([]);
  // Per-file status: { [filename]: { type: 'pending'|'uploading'|'success'|'error', message: string } }
  const [fileStatuses, setFileStatuses] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  // Deleting state
  const [deletingDoc, setDeletingDoc] = useState(null);

  const fileInputRef = useRef(null);

  const ALLOWED_EXTS = [
    '.pdf', '.docx', '.pptx', '.xlsx', '.html', '.htm', '.md', '.csv',
    '.odt', '.ods', '.odp', '.tex', '.adoc', '.asciidoc',
    '.py', '.js', '.ts', '.c', '.cpp', '.java', '.go', '.rs', '.sh',
    '.json', '.yaml', '.yml', '.txt', '.log', '.xml',
    '.png', '.jpg', '.jpeg', '.tiff', '.bmp',
  ].join(',');

  const handleFileChange = (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const newFiles = Array.from(e.target.files);
    setFileQueue((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const toAdd = newFiles.filter((f) => !existingNames.has(f.name));
      return [...prev, ...toAdd];
    });
    // Reset input so same file can be re-added if removed
    e.target.value = '';
  };

  const removeFromQueue = (filename) => {
    setFileQueue((prev) => prev.filter((f) => f.name !== filename));
    setFileStatuses((prev) => {
      const next = { ...prev };
      delete next[filename];
      return next;
    });
  };

  const setStatus = (filename, type, message) => {
    setFileStatuses((prev) => ({ ...prev, [filename]: { type, message } }));
  };

  const handleUploadAll = async () => {
    if (fileQueue.length === 0 || isUploading) return;
    setIsUploading(true);

    for (const file of fileQueue) {
      setStatus(file.name, 'uploading', 'Parsing with Docling & extracting diagrams...');
      try {
        const result = await uploadPdf(file, sessionId);
        setStatus(
          file.name,
          'success',
          `Indexed ${result.total_chunks} chunks (${result.text_chunks} text/tables, ${result.image_chunks} diagrams)`,
        );
      } catch (err) {
        setStatus(file.name, 'error', err.message || 'Failed to upload and index.');
      }
    }

    setIsUploading(false);
    // Clear successfully uploaded files from queue, keep errored ones
    setFileQueue((prev) =>
      prev.filter((f) => fileStatuses[f.name]?.type === 'error'),
    );
    if (refreshDocs) refreshDocs();
    if (onUploadSuccess) onUploadSuccess();
  };

  const handleDelete = async (docName) => {
    if (deletingDoc) return;
    setDeletingDoc(docName);
    try {
      await deleteDocument(docName, sessionId);
      if (refreshDocs) refreshDocs();
    } catch (err) {
      alert(`Failed to delete: ${err.message}`);
    } finally {
      setDeletingDoc(null);
    }
  };

  const statusIcon = (type) => {
    if (type === 'uploading') return <Loader2 size={13} className="spin" style={{ color: 'var(--accent-cyan)' }} />;
    if (type === 'success') return <CheckCircle2 size={13} color="#10b981" />;
    if (type === 'error') return <AlertTriangle size={13} color="#f43f5e" />;
    return <FileText size={13} color="var(--text-dim)" />;
  };

  return (
    <aside className="sidebar">
      {/* ─── Upload Section ─── */}
      <div>
        <div className="section-label">Document Ingestion</div>

        {/* Drop zone / click to add files */}
        <div
          className="dropzone"
          onClick={() => fileInputRef.current?.click()}
          style={{ cursor: 'pointer' }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept={ALLOWED_EXTS}
            multiple
            style={{ display: 'none' }}
          />
          <div className="dropzone-icon"><UploadCloud size={20} /></div>
          <div className="dropzone-title">Add Documents</div>
          <div className="dropzone-subtitle">
            Click to select one or more files (PDF, Office, Code, Images…)
          </div>
        </div>

        {/* File Queue */}
        {fileQueue.length > 0 && (
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {fileQueue.map((file) => {
              const status = fileStatuses[file.name];
              return (
                <div
                  key={file.name}
                  style={{
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 8,
                    padding: '7px 10px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 8,
                  }}
                >
                  <div style={{ marginTop: 2 }}>{statusIcon(status?.type || 'pending')}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.78rem', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {file.name}
                    </div>
                    {status && (
                      <div style={{ fontSize: '0.7rem', color: status.type === 'error' ? '#f43f5e' : status.type === 'success' ? '#10b981' : 'var(--text-dim)', marginTop: 2 }}>
                        {status.message}
                      </div>
                    )}
                    {!status && (
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: 2 }}>
                        {(file.size / 1024 / 1024).toFixed(2)} MB — queued
                      </div>
                    )}
                  </div>
                  {(!status || status.type !== 'uploading') && (
                    <button
                      onClick={() => removeFromQueue(file.name)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: 'var(--text-dim)' }}
                      title="Remove from queue"
                    >
                      <X size={13} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Action buttons */}
        {fileQueue.length > 0 && (
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <button
              className="btn-upload"
              onClick={handleUploadAll}
              disabled={isUploading}
              style={{ flex: 1 }}
            >
              {isUploading ? (
                <><Loader2 size={14} className="spin" /><span>Parsing & Indexing…</span></>
              ) : (
                <><FilePlus2 size={14} /><span>Parse & Index {fileQueue.length > 1 ? `${fileQueue.length} Documents` : 'Document'}</span></>
              )}
            </button>
            {!isUploading && (
              <button
                onClick={() => { setFileQueue([]); setFileStatuses({}); }}
                style={{
                  background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)',
                  color: 'var(--text-dim)', borderRadius: 8, padding: '0 10px', cursor: 'pointer',
                  fontSize: '0.75rem',
                }}
                title="Clear queue"
              >
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* ─── Retrieval Controls ─── */}
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
              <option value={20}>Top 20</option>
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

      {/* ─── Indexed Documents ─── */}
      <div style={{ marginTop: 'auto' }}>
        <div className="section-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Indexed Documents</span>
          {indexedDocs && <span style={{ fontWeight: 400, color: 'var(--text-dim)' }}>{indexedDocs.length} doc{indexedDocs.length !== 1 ? 's' : ''}</span>}
        </div>
        <div style={{
          background: 'rgba(255,255,255,0.02)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}>
          {(!indexedDocs || indexedDocs.length === 0) ? (
            <div style={{ padding: 14, fontSize: '0.78rem', color: 'var(--text-dim)', textAlign: 'center' }}>
              No documents indexed yet.<br />Upload a file above to get started.
            </div>
          ) : (
            indexedDocs.map((doc) => (
              <div
                key={doc.doc_name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '9px 12px',
                  borderBottom: '1px solid var(--border-color)',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <FileText size={13} style={{ color: 'var(--accent-cyan)', flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {doc.doc_name}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: 1 }}>
                    {doc.chunk_count} chunks
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.doc_name)}
                  disabled={deletingDoc === doc.doc_name}
                  title={`Remove ${doc.doc_name}`}
                  style={{
                    background: 'none', border: 'none', cursor: deletingDoc === doc.doc_name ? 'not-allowed' : 'pointer',
                    padding: 3, color: 'var(--text-dim)', borderRadius: 4, display: 'flex', alignItems: 'center',
                    transition: 'color 0.15s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#f43f5e'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-dim)'}
                >
                  {deletingDoc === doc.doc_name
                    ? <Loader2 size={13} className="spin" />
                    : <Trash2 size={13} />}
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  );
}
