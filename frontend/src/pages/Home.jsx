import { useState } from "react";
import FileUpload from "../components/FileUpload";
import FieldSearch from "../components/FieldSearch";
import ChatWindow from "../components/ChatWindow";
import DocumentRepository from "../components/DocumentRepository";

export default function Home() {
  const [documentId, setDocumentId] = useState(null);
  const [documentName, setDocumentName] = useState("");
  const [metadataSuggestions, setMetadataSuggestions] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");

  const handleUseDocument = (document) => {
    setDocumentId(document.document_id);
    setDocumentName(document.file_name);
    setMetadataSuggestions(null);
    setActiveTab("chat");
  };

  const handleDeleteDocument = (deletedDocumentId) => {
    if (deletedDocumentId === documentId) {
      setDocumentId(null);
      setDocumentName("");
      setMetadataSuggestions(null);
    }
  };

  return (
    <main className="app-shell">
      <section className="hero-panel" aria-labelledby="page-title">
        <div className="hero-title-row">
          <img className="hero-symbol" src="/RAGsymbol.png" alt="" aria-hidden="true" />
          <div>
            <p className="eyebrow">Document intelligence workspace</p>
            <h1 id="page-title">Your RAG Assistant</h1>
            <p className="hero-copy">
              Upload a document, then ask precise questions and get answers grounded in that file.
            </p>
          </div>
        </div>

        <div className={documentId ? "status-pill ready" : "status-pill"}>
          <span aria-hidden="true" />
          {documentId ? "Document ready" : "Awaiting upload"}
        </div>
      </section>

      <nav className="tab-list" aria-label="Primary workspace tabs">
        <button className={activeTab === "chat" ? "tab-button active" : "tab-button"} onClick={() => setActiveTab("chat")}>
          Chat
        </button>
        <button className={activeTab === "repo" ? "tab-button active" : "tab-button"} onClick={() => setActiveTab("repo")}>
          Repository
        </button>
      </nav>

      <div hidden={activeTab !== "repo"}>
        <DocumentRepository
          activeDocumentId={documentId}
          onUseDocument={handleUseDocument}
          onDeleteDocument={handleDeleteDocument}
        />
      </div>

      <section className="workspace-grid" aria-label="RAG assistant workspace" hidden={activeTab !== "chat"}>
        <div className="document-column">
          <FileUpload
            setDocumentId={setDocumentId}
            setDocumentName={setDocumentName}
            setMetadataSuggestions={setMetadataSuggestions}
            documentName={documentName}
            isReady={Boolean(documentId)}
          />
          <FieldSearch
            key={documentId || "no-document"}
            documentId={documentId}
            metadataSuggestions={metadataSuggestions}
            onMetadataSaved={() => setMetadataSuggestions(null)}
          />
        </div>
        <ChatWindow key={documentId || "no-document"} documentId={documentId} documentName={documentName} />
      </section>
    </main>
  );
}
