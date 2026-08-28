import React from 'react';
import { BookOpen, Database, Cpu, Plus } from 'lucide-react';

export function Header({ health, isCheckingHealth, onNewChat, hasMessages }) {
  const isHealthy = health?.status === 'healthy' && health?.qdrant === 'connected';

  return (
    <header className="app-header">
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
        {hasMessages && (
          <button className="btn-new-chat" onClick={onNewChat} title="Start a fresh conversation">
            <Plus size={15} />
            <span>New Chat</span>
          </button>
        )}

        <div className="status-pill">
          <Cpu size={14} color="#9ca3af" />
          <span>FastAPI</span>
          <span className={`status-dot ${isHealthy ? 'green' : 'red'}`} />
        </div>

        <div className="status-pill">
          <Database size={14} color="#9ca3af" />
          <span>Qdrant Vector DB</span>
          <span className={`status-dot ${health?.qdrant === 'connected' ? 'green' : 'yellow'}`} />
          {health?.indexed_chunks !== undefined && (
            <strong style={{ color: '#a5b4fc', marginLeft: 4 }}>
              ({health.indexed_chunks} chunks)
            </strong>
          )}
        </div>
      </div>
    </header>
  );
}
