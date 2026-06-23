import { useState } from "react";
import { ingestLatestGoldNews, queryAgent } from "../services/api";
import MarkdownMessage from "./MarkdownMessage";

// Helper component for news modal list items
export function NewsModalListItems({ articles, className, pillLabel, pillClass, detailField }) {
  return articles.map((article, index) => (
    <div className={`news-summary-row ${className}`} key={article.document_id || `${article.url || article.title}-${index}`}>
      <div>
        <strong>{article.title}</strong>
        <span>{article[detailField] || (detailField === "reason" ? "Duplicate article skipped." : "No domain assigned")}</span>
      </div>
      <span className={pillClass}>{pillLabel}</span>
    </div>
  ));
}

export default function ChatWindow({
  documentId,
  onUploadClick,
  scopeType,
  scopeLabel,
  selectedFolderIds = [],
  selectedDocumentIds = [],
  onToggleFolderSelection,
  onToggleDocumentSelection,
  onNewsIngestComplete,
}) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isIngestingNews, setIsIngestingNews] = useState(false);
  const [newsProgress, setNewsProgress] = useState([]);
  const [newsSummary, setNewsSummary] = useState(null);
  const [threadId] = useState(() => crypto.randomUUID());

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
        thread_id: threadId,
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

  const handleIngestLatestNews = async () => {
    setError("");
    setNewsSummary(null);
    setNewsProgress([
      {
        title: "Searching latest gold news",
        status: "processing",
        success: null,
      },
    ]);
    setIsIngestingNews(true);

    try {
      const res = await ingestLatestGoldNews();
      const processed = res.processed || [];
      const failed = res.failed || [];
      const skipped = res.skipped || [];

      setNewsProgress([
        ...processed.map((article) => ({
          ...article,
          status: "processed",
          success: true,
        })),
        ...skipped.map((article) => ({
          ...article,
          status: "skipped",
          success: true,
        })),
        ...failed.map((article) => ({
          ...article,
          status: "failed",
          success: false,
        })),
      ]);
      setNewsSummary(res);
      onNewsIngestComplete?.(res);
    } catch (error) {
      setError(error.message || "Could not download the latest gold news.");
      setNewsProgress([
        {
          title: "Latest gold news ingestion",
          status: "failed",
          success: false,
          error: error.message || "Request failed.",
        },
      ]);
    } finally {
      setIsIngestingNews(false);
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

      <div className="news-ingestion-panel" aria-live="polite">
        <button
          className="secondary-button news-ingestion-button"
          type="button"
          onClick={handleIngestLatestNews}
          disabled={isIngestingNews}
        >
          {isIngestingNews && <span className="spinner small-spinner" />}
          {isIngestingNews ? "Downloading latest gold news..." : "Download Latest Gold News"}
        </button>

        {newsProgress.length > 0 && (
          <div className="news-progress-list">
            {newsProgress.slice(0, 10).map((item, index) => (
              <div
                className={`news-progress-item ${item.success === false ? "failed" : ""}`}
                key={`${item.title}-${index}`}
              >
                <span className="news-progress-status">
                  {item.success === false
                    ? "Failed"
                    : item.status === "processing"
                      ? "Processing"
                      : item.status === "skipped"
                        ? "Skipped"
                        : "Processed"}
                </span>
                <span className="news-progress-title">{item.title}</span>
                {item.domain && <span className="news-progress-domain">{item.domain}</span>}
              </div>
            ))}
          </div>
        )}
      </div>

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

      {newsSummary && (
        <div className="modal-overlay">
          <div className="news-summary-modal" role="dialog" aria-modal="true" aria-labelledby="news-summary-title">
            <div className="modal-header">
              <div>
                <p className="section-kicker">Autonomous ingestion</p>
                <h2 id="news-summary-title">Gold News Download Complete</h2>
              </div>
              <button
                className="close-button"
                onClick={() => setNewsSummary(null)}
                aria-label="Close news ingestion summary"
                type="button"
              >
                x
              </button>
            </div>

            <p className="news-summary-counts">
              {newsSummary.total_processed || 0} processed, {newsSummary.total_skipped || 0} skipped, {newsSummary.total_failed || 0} failed
            </p>

            <div className="news-summary-list">
              <NewsModalListItems
                articles={newsSummary.processed || []}
                className=""
                pillLabel="Processed"
                pillClass="success-pill"
                detailField="domain"
              />
              <NewsModalListItems
                articles={newsSummary.skipped || []}
                className="skipped"
                pillLabel="Skipped"
                pillClass="skipped-pill"
                detailField="reason"
              />
              <NewsModalListItems
                articles={newsSummary.failed || []}
                className="failed"
                pillLabel="Failed"
                pillClass="failure-pill"
                detailField="error"
              />
            </div>

            <div className="modal-actions">
              <button className="primary-button" type="button" onClick={() => setNewsSummary(null)}>
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
