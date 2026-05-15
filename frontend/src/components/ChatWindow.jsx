import { useState } from "react";
import { queryAgent } from "../services/api";
import MarkdownMessage from "./MarkdownMessage";

export default function ChatWindow({ documentId, documentName, onUploadClick, onViewMetadata, scopeType, scopeLabel, selectedFolderIds = [], selectedDocumentIds = [], onToggleFolderSelection, onToggleDocumentSelection }) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) return;

    const userMessage = { role: "user", text: trimmedQuery };
    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setQuery("");
    setError("");
    setIsSending(true);

    try {
      const res = await queryAgent({
       query: trimmedQuery,

       // temporary compatibility
       document_id: documentId,

       // NEW retrieval scope architecture
       scope_type: scopeType,

       folder_ids: selectedFolderIds,
       document_ids:   
        selectedDocumentIds.length > 0
          ? selectedDocumentIds
          : documentId
          ? [documentId]
          : [],
      });

      setMessages((currentMessages) => [
        ...currentMessages,
        { role: "ai", text: res.answer || "I could not find an answer in this document." },
      ]);
    } catch (error) {
      setError(error.message || "The assistant could not answer right now.");
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">Hello User!</p>
          <h2 id="chat-title">Ask the analyst</h2>
        </div>
        <span className={documentId ? "badge success" : "badge"}>{documentId ? "Enabled" : "Locked"}</span>
      </div>

      {/* ── Retrieval Scope Header (Phase 1) ── */}
      <div className="scope-header">
        <span className="scope-badge">{scopeLabel}</span>
        {selectedDocumentIds.length > 0 && (
          <div className="scope-chips">
            {selectedDocumentIds.slice(0, 3).map((id) => (
              <span key={id} className="scope-chip" title={`Document: ${id}`}>
                📄 {id.slice(0, 10)}…
                <button
                  className="chip-remove"
                  onClick={() => onToggleDocumentSelection(id)}
                  type="button"
                  title="Remove from scope"
                  aria-label="Remove document"
                >
                  ✕
                </button>
              </span>
            ))}
            {selectedDocumentIds.length > 3 && (
              <span className="scope-chip" style={{ background: 'rgba(214, 168, 61, 0.15)', borderColor: 'rgba(214, 168, 61, 0.25)' }}>
                +{selectedDocumentIds.length - 3} more
              </span>
            )}
          </div>
        )}
        {selectedFolderIds.length > 0 && (
          <div className="scope-chips">
            {selectedFolderIds.slice(0, 3).map((id) => (
              <span key={id} className="scope-chip scope-chip-folder" title={`Folder: ${id}`}>
                📁 {String(id).slice(0, 12)}…
                <button
                  className="chip-remove"
                  onClick={() => onToggleFolderSelection(id)}
                  type="button"
                  title="Remove from scope"
                  aria-label="Remove folder"
                >
                  ✕
                </button>
              </span>
            ))}
            {selectedFolderIds.length > 3 && (
              <span className="scope-chip" style={{ background: 'rgba(116, 210, 162, 0.15)', borderColor: 'rgba(116, 210, 162, 0.25)' }}>
                +{selectedFolderIds.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>

      <div className={documentId ? "chat-context active-source-banner" : "chat-context"}>
        {documentId ? (
          <>
            <div className="source-info">
              <span>Active source</span>
              <strong>{documentName || "Uploaded document"}</strong>
            </div>
            <button
              className="icon-button metadata-button"
              onClick={onViewMetadata}
              title="View document metadata"
              aria-label="View document metadata"
              type="button"
            >
              📋
            </button>
          </>
        ) : (
          "Upload or choose a market document to start a grounded gold-analysis conversation."
        )}
      </div>

      <div className="messages" aria-live="polite">
        {messages.length === 0 ? (
          <div className="empty-state">
            <strong>No analyst questions yet</strong>
            <span>Ask about gold drivers, central-bank signals, macro risks, or market implications.</span>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div className={`message ${msg.role}`} key={`${msg.role}-${i}`}>
              <span className="message-label">{msg.role === "ai" ? "Assistant" : "You"}</span>
              {msg.role === "ai" ? <MarkdownMessage text={msg.text} /> : <p>{msg.text}</p>}
            </div>
          ))
        )}

        {isSending && (
          <div className="message ai pending">
            <span className="message-label">Assistant</span>
            <p>Reviewing the market document...</p>
          </div>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}

<div className="composer">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about gold's status today, gold drivers, or market risks..."
          disabled={isSending}
          rows="3"
        />
        <div className="character-counter">
          {query.length}/255
        </div>
        <div className="composer-actions">
          <button
            className="icon-button upload-button"
            onClick={onUploadClick}
            title="Attach document"
            aria-label="Attach document"
            type="button"
          >
            📎
          </button>
          <button
            className="primary-button"
            onClick={handleSend}
            disabled={isSending || !query.trim()}
          >
            {isSending ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
    </section>
  );
}