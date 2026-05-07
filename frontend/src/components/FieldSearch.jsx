import { useEffect, useState } from "react";
import { saveDocumentMetadata } from "../services/api";

const emptyMetadata = {
  name: "",
  location: "",
  date: "",
};

export default function FieldSearch({ documentId, metadataSuggestions, onMetadataSaved }) {
  const [metadataForm, setMetadataForm] = useState(emptyMetadata);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [hasSavedMetadata, setHasSavedMetadata] = useState(false);

  useEffect(() => {
    setError("");
    setMessage("");

    if (!documentId) {
      setMetadataForm(emptyMetadata);
      setIsReviewOpen(false);
      setHasSavedMetadata(false);
      return;
    }

    if (!metadataSuggestions) return;

    setMetadataForm({
      name: metadataSuggestions.name || "",
      location: metadataSuggestions.location || "",
      date: metadataSuggestions.date || "",
    });
    setHasSavedMetadata(Boolean(metadataSuggestions.saved));
    setIsReviewOpen(!metadataSuggestions.saved);
  }, [documentId, metadataSuggestions]);

  const updateMetadataField = (field, value) => {
    setMetadataForm((currentMetadata) => ({
      ...currentMetadata,
      [field]: value,
    }));
  };

  const handleSaveMetadata = async () => {
    if (!documentId) {
      setError("Upload a document first before saving metadata.");
      return;
    }

    setIsSaving(true);
    setError("");

    try {
      await saveDocumentMetadata(documentId, {
        name: metadataForm.name.trim() || null,
        location: metadataForm.location.trim() || null,
        date: metadataForm.date.trim() || null,
      });
      setIsReviewOpen(false);
      setHasSavedMetadata(true);
      setMessage("Document metadata saved.");
      onMetadataSaved();
    } catch (error) {
      setError(error.message || "Could not save document metadata.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="panel field-panel" aria-labelledby="field-search-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">Step 1B</p>
          <h2 id="field-search-title">{hasSavedMetadata ? "Saved document fields" : "Confirm extracted fields"}</h2>
        </div>
        <span className={documentId ? "badge success" : "badge"}>{documentId ? "Ready" : "Locked"}</span>
      </div>

      <div className="metadata-summary">
        {documentId ? (
          <>
            <div>
              <span>Name</span>
              <strong>{metadataForm.name || "Null"}</strong>
            </div>
            <div>
              <span>Location</span>
              <strong>{metadataForm.location || "Null"}</strong>
            </div>
            <div>
              <span>Date</span>
              <strong>{metadataForm.date || "Null"}</strong>
            </div>
          </>
        ) : (
          <div className="empty-state compact">
            <strong>No document yet</strong>
            <span>Upload a document to extract name, location, and date.</span>
          </div>
        )}
      </div>

      <button
        className="secondary-button"
        type="button"
        onClick={() => setIsReviewOpen(true)}
        disabled={!documentId || isSaving}
      >
        Review fields
      </button>

      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}

      {isReviewOpen && documentId && (
        <div className="modal-backdrop" role="presentation">
          <div className="metadata-modal" role="dialog" aria-modal="true" aria-labelledby="metadata-title">
            <div className="metadata-modal-header">
              <div>
                <p className="section-kicker">Step 1B</p>
                <h2 id="metadata-title">{hasSavedMetadata ? "Review saved fields" : "Confirm extracted fields"}</h2>
              </div>
            </div>

            <div className="metadata-form">
              <label>
                <span>Name</span>
                <input
                  value={metadataForm.name}
                  onChange={(event) => updateMetadataField("name", event.target.value)}
                  placeholder="Null"
                  disabled={isSaving}
                />
              </label>
              <label>
                <span>Location</span>
                <input
                  value={metadataForm.location}
                  onChange={(event) => updateMetadataField("location", event.target.value)}
                  placeholder="Null"
                  disabled={isSaving}
                />
              </label>
              <label>
                <span>Date</span>
                <input
                  value={metadataForm.date}
                  onChange={(event) => updateMetadataField("date", event.target.value)}
                  placeholder="Null"
                  disabled={isSaving}
                />
              </label>
            </div>

            <button className="primary-button" type="button" onClick={handleSaveMetadata} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save and close"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
