import { useCallback, useEffect, useState } from "react";
import { getDomains, getFolderDocuments, createDomain } from "../services/api";

export default function SidebarFolders({
  onSelectFolder,
  selectedFolderIds = [],
  selectedDocumentIds = [],
  onToggleFolderSelection,
  onViewMetadata,
}) {
  const [folders, setFolders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedFolder, setExpandedFolder] = useState(null);
  const [folderDocuments, setFolderDocuments] = useState([]);
  const [isFolderLoading, setIsFolderLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [newFolderDescription, setNewFolderDescription] = useState("");
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);

  const loadFolders = useCallback(async () => {
    setIsLoading(true);
    setError("");

    try {
      const res = await getDomains();
      setFolders(res.domains || []);
    } catch (error) {
      setError(error.message || "Failed to load folders.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(loadFolders, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadFolders]);

  const toggleFolder = async (folder) => {
    if (expandedFolder?.id === folder.id) {
      setExpandedFolder(null);
      setFolderDocuments([]);
      return;
    }

    setExpandedFolder(folder);
    setIsFolderLoading(true);

    try {
      const res = await getFolderDocuments(folder.id);
      setFolderDocuments(res.documents || []);
    } catch (error) {
      console.error(error);
      setFolderDocuments([]);
    } finally {
      setIsFolderLoading(false);
    }
  };

  const createFolder = async () => {
    if (!newFolderName.trim()) {
      return;
    }

    setIsCreatingFolder(true);

    try {
      await createDomain({
        name: newFolderName,
        description: newFolderDescription,
      });

      await loadFolders();
      setNewFolderName("");
      setNewFolderDescription("");
      setShowCreateModal(false);
    } catch (error) {
      console.error(error);
    } finally {
      setIsCreatingFolder(false);
    }
  };

  return (
    <aside className="workspace-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title-area">
          <p className="section-kicker">Workspace</p>
          <h3>Semantic Folders</h3>
          {selectedFolderIds.length > 0 && (
            <span className="selection-badge">
              {selectedFolderIds.length} selected
            </span>
          )}
        </div>
        <div className="sidebar-actions">
          <button
            className="icon-button"
            onClick={() => setShowCreateModal(true)}
            title="Create new folder"
            aria-label="Create new folder"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
          <button
            className="icon-button"
            onClick={loadFolders}
            disabled={isLoading}
            title="Refresh folders"
            aria-label="Refresh folders"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M13.5 8a5.5 5.5 0 1 1-1.6-3.9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M13.5 2v3.5h-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      {error && <p className="error-text sidebar-error">{error}</p>}

      {isLoading && !folders.length ? (
        <div className="sidebar-loading">
          <span className="spinner" />
          Loading folders...
        </div>
      ) : folders.length === 0 ? (
        <div className="empty-state sidebar-empty">
          <div className="empty-icon">📂</div>
          <strong>No folders yet</strong>
          <span>Tap + to create your first semantic folder</span>
        </div>
      ) : (
        <nav className="folders-list">
          {folders.map((folder) => {
            const isSelected = selectedFolderIds.includes(folder.id);
            const isOpen = expandedFolder?.id === folder.id;
            const isUnorganized = folder.id === "unorganized";

            return (
              <div
                key={folder.id}
                className={`folder-item ${isSelected ? "selected" : ""}`}
              >
                <button
                  className="folder-row"
                  onClick={() => toggleFolder(folder)}
                  type="button"
                >
                  {onToggleFolderSelection && (
                    <button
                      className={`scope-toggle ${isSelected ? "selected" : ""}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleFolderSelection(folder.id);
                      }}
                      type="button"
                      title={isSelected ? "Remove from scope" : "Add to scope"}
                    >
                      {isSelected ? "✓" : "○"}
                    </button>
                  )}

                  <span className="folder-icon">
                    {isUnorganized ? "📋" : (isOpen ? "📂" : "📁")}
                  </span>

                  <span className="folder-name" title={folder.name}>{folder.name}</span>
                  {folder.document_count !== undefined && (
                    <span className="doc-count">
                      {folder.document_count}
                    </span>
                  )}

                  <span className="expand-icon">
                    {isOpen ? "▾" : "▸"}
                  </span>
                </button>

                {isOpen && (
                  <div className="folder-documents">
                    {isFolderLoading ? (
                      <span className="sidebar-loading">Loading...</span>
                    ) : folderDocuments.length === 0 ? (
                      <span className="empty-hint">No documents</span>
                    ) : (
                      <ul className="documents-list">
                        {folderDocuments.map((doc) => {
                          const isDocumentSelected = selectedDocumentIds.includes(doc.document_id);

                          return (
                            <li key={doc.document_id} className="folder-document-row">
                            <button
                              className={`document-button ${isDocumentSelected ? "selected" : ""}`}
                              onClick={() => onSelectFolder(doc)}
                              type="button"
                              title={doc.file_name}
                              aria-pressed={isDocumentSelected}
                            >
                              <span className="doc-icon">📄</span>
                              <span className="doc-name">{doc.file_name}</span>
                            </button>
                            <button
                              className="secondary-button document-metadata-button"
                              type="button"
                              onClick={() => onViewMetadata(doc)}
                            >
                              Metadata
                            </button>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      )}

      {showCreateModal && (
        <div className="modal-overlay sidebar-modal">
          <div className="folder-modal">
            <div className="modal-header">
              <div>
                <p className="section-kicker">Semantic Workspace</p>
                <h2>Create Folder</h2>
              </div>
              <button
                className="close-button"
                onClick={() => setShowCreateModal(false)}
                aria-label="Close create folder modal"
                type="button"
              >
                ✕
              </button>
            </div>

            <p className="folder-modal-subtitle">
              Organize documents into semantic collections powered by embeddings.
            </p>

            <div className="folder-form-group">
              <label>Folder Name</label>
              <input
                autoFocus
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="e.g. Central Banks"
              />
            </div>

            <div className="folder-form-group">
              <label>Description <span className="optional">(optional)</span></label>
              <textarea
                rows="3"
                value={newFolderDescription}
                onChange={(e) => setNewFolderDescription(e.target.value)}
                placeholder="What should this folder contain?"
              />
            </div>

            <div className="modal-actions">
              <button
                className="secondary-button"
                onClick={() => setShowCreateModal(false)}
                type="button"
              >
                Cancel
              </button>
              <button
                className="primary-button"
                onClick={createFolder}
                disabled={isCreatingFolder || !newFolderName.trim()}
                type="button"
              >
                {isCreatingFolder ? "Creating..." : "Create Folder"}
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
