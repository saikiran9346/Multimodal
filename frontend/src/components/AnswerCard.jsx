import React, { useState } from 'react';
import { Bot, Table, Image as ImageIcon, FileText, ChevronDown, ChevronUp, Sparkles, BookOpen } from 'lucide-react';

export function AnswerCard({ item }) {
  const [expandedSources, setExpandedSources] = useState({});

  const toggleSource = (idx) => {
    setExpandedSources((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const renderAnswerWithCitations = (text) => {
    if (!text) return null;
    // Highlight inline citations like [1], [2], etc.
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      if (/^\[\d+\]$/.test(part)) {
        return (
          <span key={i} className="citation-badge-inline">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const getTypeBadge = (types = []) => {
    if (types.includes('picture')) {
      return (
        <span className="badge-type picture">
          <ImageIcon size={12} /> Figure / Diagram
        </span>
      );
    }
    if (types.includes('table')) {
      return (
        <span className="badge-type table">
          <Table size={12} /> Table Spec
        </span>
      );
    }
    return (
      <span className="badge-type text">
        <FileText size={12} /> Text
      </span>
    );
  };

  return (
    <div className="qa-block">
      {/* User Question Bubble */}
      <div className="user-question-row">
        <div className="user-question-bubble">
          {item.query}
        </div>
      </div>

      {/* Grounded Bot Answer Card */}
      <div className="bot-answer-row">
        <div className="bot-avatar">
          <Bot size={18} color="#fff" />
        </div>

        <div className="bot-answer-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
            <Sparkles size={14} color="#6366f1" />
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Grounded Technical Answer
            </span>
          </div>

          <div className="answer-body">
            {renderAnswerWithCitations(item.answer)}
          </div>

          {/* Sources Section */}
          {item.sources && item.sources.length > 0 && (
            <div>
              <div className="sources-header">
                <BookOpen size={14} />
                <span>Retrieved Evidence Sources ({item.sources.length})</span>
              </div>

              <div className="sources-list">
                {item.sources.map((s, idx) => {
                  const isExpanded = expandedSources[idx];
                  return (
                    <div key={idx} className="source-item">
                      <div className="source-meta">
                        <div className="source-left-meta">
                          <span className="badge-index">[{s.index || idx + 1}]</span>
                          {s.doc_name && (
                            <span className="badge-doc" style={{
                              background: 'rgba(255, 255, 255, 0.08)',
                              color: '#e5e7eb',
                              fontSize: '0.72rem',
                              fontWeight: 600,
                              padding: '2px 8px',
                              borderRadius: '12px',
                              maxWidth: '180px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              📄 {s.doc_name}
                            </span>
                          )}
                          {s.page_no !== null && s.page_no !== undefined ? (
                            <span className="badge-page">Page {s.page_no}</span>
                          ) : s.headings && s.headings.length > 0 ? (
                            <span className="badge-page" style={{ background: 'rgba(99, 102, 241, 0.18)', color: '#a5b4fc' }}>
                              {s.headings[0]}
                            </span>
                          ) : null}
                          {getTypeBadge(s.content_types)}
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          {s.score !== undefined && (
                            <span className="source-score">
                              Score: {s.score.toFixed(3)}
                            </span>
                          )}
                          <button
                            onClick={() => toggleSource(idx)}
                            style={{
                              background: 'transparent',
                              color: 'var(--text-dim)',
                              display: 'flex',
                              alignItems: 'center',
                              padding: 2,
                            }}
                          >
                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </button>
                        </div>
                      </div>

                      {s.headings && s.headings.length > 0 && (
                        <div className="source-headings">
                          {s.headings.join(' > ')}
                        </div>
                      )}

                      {s.text && (
                        <div className="source-snippet">
                          {isExpanded ? s.text : `${s.text.slice(0, 160)}...`}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
