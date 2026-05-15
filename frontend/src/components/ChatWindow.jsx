import { useState } from "react";
import { queryAgent } from "../services/api";
import MarkdownMessage from "./MarkdownMessage";

export default function ChatWindow({
  documentId,
  onUploadClick,
  scopeType,
  scopeLabel,
  selectedFolderIds = [],
  selectedDocumentIds = [],
  onToggleFolderSelection,
  onToggleDocumentSelection,
}) {
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
        document_id: documentId,
        scope_type: scopeType,
        folder_ids: selectedFolderIds,
        document_ids: selectedDocumentIds,
      });

      setMessages((currentMessages) => [
        ...currentMessages,
        { role: "ai", text: res.answer || "I could not find an answer in the selected workspace context." },
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
          <p className="section-kicker">Workspace Assistant</p>
          <h2 id="chat-title">Ask across your knowledge base</h2>
        </div>
      </div>

      <div className="scope-header">
        <span className="scope-badge">{scopeLabel}</span>
        {selectedDocumentIds.length > 0 && (
          <div className="scope-chips">
            {selectedDocumentIds.slice(0, 3).map((id) => (
              <span key={id} className="scope-chip" title={`Document: ${id}`}>
                Doc {id.slice(0, 10)}...
                <button
                  className="chip-remove"
                  onClick={() => onToggleDocumentSelection(id)}
                  type="button"
                  title="Remove from scope"
                  aria-label="Remove document"
                >
                  x
                </button>
              </span>
            ))}
            {selectedDocumentIds.length > 3 && (
              <span className="scope-chip">+{selectedDocumentIds.length - 3} more</span>
            )}
          </div>
        )}
        {selectedFolderIds.length > 0 && (
          <div className="scope-chips">
            {selectedFolderIds.slice(0, 3).map((id) => (
              <span key={id} className="scope-chip scope-chip-folder" title={`Folder: ${id}`}>
                Folder {String(id).slice(0, 12)}...
                <button
                  className="chip-remove"
                  onClick={() => onToggleFolderSelection?.(id)}
                  type="button"
                  title="Remove from scope"
                  aria-label="Remove folder"
                >
                  x
                </button>
              </span>
            ))}
            {selectedFolderIds.length > 3 && (
              <span className="scope-chip">+{selectedFolderIds.length - 3} more</span>
            )}
          </div>
        )}
      </div>

      <div className="messages" aria-live="polite">
        {messages.length === 0 ? (
          <div className="empty-state">
            <strong>No analyst questions yet</strong>
            <span>Ask about gold drivers, central-bank signals, macro risks, or compare selected documents.</span>
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
            <p>Searching the selected workspace context...</p>
          </div>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="composer">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask across the workspace, selected folders, or selected documents..."
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
            +
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
