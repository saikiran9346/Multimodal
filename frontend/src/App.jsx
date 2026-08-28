import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/ChatView';
import { fetchHealth, sendQuery } from './api';

export default function App() {
  const [health, setHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);
  const [messages, setMessages] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [excludeImages, setExcludeImages] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      setHealth({ status: 'unreachable', qdrant: 'disconnected' });
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentQuery('');
    setError(null);
  };

  const handleSend = async (customText) => {
    const textToSend = customText || currentQuery;
    if (!textToSend || !textToSend.trim() || loading) return;

    const queryStr = textToSend.trim();
    setCurrentQuery('');
    setError(null);
    setLoading(true);

    try {
      const response = await sendQuery(queryStr, topK, excludeImages);
      setMessages((prev) => [
        ...prev,
        {
          query: response.query,
          answer: response.answer,
          sources: response.sources || [],
        },
      ]);
    } catch (err) {
      setError(err.message || 'An error occurred while generating the answer.');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    checkHealth();
  };

  return (
    <div className="app-container">
      <Header
        health={health}
        isCheckingHealth={isCheckingHealth}
        onNewChat={handleNewChat}
        hasMessages={messages.length > 0}
      />
      <div className="main-workspace">
        <Sidebar
          topK={topK}
          setTopK={setTopK}
          excludeImages={excludeImages}
          setExcludeImages={setExcludeImages}
          onUploadSuccess={handleUploadSuccess}
        />
        <ChatView
          messages={messages}
          currentQuery={currentQuery}
          setCurrentQuery={setCurrentQuery}
          onSend={handleSend}
          loading={loading}
          error={error}
        />
      </div>
    </div>
  );
}
