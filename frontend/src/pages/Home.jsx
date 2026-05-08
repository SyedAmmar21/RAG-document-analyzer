import { useState } from "react";
import FileUpload from "../components/FileUpload";
import FieldSearch from "../components/FieldSearch";
import ChatWindow from "../components/ChatWindow";
import DocumentRepository from "../components/DocumentRepository";
import { getDocumentMetadata } from "../services/api";

function rowsToMetadataSuggestions(rows) {
  const metadata = {
    title: null,
    published_date: null,
    focus: null,
    entities: [],
    economic_indicators: [],
    regions: [],
    saved: true,
  };

  rows.forEach((row) => {
    if (["entities", "economic_indicators", "regions"].includes(row.field)) {
      if (row.value) {
        metadata[row.field].push(row.value);
      }
      return;
    }

    if (row.field in metadata && row.value) {
      metadata[row.field] = row.value;
    }
  });

  return metadata;
}

export default function Home() {
  const [documentId, setDocumentId] = useState(null);
  const [documentName, setDocumentName] = useState("");
  const [metadataSuggestions, setMetadataSuggestions] = useState(null);
  const [domainSuggestion, setDomainSuggestion] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");

  const handleUseDocument = async (document) => {
    setDocumentId(document.document_id);
    setDocumentName(document.file_name);
    setMetadataSuggestions(null);
    setDomainSuggestion(null);
    setActiveTab("chat");

    try {
      const res = await getDocumentMetadata(document.document_id);
      setMetadataSuggestions(rowsToMetadataSuggestions(res.metadata || []));
      setDomainSuggestion(res.domain || null);
    } catch {
      setMetadataSuggestions({
        title: null,
        published_date: null,
        focus: null,
        entities: [],
        economic_indicators: [],
        regions: [],
        saved: true,
      });
      setDomainSuggestion(null);
    }
  };

  const handleDeleteDocument = (deletedDocumentId) => {
    if (deletedDocumentId === documentId) {
      setDocumentId(null);
      setDocumentName("");
      setMetadataSuggestions(null);
      setDomainSuggestion(null);
    }
  };

  return (
    <main className="app-shell">
      <section className="hero-panel" aria-labelledby="page-title">
        <div className="hero-title-row">
          <img className="hero-symbol" src="/RAGsymbol.png" alt="" aria-hidden="true" />
          <div>
            <p className="eyebrow">Gold market intelligence workspace</p>
            <h1 id="page-title">Gold Analyst Helper</h1>
            <p className="hero-copy">
              Upload market notes, news, or reports, then extract metadata and ask grounded gold-analysis questions.
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

      <section className="workspace-grid" aria-label="Gold analyst workspace" hidden={activeTab !== "chat"}>
        <div className="document-column">
          <FileUpload
            setDocumentId={setDocumentId}
            setDocumentName={setDocumentName}
            setMetadataSuggestions={setMetadataSuggestions}
            setDomainSuggestion={setDomainSuggestion}
            documentName={documentName}
            isReady={Boolean(documentId)}
          />
          <FieldSearch
            key={documentId || "no-document"}
            documentId={documentId}
            metadataSuggestions={metadataSuggestions}
            domainSuggestion={domainSuggestion}
            onMetadataSaved={() => setMetadataSuggestions(null)}
          />
        </div>
        <ChatWindow key={documentId || "no-document"} documentId={documentId} documentName={documentName} />
      </section>
    </main>
  );
}
