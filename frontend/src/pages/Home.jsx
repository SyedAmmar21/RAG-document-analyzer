import { useState, useEffect } from "react";
import ChatWindow, { NewsModalListItems } from "../components/ChatWindow";
import DocumentRepository from "../components/DocumentRepository";
import FoldersView from "../components/FoldersView";
import OutputsView from "../components/OutputsView";
import SidebarFolders from "../components/SidebarFolders";
import UploadModal from "../components/UploadModal";
import MetadataModal from "../components/MetadataModal";
import DuplicateAlert from "../components/DuplicateAlert";
import { getDocumentMetadata, getScheduledIngestionSummary } from "../services/api";

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
  const [duplicateDocument, setDuplicateDocument] = useState(null);
  const [workspaceRefreshKey, setWorkspaceRefreshKey] = useState(0);
  const [outputRefreshKey, setOutputRefreshKey] = useState(0);
  const [chatThreadId] = useState(() => crypto.randomUUID());

  // ── Retrieval Scope State (Phase 1: architecture only) ──
  const [scopeType, setScopeType] = useState("global");
  const [selectedFolderIds, setSelectedFolderIds] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);

  // ── Scheduled Ingestion Auto-Detection State ──
  const [scheduledNewsSummary, setScheduledNewsSummary] = useState(null);

  // Poll backend every 30s for completed scheduled ingestion
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const summary = await getScheduledIngestionSummary();
        // If summary has data, a scheduled run just completed
        if (summary && (summary.total_processed > 0 || summary.total_failed > 0 || summary.total_skipped > 0 || summary.error)) {
          setScheduledNewsSummary(summary);
          // Auto-refresh document list to show new articles
          setWorkspaceRefreshKey((k) => k + 1);
        }
      } catch {
        // Ignore polling errors — silent fail
      }
    }, 30000);

    return () => clearInterval(pollInterval);
  }, []);

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

  const handleFolderDeleted = (deletedFolderId) => {
    setSelectedFolderIds((prev) => {
      const next = prev.filter((id) => String(id) !== String(deletedFolderId));

      if (next.length === 0 && selectedDocumentIds.length === 0) {
        setScopeType("global");
      }

      return next;
    });
    setWorkspaceRefreshKey((currentKey) => currentKey + 1);
  };

  const handleFolderChanged = () => {
    setWorkspaceRefreshKey((currentKey) => currentKey + 1);
  };

  const handleUploadSuccess = (uploadData) => {
    setDocumentId(uploadData.document_id);
    setMetadataDocumentId(uploadData.document_id);
    setMetadataSuggestions(uploadData.metadata_suggestions);
    setDomainSuggestion(uploadData.domain_suggestion);
    setSelectedDocumentIds([uploadData.document_id]);
    setScopeType("documents");
    setIsUploadModalOpen(false);

    if (uploadData.is_duplicate) {
      setIsMetadataModalOpen(false);
      setDuplicateDocument({
        fileName: uploadData.file_name,
        documentNumber: uploadData.document_number,
      });
      return;
    }
    
    // Show metadata modal if metadata was extracted
    if (uploadData.metadata_suggestions) {
      setIsMetadataModalOpen(true);
    }
  };

  const handleNewsIngestComplete = (result) => {
    const processedIds = (result.processed || [])
      .map((article) => article.document_id)
      .filter(Boolean);

    if (processedIds.length > 0) {
      setDocumentId(processedIds[0]);
      setSelectedDocumentIds(processedIds);
      setScopeType("documents");
    }

    setWorkspaceRefreshKey((currentKey) => currentKey + 1);
  };

  const handleMetadataSaved = () => {
    // Reset metadata review state after saving
    setMetadataSuggestions(null);
    setDomainSuggestion(null);
  };

  const handleOutputsChanged = () => {
    setOutputRefreshKey((currentKey) => currentKey + 1);
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
        <button className={activeTab === "folders" ? "tab-button active" : "tab-button"} onClick={() => setActiveTab("folders")}>
          Folders
        </button>
        <button className={activeTab === "outputs" ? "tab-button active" : "tab-button"} onClick={() => setActiveTab("outputs")}>
          Outputs
        </button>
      </nav>

      <section className="semantic-workspace" aria-label="Gold analyst workspace" hidden={activeTab !== "main"}>
        <SidebarFolders
          key={`folders-${workspaceRefreshKey}`}
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
            onNewsIngestComplete={handleNewsIngestComplete}
            scopeType={scopeType}
            scopeLabel={scopeLabel}
            
            selectedFolderIds={selectedFolderIds || []}
            selectedDocumentIds={selectedDocumentIds || []}

            onToggleDocumentSelection={toggleDocumentSelection}
            onToggleFolderSelection={toggleFolderSelection}
            onOutputsChanged={handleOutputsChanged}
            threadId={chatThreadId}
          />
        </div>
      </section>

      <div hidden={activeTab !== "repo"}>
        <DocumentRepository
          key={`repository-${workspaceRefreshKey}`}
          selectedDocumentIds={selectedDocumentIds}
          onUseDocument={handleToggleScopedDocument}
          onViewMetadata={handleViewDocumentMetadata}
          onDeleteDocument={handleDeleteDocument}
        />
      </div>

      <div hidden={activeTab !== "folders"}>
        <FoldersView
          key={`folders-view-${workspaceRefreshKey}`}
          onUseDocument={handleToggleScopedDocument}
          onFolderChanged={handleFolderChanged}
          onFolderDeleted={handleFolderDeleted}
        />
      </div>

      <div hidden={activeTab !== "outputs"}>
        <OutputsView key={`outputs-${outputRefreshKey}`} threadId={chatThreadId} />
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

      <DuplicateAlert
        isOpen={Boolean(duplicateDocument)}
        onClose={() => setDuplicateDocument(null)}
        fileName={duplicateDocument?.fileName}
        documentNumber={duplicateDocument?.documentNumber}
      />

      {/* Scheduled ingestion summary modal — reuses ChatWindow's NewsModalListItems */}
      {scheduledNewsSummary && (
        <div className="modal-overlay">
          <div className="news-summary-modal" role="dialog" aria-modal="true" aria-labelledby="scheduled-news-summary-title">
            <div className="modal-header">
              <div>
                <p className="section-kicker">Scheduled ingestion</p>
                <h2 id="scheduled-news-summary-title">Gold News Download Complete</h2>
              </div>
              <button
                className="close-button"
                onClick={() => setScheduledNewsSummary(null)}
                aria-label="Close news ingestion summary"
                type="button"
              >
                x
              </button>
            </div>

            <p className="news-summary-counts">
              {scheduledNewsSummary.total_processed || 0} processed, {scheduledNewsSummary.total_skipped || 0} skipped, {scheduledNewsSummary.total_failed || 0} failed
            </p>

            <div className="news-summary-list">
              <NewsModalListItems
                articles={scheduledNewsSummary.processed || []}
                className=""
                pillLabel="Processed"
                pillClass="success-pill"
                detailField="domain"
              />
              <NewsModalListItems
                articles={scheduledNewsSummary.skipped || []}
                className="skipped"
                pillLabel="Skipped"
                pillClass="skipped-pill"
                detailField="reason"
              />
              <NewsModalListItems
                articles={scheduledNewsSummary.failed || []}
                className="failed"
                pillLabel="Failed"
                pillClass="failure-pill"
                detailField="error"
              />
            </div>

            <div className="modal-actions">
              <button className="primary-button" type="button" onClick={() => setScheduledNewsSummary(null)}>
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
