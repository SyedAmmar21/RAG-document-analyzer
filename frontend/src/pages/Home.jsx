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
  const [metadataDocumentId, setMetadataDocumentId] = useState(null);
  const [metadataSuggestions, setMetadataSuggestions] = useState(null);
  const [domainSuggestion, setDomainSuggestion] = useState(null);
  const [activeTab, setActiveTab] = useState("main");
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isMetadataModalOpen, setIsMetadataModalOpen] = useState(false);

  // ── Retrieval Scope State (Phase 1: architecture only) ──
  const [scopeType, setScopeType] = useState("global");
  const [selectedFolderIds, setSelectedFolderIds] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);

  const loadMetadataForDocument = async (docId) => {
    try {
      const res = await getDocumentMetadata(docId);
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

  const handleUseDocument = (document) => {
    setDocumentId(document.document_id);
  };

  const handleViewDocumentMetadata = (document) => {
    setMetadataDocumentId(document.document_id);
    setMetadataSuggestions(null);
    setDomainSuggestion(null);
    setIsMetadataModalOpen(true);
    loadMetadataForDocument(document.document_id);
  };

  const toggleDocumentSelection = (docId) => {
    setSelectedDocumentIds((prev) => {
      const next = prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId];

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

  const handleToggleScopedDocument = (document) => {
    toggleDocumentSelection(document.document_id);
    handleUseDocument(document);
  };

  const handleDeleteDocument = (deletedDocumentId) => {
    if (deletedDocumentId === documentId) {
      setDocumentId(null);
    }

    if (deletedDocumentId === metadataDocumentId) {
      setMetadataDocumentId(null);
      setMetadataSuggestions(null);
      setDomainSuggestion(null);
      setIsMetadataModalOpen(false);
    }

    setSelectedDocumentIds((prev) => {
      const next = prev.filter((id) => id !== deletedDocumentId);

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

  const handleUploadSuccess = (uploadData) => {
    setDocumentId(uploadData.document_id);
    setMetadataDocumentId(uploadData.document_id);
    setMetadataSuggestions(uploadData.metadata_suggestions);
    setDomainSuggestion(uploadData.domain_suggestion);
    setSelectedDocumentIds([uploadData.document_id]);
    setScopeType("documents");
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
              Query market notes, news, and reports across global, folder, or document-scoped research contexts.
            </p>
          </div>
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
          onSelectFolder={handleToggleScopedDocument}
          selectedFolderIds={selectedFolderIds}
          selectedDocumentIds={selectedDocumentIds}
          onToggleFolderSelection={toggleFolderSelection}
          onViewMetadata={handleViewDocumentMetadata}
        />
        <div className="workspace-chat-area">
          <ChatWindow
            documentId={documentId}
            onUploadClick={() => setIsUploadModalOpen(true)}
            scopeType={scopeType}
            scopeLabel={scopeLabel}
            
            selectedFolderIds={selectedFolderIds || []}
            selectedDocumentIds={selectedDocumentIds || []}

            onToggleDocumentSelection={toggleDocumentSelection}
            onToggleFolderSelection={toggleFolderSelection}
          />
        </div>
      </section>

      <div hidden={activeTab !== "repo"}>
        <DocumentRepository
          selectedDocumentIds={selectedDocumentIds}
          onUseDocument={handleToggleScopedDocument}
          onViewMetadata={handleViewDocumentMetadata}
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
        documentId={metadataDocumentId}
        metadataSuggestions={metadataSuggestions}
        domainSuggestion={domainSuggestion}
        onMetadataSaved={handleMetadataSaved}
      />
    </main>
  );
}
