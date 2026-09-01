const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error(`Health check failed: ${response.statusText}`);
  return response.json();
}

export async function fetchDocuments(sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/documents`, {
    headers: sessionId ? { 'X-Session-ID': sessionId } : {},
  });
  if (!response.ok) throw new Error(`Failed to fetch documents: ${response.statusText}`);
  return response.json();
}

export async function deleteDocument(docName, sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(docName)}`, {
    method: 'DELETE',
    headers: sessionId ? { 'X-Session-ID': sessionId } : {},
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Delete failed with status ${response.status}`);
  }
  return response.json();
}

export async function sendQuery(query, topK = 10, excludeImages = false, sessionId = null) {
  const response = await fetch(`${API_BASE_URL}/api/query/agentic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query.trim(),
      top_k: topK,
      exclude_images: excludeImages,
      session_id: sessionId,
    }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Query failed with status ${response.status}`);
  }
  return response.json();
}

export async function uploadPdf(file, sessionId) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/ingest`, {
    method: 'POST',
    headers: sessionId ? { 'X-Session-ID': sessionId } : {},
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
  }
  return response.json();
}
