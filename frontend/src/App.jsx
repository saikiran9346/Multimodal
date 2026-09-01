import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/ChatView';
import { fetchHealth, fetchDocuments, sendQuery } from './api';

function generateSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function makeSession() {
  const id = generateSessionId();
  return { id, sessionId: id, messages: [], currentQuery: '', error: null, docs: [] };
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(20);
  const [excludeImages, setExcludeImages] = useState(false);

  // ─── Sessions ─────────────────────────────────────────────────────
  const [sessions, setSessions] = useState([makeSession()]);
  const [activeIdx, setActiveIdx] = useState(0);

  const active = sessions[activeIdx] || sessions[0];

  const patchSession = useCallback((idx, patch) => {
    setSessions((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  }, []);

  // ─── Health ───────────────────────────────────────────────────────
  const checkHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setHealth({ status: 'unreachable', qdrant: 'disconnected' });
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const iv = setInterval(checkHealth, 15000);
    return () => clearInterval(iv);
  }, [checkHealth]);

  // ─── Docs per session ─────────────────────────────────────────────
  const refreshDocs = useCallback(async (sessionId, sessionIdx) => {
    try {
      const data = await fetchDocuments(sessionId);
      setSessions((prev) =>
        prev.map((s, i) => (i === sessionIdx ? { ...s, docs: data.documents || [] } : s)),
      );
    } catch { /* silently ignore */ }
  }, []);

  // Refresh docs when active session changes
  useEffect(() => {
    if (active?.sessionId !== undefined) {
      refreshDocs(active.sessionId, activeIdx);
    }
  }, [active?.sessionId, activeIdx, refreshDocs]);

  // ─── New Chat ──────────────────────────────────────────────────────
  const handleNewChat = () => {
    const newSession = makeSession();
    setSessions((prev) => {
      const next = [...prev, newSession];
      // Switch to the new tab
      setActiveIdx(next.length - 1);
      return next;
    });
  };

  // ─── Close a chat tab ─────────────────────────────────────────────
  const handleCloseSession = (idx) => {
    setSessions((prev) => {
      if (prev.length === 1) return prev; // Never close the last session
      const next = prev.filter((_, i) => i !== idx);
      // Adjust activeIdx
      setActiveIdx((prevIdx) => {
        if (prevIdx === idx) return Math.max(0, idx - 1);
        if (prevIdx > idx) return prevIdx - 1;
        return prevIdx;
      });
      return next;
    });
  };

  // ─── Send Query ────────────────────────────────────────────────────
  const handleSend = async (customText) => {
    const textToSend = customText || active.currentQuery;
    if (!textToSend?.trim() || loading) return;

    const queryStr = textToSend.trim();
    patchSession(activeIdx, { currentQuery: '', error: null });
    setLoading(true);

    try {
      const response = await sendQuery(queryStr, topK, excludeImages, active.sessionId);
      setSessions((prev) =>
        prev.map((s, i) =>
          i === activeIdx
            ? {
                ...s,
                messages: [
                  ...s.messages,
                  {
                    query: response.query,
                    answer: response.answer,
                    sources: response.sources || [],
                    critique_log: response.critique_log || [],
                    attempts: response.attempts || 1,
                    final_query: response.final_query || response.query,
                  },
                ],
              }
            : s,
        ),
      );
    } catch (err) {
      patchSession(activeIdx, { error: err.message || 'An error occurred.' });
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    checkHealth();
    refreshDocs(active.sessionId, activeIdx);
  };

  const setCurrentQuery = (val) => patchSession(activeIdx, { currentQuery: val });

  return (
    <div className="app-container">
      <Header
        health={health}
        isCheckingHealth={isCheckingHealth}
        onNewChat={handleNewChat}
        sessions={sessions}
        activeSessionIdx={activeIdx}
        onSwitchSession={setActiveIdx}
        onCloseSession={handleCloseSession}
      />
      <div className="main-workspace">
        <Sidebar
          topK={topK}
          setTopK={setTopK}
          excludeImages={excludeImages}
          setExcludeImages={setExcludeImages}
          onUploadSuccess={handleUploadSuccess}
          indexedDocs={active.docs}
          refreshDocs={() => refreshDocs(active.sessionId, activeIdx)}
          sessionId={active.sessionId}
        />
        <ChatView
          messages={active.messages}
          currentQuery={active.currentQuery}
          setCurrentQuery={setCurrentQuery}
          onSend={handleSend}
          loading={loading}
          error={active.error}
        />
      </div>
    </div>
  );
}
