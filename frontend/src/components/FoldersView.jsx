import { useEffect, useState } from "react";
import {
  createDomain,
  deleteDomain,
  getDomains,
  getFolderDocuments,
  updateDomain,
} from "../services/api";

const emptyFolderForm = {
  name: "",
  description: "",
};

export default function FoldersView({
  onUseDocument,
  onFolderChanged,
  onFolderDeleted,
}) {
  const [folders, setFolders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [folderDocuments, setFolderDocuments] = useState([]);
  const [isFolderLoading, setIsFolderLoading] = useState(false);
  const [activeModal, setActiveModal] = useState(null);
  const [folderForm, setFolderForm] = useState(emptyFolderForm);
  const [isSavingFolder, setIsSavingFolder] = useState(false);
  const [deletingFolderId, setDeletingFolderId] = useState(null);

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

  useEffect(() => {
    loadFolders();
  }, []);

  const openFolder = async (folder) => {
    setSelectedFolder(folder);
    setIsFolderLoading(true);
    setError("");

    try {
      const res = await getFolderDocuments(folder.id);
      setFolderDocuments(res.documents || []);
    } catch (error) {
      setError(error.message || "Failed to load folder documents.");
      setFolderDocuments([]);
    } finally {
      setIsFolderLoading(false);
    }
  };

  const openCreateModal = () => {
    setFolderForm(emptyFolderForm);
    setActiveModal("create");
    setError("");
    setMessage("");
  };

  const openEditModal = (folder) => {
    setSelectedFolder(folder);
    setFolderForm({
      name: folder.name || "",
      description: folder.description || "",
    });
    setActiveModal("edit");
    setError("");
    setMessage("");
  };

  const closeFolderModal = () => {
    setActiveModal(null);
    setFolderForm(emptyFolderForm);
    setIsSavingFolder(false);
  };

  const handleSaveFolder = async () => {
    const name = folderForm.name.trim();

    if (!name) {
      setError("Folder name is required.");
      return;
    }

    setIsSavingFolder(true);
    setError("");
    setMessage("");

    try {
      const payload = {
        name,
        description: folderForm.description.trim() || null,
      };

      const res = activeModal === "edit" && selectedFolder
        ? await updateDomain(selectedFolder.id, payload)
        : await createDomain(payload);

      await loadFolders();

      if (activeModal === "edit") {
        const updatedFolder = {
          ...selectedFolder,
          ...res.domain,
        };
        setSelectedFolder(updatedFolder);
        setMessage("Folder information updated.");
        onFolderChanged?.(updatedFolder);
      } else {
        setMessage("Folder created.");
        onFolderChanged?.(res.domain);
      }

      closeFolderModal();
    } catch (error) {
      setError(error.message || "Could not save folder.");
    } finally {
      setIsSavingFolder(false);
    }
  };

  const handleDeleteFolder = async (folder) => {
    if (!window.confirm(`Delete "${folder.name}"? Documents in this folder will move to Unorganized Files.`)) {
      return;
    }

    setDeletingFolderId(folder.id);
    setError("");
    setMessage("");

    try {
      await deleteDomain(folder.id);
      setMessage("Folder deleted. Documents were moved to Unorganized Files.");
      setSelectedFolder(null);
      setFolderDocuments([]);
      await loadFolders();
      onFolderDeleted?.(folder.id);
    } catch (error) {
      setError(error.message || "Could not delete folder.");
    } finally {
      setDeletingFolderId(null);
    }
  };

  const canEditSelectedFolder = selectedFolder && selectedFolder.id !== "unorganized";

  return (
    <section className="panel repository-panel folders-panel">
      <div className="panel-header folders-header">
        <div>
          <p className="section-kicker">Semantic Workspace</p>
          <h2>Folders</h2>
          <p className="folders-subtitle">
            Manage semantic domains. Deleting a folder keeps documents and moves them to Unorganized Files.
          </p>
        </div>

        <div className="folders-header-actions">
          <button className="primary-button compact-button" type="button" onClick={openCreateModal}>
            + New Folder
          </button>
          <button className="secondary-button compact-button" type="button" onClick={loadFolders} disabled={isLoading}>
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="success-text">{message}</p>}

      {selectedFolder ? (
        <div className="folder-workspace">
          <div className="folder-workspace-header">
            <button
              className="secondary-button compact-button"
              type="button"
              onClick={() => {
                setSelectedFolder(null);
                setFolderDocuments([]);
              }}
            >
              Back to Folders
            </button>

            <div className="folder-detail-heading">
              <div>
                <p className="section-kicker">
                  {selectedFolder.id === "unorganized" ? "Fallback folder" : "Semantic domain"}
                </p>
                <h2>{selectedFolder.name}</h2>
                <p className="folder-description">
                  {selectedFolder.description || "No semantic description provided."}
                </p>
              </div>

              {canEditSelectedFolder && (
                <div className="folder-detail-actions">
                  <button className="secondary-button compact-button" type="button" onClick={() => openEditModal(selectedFolder)}>
                    Edit Info
                  </button>
                  <button
                    className="danger-button compact-button"
                    type="button"
                    onClick={() => handleDeleteFolder(selectedFolder)}
                    disabled={deletingFolderId === selectedFolder.id}
                  >
                    {deletingFolderId === selectedFolder.id ? "Deleting..." : "Delete Folder"}
                  </button>
                </div>
              )}
            </div>
          </div>

          {isFolderLoading ? (
            <p>Loading folder documents...</p>
          ) : folderDocuments.length === 0 ? (
            <div className="empty-folder-state">
              <h3>No documents inside this folder</h3>
            </div>
          ) : (
            <div className="folder-documents-list">
              {folderDocuments.map((document) => (
                <div key={document.document_id} className="folder-document-card">
                  <div>
                    <h4>{document.file_name}</h4>
                    <p className="folder-document-date">Added: {document.created_date}</p>
                  </div>

                  <button
                    className="secondary-button compact-button"
                    type="button"
                    onClick={() => onUseDocument(document)}
                  >
                    Use Document
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : folders.length === 0 ? (
        <div className="empty-folder-state">
          <h3>No folders created yet</h3>
          <p>Create semantic folders during metadata review to begin organizing your knowledge workspace.</p>
        </div>
      ) : (
        <div className="folders-grid">
          {folders.map((folder) => {
            const isSyntheticFolder = folder.id === "unorganized";

            return (
              <div key={folder.id} className="folder-card">
                <div className="folder-card-top">
                  <div className="folder-icon" aria-hidden="true">
                    {isSyntheticFolder ? "Un" : "Fo"}
                  </div>

                  <div className="folder-meta">
                    <h3>{folder.name}</h3>
                    <p className="folder-description">
                      {folder.description || "No semantic description provided."}
                    </p>
                  </div>
                </div>

                <div className="folder-card-footer">
                  <div className="folder-count-badge">
                    {folder.document_count} Documents
                  </div>

                  <div className="folder-card-actions">
                    <button className="secondary-button compact-button" type="button" onClick={() => openFolder(folder)}>
                      Open
                    </button>

                    {!isSyntheticFolder && (
                      <>
                        <button className="secondary-button compact-button" type="button" onClick={() => openEditModal(folder)}>
                          Edit
                        </button>
                        <button
                          className="danger-button compact-button"
                          type="button"
                          onClick={() => handleDeleteFolder(folder)}
                          disabled={deletingFolderId === folder.id}
                        >
                          {deletingFolderId === folder.id ? "..." : "Del"}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeModal && (
        <div className="modal-overlay">
          <div className="folder-modal">
            <div>
              <p className="section-kicker">Semantic Workspace</p>
              <h2>{activeModal === "edit" ? "Edit Folder" : "Create Folder"}</h2>
            </div>

            <p className="folder-modal-subtitle">
              Folder information is part of the semantic embedding, so saving updates the folder centroid.
            </p>

            <div className="folder-form-group">
              <label>Folder Name</label>
              <input
                type="text"
                value={folderForm.name}
                onChange={(event) => setFolderForm((current) => ({ ...current, name: event.target.value }))}
                placeholder="Example: Central Banks"
                disabled={isSavingFolder}
              />
            </div>

            <div className="folder-form-group">
              <label>Description</label>
              <textarea
                rows="4"
                value={folderForm.description}
                onChange={(event) => setFolderForm((current) => ({ ...current, description: event.target.value }))}
                placeholder="Describe the semantic focus of this folder..."
                disabled={isSavingFolder}
              />
            </div>

            <div className="folder-modal-actions">
              <button className="secondary-button" type="button" onClick={closeFolderModal} disabled={isSavingFolder}>
                Cancel
              </button>
              <button className="primary-button" type="button" onClick={handleSaveFolder} disabled={isSavingFolder}>
                {isSavingFolder ? "Saving..." : activeModal === "edit" ? "Save Changes" : "Create Folder"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
