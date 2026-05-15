import { useCallback, useEffect, useState } from "react";
import { deleteDocument, getDocuments } from "../services/api";

function formatSavedTime(value) {
  if (!value) return "-";

  const hasTimezone = /(?:z|[+-]\d{2}:\d{2})$/i.test(value);
  const date = new Date(hasTimezone ? value : `${value}Z`);

  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

export default function DocumentRepository({
  selectedDocumentIds = [],
  onUseDocument,
  onViewMetadata,
  onDeleteDocument,
}) {
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [deletingId, setDeletingId] = useState("");

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    setError("");

    try {
      const res = await getDocuments();
      setDocuments(res.documents || []);
    } catch (error) {
      setError(error.message || "Could not load document.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(loadDocuments, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadDocuments]);

  const handleDelete = async (documentId) => {
    setDeletingId(documentId);
    setError("");

    try {
      await deleteDocument(documentId);
      onDeleteDocument(documentId);
      await loadDocuments();
    } catch (error) {
      setError(error.message || "Could not delete document.");
    } finally {
      setDeletingId("");
    }
  };

  const normalizedSearchQuery = searchQuery.trim().toLowerCase();
  const visibleDocuments = documents.filter((document) => {
    if (!normalizedSearchQuery) return true;
    return [
      String(document.number),
      document.document_id,
      document.file_name,
      document.file_path,
      document.status,
      document.created_date,
    ]
      .filter(Boolean)
      .some((value) => value.toLowerCase().includes(normalizedSearchQuery));
  });

  return (
    <section className="panel repository-panel" aria-labelledby="repository-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">Documents</p>
          <h2 id="repository-title">Document Repository</h2>
        </div>
        <button className="secondary-button compact-button" type="button" onClick={loadDocuments} disabled={isLoading}>
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="repository-search-row">
        <input
          className="repository-search-input"
          type="search"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Search by name, ID, path, status, or date"
          aria-label="Search repository documents"
        />
        <button
          className="secondary-button compact-button"
          type="button"
          onClick={() => setSearchQuery("")}
          disabled={!searchQuery}
        >
          Clear
        </button>
      </div>

      <div className="table-wrap">
        <table className="repository-table">
          <thead>
            <tr>
              <th>Number</th>
              <th>Document ID</th>
              <th>File Name</th>
              <th>File Path</th>
              <th>Status</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {documents.length === 0 ? (
              <tr>
                <td colSpan="7">{isLoading ? "Loading documents..." : "No uploaded documents found."}</td>
              </tr>
            ) : visibleDocuments.length === 0 ? (
              <tr>
                <td colSpan="7">No documents match your search.</td>
              </tr>
            ) : (
              visibleDocuments.map((document) => {
                const isSelected = selectedDocumentIds.includes(document.document_id);

                return (
                  <tr key={document.document_id} className={isSelected ? "selected-document-row" : ""}>
                    <td>{document.number}</td>
                    <td>{document.document_id}</td>
                    <td>{document.file_name}</td>
                    <td>{document.file_path}</td>
                    <td>{document.status}</td>
                    <td title={document.created_date}>{formatSavedTime(document.created_date)}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className={`secondary-button table-button ${isSelected ? "selected" : ""}`}
                          type="button"
                          onClick={() => onUseDocument(document)}
                          aria-pressed={isSelected}
                        >
                          {isSelected ? "Selected" : "Use"}
                        </button>
                        <button
                          className="secondary-button table-button"
                          type="button"
                          onClick={() => onViewMetadata(document)}
                        >
                          View Metadata
                        </button>
                        <button
                          className="danger-button table-button"
                          type="button"
                          onClick={() => handleDelete(document.document_id)}
                          disabled={deletingId === document.document_id}
                        >
                          {deletingId === document.document_id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
