import { useEffect, useState } from "react";
import { getDomains, getFolderDocuments, createDomain} from "../services/api";

export default function FoldersView({
  onUseDocument,
  onToggleDocumentSelection,
  }) {
  const [folders, setFolders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [folderDocuments, setFolderDocuments] = useState([]);
  const [isFolderLoading, setIsFolderLoading] = useState(false);

  const [showCreateModal, setShowCreateModal] = useState(false); //create folder modal
  const [newFolderName, setNewFolderName] = useState(""); // new folder name input
  const [newFolderDescription, setNewFolderDescription] = useState(""); // new description
  const [isCreatingFolder, setIsCreatingFolder] = useState(false); // create loading state

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

  const openFolder = async (folder) => {
    setSelectedFolder(folder);
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

  // ADDED: create semantic folder
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

      // refresh folder list
      await loadFolders();

      // reset form
      setNewFolderName("");
      setNewFolderDescription("");

      setSelectedFolder(null);

      // close modal
      setShowCreateModal(false);
    } catch (error) {
      console.error(error);
    } finally {
      setIsCreatingFolder(false);
    }
  };


  return (
    <section className="panel repository-panel folders-panel">
      <div className="panel-header folders-header">
        <div>
          <p className="section-kicker">Semantic Workspace</p>

          <h2>Folders</h2>

          <p className="folders-subtitle">
            Adaptive semantic collections powered by embedding similarity.
          </p>
        </div>


        {/* NEW: create folder button */}
        <div className="folders-header-actions">
          <button
            className="primary-button compact-button"
            type="button"
            onClick={() => setShowCreateModal(true)}
          >
            + New Folder
          </button>


          <button
            className="secondary-button compact-button"
            type="button"
            onClick={loadFolders}
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}


      {/* NEW: create folder modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="folder-modal">
            <div>
              <p className="section-kicker">Semantic Workspace</p>
              <h2>Create Folder</h2>
            </div>

            <p className="folder-modal-subtitle">
              Create a semantic workspace folder powered by embeddings.
            </p>

            {/* NEW: folder name input */}
            <div className="folder-form-group">
              <label>Folder Name</label>

              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Example: Central Banks"
              />
            </div>

            {/* NEW: folder description input */}
            <div className="folder-form-group">
              <label>Description</label>

              <textarea
                rows="4"
                value={newFolderDescription}
                onChange={(e) =>
                  setNewFolderDescription(e.target.value)
                }
                placeholder="Describe the semantic focus of this folder..."
              />
            </div>

            {/* NEW: modal action buttons */}
            <div className="folder-modal-actions">
              <button
                className="secondary-button"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>

              <button
                className="primary-button"
                onClick={createFolder}
                disabled={isCreatingFolder}
              >
                {isCreatingFolder
                  ? "Creating..."
                  : "Create Folder"}
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedFolder ? (
        <div className="folder-workspace">
          <div className="folder-workspace-header">
            <button
              className="secondary-button compact-button"
              onClick={() => {
                setSelectedFolder(null);
                setFolderDocuments([]);
              }}
            >
              ← Back to Folders
            </button>

            <div>
              <h2>{selectedFolder.name}</h2>

              <p className="folder-description">
                {selectedFolder.description ||
                  "No description provided."}
              </p>
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
                <div
                  key={document.document_id}
                  className="folder-document-card"
                >
                  <div>
                    <h4>{document.file_name}</h4>

                    <p className="folder-document-date">
                      Added: {document.created_date}
                    </p>
                  </div>

                  <button
                    className="secondary-button compact-button"
                    type="button"
                    onClick={() => {
                      onUseDocument(document);
                      onToggleDocumentSelection(document.document_id);
                    }}
                  >
                    Open Document
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : folders.length === 0 ? (
        <div className="empty-folder-state">
          <h3>No folders created yet</h3>

          <p>
            Create semantic folders during metadata review to begin
            organizing your knowledge workspace.
          </p>
        </div>
      ) : (
        <div className="folders-grid">
          {folders.map((folder) => (
            <div key={folder.id} className="folder-card">
              <div className="folder-card-top">
                <div className="folder-icon">
                  {folder.id === "unorganized" ? "📋" : "📁"}
                </div>

                <div className="folder-meta">
                  <h3>{folder.name}</h3>

                  <p className="folder-description">
                    {folder.description ||
                      "No semantic description provided."}
                  </p>
                </div>
              </div>

              <div className="folder-card-footer">
                <div className="folder-count-badge">
                  {folder.document_count} Documents
                </div>

                <button
                  className="secondary-button compact-button"
                  type="button"
                  onClick={() => openFolder(folder)}
                >
                  Open Folder
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
