import React, { useEffect, useRef } from 'react';
import { Send, Sparkles, BookOpen, Layers, Terminal } from 'lucide-react';
import { AnswerCard } from './AnswerCard';

const SAMPLE_SUGGESTIONS = [
  {
    tag: 'Exact Part Code',
    text: 'What is shaft seal type AQQx rated for?',
  },
  {
    tag: 'Technical Diagram',
    text: "What are the pump's standard mounting positions?",
  },
  {
    tag: 'Fault-Finding Table',
    text: 'What is the remedy if the pump runs but delivers no water?',
  },
  {
    tag: 'Safety & Procedures',
    text: 'What should I check regarding the direction of rotation before starting the pump?',
  },
];

export function ChatView({
  messages,
  currentQuery,
  setCurrentQuery,
  onSend,
  loading,
  error,
}) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <main className="chat-area">
      <div className="messages-stream">
        {messages.length === 0 ? (
          <div className="welcome-card">
            <div className="welcome-badge">
              <Sparkles size={14} />
              <span>Multimodal Retrieval-Augmented Generation</span>
            </div>
            <h2 className="welcome-title">Ask Any Technical Manual Question</h2>
            <p className="welcome-text">
              Grounded in exact PDF sections, tables, and wiring diagrams using Dense + BM25 Hybrid Search and Cross-Encoder Reranking.
            </p>

            <div className="section-label" style={{ textAlign: 'left', marginBottom: 12 }}>
              Try Example Questions:
            </div>
            <div className="suggestions-grid">
              {SAMPLE_SUGGESTIONS.map((item, i) => (
                <button
                  key={i}
                  className="suggestion-btn"
                  onClick={() => onSend(item.text)}
                >
                  <span className="suggestion-tag">{item.tag}</span>
                  <span>{item.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((item, idx) => <AnswerCard key={idx} item={item} />)
        )}

        {loading && (
          <div className="qa-block">
            <div className="loading-box">
              <div className="pulsing-spinner" />
              <span>Retrieving candidates from Qdrant, reranking with Cross-Encoder & generating grounded answer...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="qa-block">
            <div className="upload-status-card error">
              <strong>Query Error:</strong> {error}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Section */}
      <div className="input-section">
        <div className="input-bar-container">
          <input
            type="text"
            className="query-input"
            placeholder="Ask anything about the manual (e.g. pressure ratings, wiring schematics, mounting)..."
            value={currentQuery}
            onChange={(e) => setCurrentQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="btn-send"
            onClick={() => onSend()}
            disabled={loading || !currentQuery.trim()}
          >
            <Send size={16} />
          </button>
        </div>
        <div className="input-disclaimer">
          Answers are strictly grounded with citations [1], [2] to page numbers and figures in the manual.
        </div>
      </div>
    </main>
  );
}
