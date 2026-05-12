import { useEffect, useState } from "react";
import { getDomains, getFolderDocuments } from "../services/api";

export default function FoldersView() {
  const [folders, setFolders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [folderDocuments, setFolderDocuments] = useState([]);
  const [isFolderLoading, setIsFolderLoading] = useState(false);

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

      <button
        className="secondary-button compact-button"
        type="button"
        onClick={loadFolders}
        disabled={isLoading}
      >
        {isLoading ? "Refreshing..." : "Refresh"}
      </button>
    </div>

    {error && <p className="error-text">{error}</p>}

      {/* ADDED: if folder selected, show folder workspace */}
      {selectedFolder ? (
        <div className="folder-workspace">
          <div className="folder-workspace-header">
            {/* ADDED: back button */}
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
                {selectedFolder.description || "No description provided."}
              </p>
            </div>
          </div>

          {/* ADDED: loading state */}
          {isFolderLoading ? (
            <p>Loading folder documents...</p>
          ) : folderDocuments.length === 0 ? (
            // ADDED: empty folder state
            <div className="empty-folder-state">
              <h3>No documents inside this folder</h3>
            </div>
          ) : (
            // ADDED: document list
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

                  {/* FUTURE: open/use document */}
                  <button
                    className="secondary-button compact-button"
                    type="button"
                  >
                    Open Document
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : folders.length === 0 ? (
        // EXISTING EMPTY STATE
        <div className="empty-folder-state">
          <h3>No folders created yet</h3>

          <p>
            Create semantic folders during metadata review to begin organizing
            your knowledge workspace.
          </p>
        </div>
      ) : (
        // EXISTING FOLDER GRID
        <div className="folders-grid">
          {folders.map((folder) => (
            <div key={folder.id} className="folder-card">
              <div className="folder-card-top">
                <div className="folder-icon">📁</div>

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

                {/* UPDATED */}
                {/* ADDED: openFolder click handler */}
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