import { useState } from "react";
import { queryAgent } from "../services/api";
import MarkdownMessage from "./MarkdownMessage";

export default function ChatWindow({ documentId, documentName }) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) return;

    if (!documentId) {
      setError("Upload a document first so the assistant has a source.");
      return;
    }

    const userMessage = { role: "user", text: trimmedQuery };
    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setQuery("");
    setError("");
    setIsSending(true);

    try {
      const res = await queryAgent(trimmedQuery, documentId);
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
          <p className="section-kicker">Step 2</p>
          <h2 id="chat-title">Ask the analyst</h2>
        </div>
        <span className={documentId ? "badge success" : "badge"}>{documentId ? "Enabled" : "Locked"}</span>
      </div>

      <div className={documentId ? "chat-context active-source-banner" : "chat-context"}>
        {documentId ? (
          <>
            <span>Active source</span>
            <strong>{documentName || "Uploaded document"}</strong>
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
          placeholder="Ask about gold drivers, macro signals, or market risks..."
          disabled={!documentId || isSending}
          rows="3"
        />
        <button className="primary-button" onClick={handleSend} disabled={!documentId || isSending || !query.trim()}>
          {isSending ? "Sending..." : "Send"}
        </button>
      </div>
    </section>
  );
}
