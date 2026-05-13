import { useState } from "react";
import ChatWindow from "../components/ChatWindow";
import DocumentRepository from "../components/DocumentRepository";
import SidebarFolders from "../components/SidebarFolders";
import UploadModal from "../components/UploadModal";
import MetadataModal from "../components/MetadataModal";
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
  const [activeTab, setActiveTab] = useState("main");
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isMetadataModalOpen, setIsMetadataModalOpen] = useState(false);

  // ── Retrieval Scope State (Phase 1: architecture only) ──
  const [scopeType, setScopeType] = useState("global");
  const [selectedFolderIds, setSelectedFolderIds] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);

  const handleUseDocument = async (document) => {
    setDocumentId(document.document_id);
    setDocumentName(document.file_name);
    setMetadataSuggestions(null);
    setDomainSuggestion(null);

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

  const handleUploadSuccess = (uploadData) => {
    setDocumentId(uploadData.document_id);
    setDocumentName(uploadData.file_name);
    setMetadataSuggestions(uploadData.metadata_suggestions);
    setDomainSuggestion(uploadData.domain_suggestion);
    setIsUploadModalOpen(false);
    
    // Show metadata modal if metadata was extracted
    if (uploadData.metadata_suggestions && !uploadData.is_duplicate) {
      setIsMetadataModalOpen(true);
    }
  };

  const handleMetadataSaved = () => {
    // Reset metadata review state after saving
    setMetadataSuggestions(null);
    setDomainSuggestion(null);
  };

  // ── Retrieval Scope Helpers (Phase 2: fixed) ──
  const toggleFolderSelection = (folderId) => {
    setSelectedFolderIds((prev) => {
      const next = prev.includes(folderId)
        ? prev.filter((id) => id !== folderId)
        : [...prev, folderId];
      // Only update scopeType when document selection is empty
      if (selectedDocumentIds.length === 0) {
        setScopeType(next.length > 0 ? "folders" : "global");
      }
      return next;
    });
  };

  const toggleDocumentSelection = (docId) => {
    setSelectedDocumentIds((prev) => {
      const next = prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId];
      // scopeType priority: documents > folders > global
      if (next.length > 0) {
        setScopeType("documents");
      } else if (selectedFolderIds.length > 0) {
        setScopeType("folders");
      } else {
        setScopeType("global");
      }
      return next;
    });
  };

  const getScopeLabel = () => {
    if (selectedDocumentIds.length > 0) {
      return `📄 Searching ${selectedDocumentIds.length} Document${selectedDocumentIds.length > 1 ? "s" : ""}`;
    }
    if (selectedFolderIds.length > 0) {
      return `📁 Searching ${selectedFolderIds.length} Folder${selectedFolderIds.length > 1 ? "s" : ""}`;
    }
    return "🌐 Searching All Documents";
  };

  const scopeLabel = getScopeLabel();

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
        <button className={activeTab === "main" ? "tab-button active" : "tab-button"} onClick={() => setActiveTab("main")}>
          Main
        </button>
        <button className={activeTab === "repo" ? "tab-button active" : "tab-button"} onClick={() => setActiveTab("repo")}>
          Repository
        </button>
      </nav>

      <section className="semantic-workspace" aria-label="Gold analyst workspace" hidden={activeTab !== "main"}>
        <SidebarFolders
          onSelectFolder={handleUseDocument}
          activeFolder={{ id: documentId }}
          selectedFolderIds={selectedFolderIds}
          onToggleFolderSelection={toggleFolderSelection}
        />
        <div className="workspace-chat-area">
          <ChatWindow
            key={documentId || "no-document"}
            documentId={documentId}
            documentName={documentName}
            onUploadClick={() => setIsUploadModalOpen(true)}
            onViewMetadata={() => setIsMetadataModalOpen(true)}
            scopeLabel={scopeLabel}
            selectedDocumentIds={selectedDocumentIds}
            onToggleDocumentSelection={toggleDocumentSelection}
          />
        </div>
      </section>

      <div hidden={activeTab !== "repo"}>
        <DocumentRepository
          activeDocumentId={documentId}
          onUseDocument={handleUseDocument}
          onDeleteDocument={handleDeleteDocument}
        />
      </div>

      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      <MetadataModal
        isOpen={isMetadataModalOpen}
        onClose={() => setIsMetadataModalOpen(false)}
        documentId={documentId}
        metadataSuggestions={metadataSuggestions}
        domainSuggestion={domainSuggestion}
        onMetadataSaved={handleMetadataSaved}
      />
    </main>
  );
}
