import { useEffect, useState } from "react";
import { getDomains, getFolderDocuments, createDomain } from "../services/api";

export default function SidebarFolders({ onSelectFolder, activeFolder, selectedFolderIds = [], onToggleFolderSelection }) {
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

  useEffect(() => {
    loadFolders();
  }, []);

  const loadFolders = async () => {
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
  };

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
        <div>
          <p className="section-kicker">Workspace</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3>Semantic Folders</h3>
            {selectedFolderIds.length > 0 && (
              <span 
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: '24px',
                  height: '24px',
                  paddingLeft: '6px',
                  paddingRight: '6px',
                  borderRadius: '999px',
                  background: 'var(--primary)',
                  color: '#1c1406',
                  fontSize: '0.65rem',
                  fontWeight: '800',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                  flexShrink: 0,
                  boxShadow: '0 0 8px rgba(214, 168, 61, 0.4)',
                }}
                title={`${selectedFolderIds.length} folder${selectedFolderIds.length > 1 ? 's' : ''} selected`}
              >
                {selectedFolderIds.length}
              </span>
            )}
          </div>
        </div>
        <div className="sidebar-actions">
          <button
            className="icon-button"
            onClick={() => setShowCreateModal(true)}
            title="Create new folder"
            aria-label="Create new folder"
            type="button"
          >
            +
          </button>
          <button
            className="icon-button"
            onClick={loadFolders}
            disabled={isLoading}
            title="Refresh folders"
            aria-label="Refresh folders"
            type="button"
          >
            ↻
          </button>
        </div>
      </div>

      {error && <p className="error-text sidebar-error">{error}</p>}

      {isLoading && !folders.length ? (
        <p className="sidebar-loading">Loading folders...</p>
      ) : folders.length === 0 ? (
        <div className="empty-state sidebar-empty">
          <strong>No folders yet</strong>
          <span>Create a semantic folder to organize your documents</span>
        </div>
      ) : (
        <nav className="folders-list">
          {folders.map((folder) => {
            const isSelected = selectedFolderIds.includes(folder.id);
            const isOpen = expandedFolder?.id === folder.id;
            const isActive = activeFolder?.id === folder.id;
            return (
              <div key={folder.id} className="folder-item">
                {/* ── Row: checkbox + navigation ── */}
                <div className="folder-row">
                  {/* ── Retrieval scope toggle: checkbox on left ── */}
                  {onToggleFolderSelection && (
                    <button
                      className={`scope-toggle ${isSelected ? "selected" : ""}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleFolderSelection(folder.id);
                      }}
                      type="button"
                      title={isSelected ? "Deselect from retrieval scope" : "Select for retrieval scope"}
                      aria-pressed={isSelected}
                      aria-label={`${isSelected ? "Deselect" : "Select"} ${folder.name} for retrieval scope`}
                    >
                      {isSelected ? "✓" : "○"}
                    </button>
                  )}

                  {/* ── Navigation row: opens/closes folder ── */}
                  <button
                    className={`folder-button ${isActive ? "active" : ""} ${isOpen ? "expanded" : ""} ${isSelected ? "selected" : ""}`}
                    onClick={() => toggleFolder(folder)}
                    type="button"
                    title={isOpen ? "Collapse folder" : "Open folder"}
                  >
                    <span className="folder-icon">{isOpen ? "📂" : "📁"}</span>
                    <span className="folder-name">{folder.name}</span>
                    {isSelected && <span className="folder-selected-badge">selected</span>}
                    <span className="folder-toggle">
                      {isOpen ? "▼" : "▶"}
                    </span>
                  </button>
                </div>

                {isOpen && (
                  <div className="folder-documents">
                    {isFolderLoading ? (
                      <p className="sidebar-loading">Loading documents...</p>
                    ) : folderDocuments.length === 0 ? (
                      <p className="empty-state compact">No documents in this folder</p>
                    ) : (
                      <ul className="documents-list">
                        {folderDocuments.map((doc) => (
                          <li key={doc.document_id}>
                            <button
                              className="document-button"
                              onClick={() => onSelectFolder(doc)}
                              type="button"
                              title={doc.file_name}
                            >
                              {doc.file_name}
                            </button>
                          </li>
                        ))}
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
              Create a semantic workspace folder powered by embeddings.
            </p>

            <div className="folder-form-group">
              <label>Folder Name</label>
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Example: Central Banks"
              />
            </div>

            <div className="folder-form-group">
              <label>Description</label>
              <textarea
                rows="3"
                value={newFolderDescription}
                onChange={(e) => setNewFolderDescription(e.target.value)}
                placeholder="Describe the semantic focus of this folder..."
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
                disabled={isCreatingFolder}
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
