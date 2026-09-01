import React from 'react';
import { BookOpen, Database, Cpu, Plus, MessageSquare, X } from 'lucide-react';

export function Header({
  health,
  isCheckingHealth,
  onNewChat,
  sessions,
  activeSessionIdx,
  onSwitchSession,
  onCloseSession,
}) {
  const isHealthy = health?.status === 'healthy' && health?.qdrant === 'connected';

  return (
    <header className="app-header" style={{ flexDirection: 'column', gap: 0, padding: 0 }}>
      {/* ── Top bar ── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 24px', width: '100%', boxSizing: 'border-box',
        borderBottom: '1px solid var(--border-color)',
      }}>
        <div className="brand-section">
          <div className="brand-logo-badge">
            <BookOpen size={20} color="#fff" />
          </div>
          <div>
            <h1 className="brand-title">Multimodal Technical Manual RAG</h1>
            <p className="brand-subtitle">Dense + BM25 Hybrid Retrieval • Cross-Encoder Reranker • Groq LLM Citations</p>
          </div>
        </div>

        <div className="header-status-pills">
          <div className="status-pill">
            <Cpu size={14} color="#9ca3af" />
            <span>FastAPI</span>
            <span className={`status-dot ${isHealthy ? 'green' : 'red'}`} />
          </div>
          <div className="status-pill">
            <Database size={14} color="#9ca3af" />
            <span>Qdrant</span>
            <span className={`status-dot ${health?.qdrant === 'connected' ? 'green' : 'yellow'}`} />
            {health?.indexed_chunks !== undefined && (
              <strong style={{ color: '#a5b4fc', marginLeft: 4 }}>
                ({health.indexed_chunks} chunks)
              </strong>
            )}
          </div>
        </div>
      </div>

      {/* ── Chat tabs bar ── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: '0 16px',
        background: 'rgba(0,0,0,0.2)',
        borderBottom: '1px solid var(--border-color)',
        overflowX: 'auto',
        scrollbarWidth: 'none',
        minHeight: 40,
      }}>
        {sessions.map((session, idx) => {
          const isActive = idx === activeSessionIdx;
          const label = session.messages.length > 0
            ? (session.messages[0].query.slice(0, 28) + (session.messages[0].query.length > 28 ? '…' : ''))
            : `Chat ${idx + 1}`;

          return (
            <div
              key={session.id}
              onClick={() => onSwitchSession(idx)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 12px',
                borderRadius: '6px 6px 0 0',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? '#e2e8f0' : 'var(--text-dim)',
                background: isActive
                  ? 'rgba(99,102,241,0.15)'
                  : 'transparent',
                borderBottom: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
                flexShrink: 0,
              }}
              onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.color = '#e2e8f0'; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.color = 'var(--text-dim)'; }}
            >
              <MessageSquare size={12} />
              <span>{label}</span>
              {/* Close tab — only show if more than 1 session */}
              {sessions.length > 1 && (
                <span
                  onClick={(e) => { e.stopPropagation(); onCloseSession(idx); }}
                  style={{
                    marginLeft: 2,
                    display: 'flex',
                    alignItems: 'center',
                    color: 'var(--text-dim)',
                    borderRadius: 3,
                    padding: 1,
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#f43f5e'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-dim)'}
                  title="Close this chat"
                >
                  <X size={11} />
                </span>
              )}
            </div>
          );
        })}

        {/* New Chat button as a tab */}
        <button
          onClick={onNewChat}
          title="Start a new chat with its own document workspace"
          style={{
            display: 'flex', alignItems: 'center', gap: 5,
            background: 'none', border: '1px dashed var(--border-color)',
            color: 'var(--text-dim)', borderRadius: 6, padding: '4px 10px',
            cursor: 'pointer', fontSize: '0.75rem', flexShrink: 0,
            transition: 'all 0.15s', marginLeft: 4,
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--accent-primary)'; e.currentTarget.style.color = '#e2e8f0'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.color = 'var(--text-dim)'; }}
        >
          <Plus size={12} />
          <span>New Chat</span>
        </button>
      </div>
    </header>
  );
}
