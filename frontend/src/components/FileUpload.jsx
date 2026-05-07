import { useState } from "react";
import { uploadFile } from "../services/api";

export default function FileUpload({ setDocumentId, setDocumentName, setMetadataSuggestions, documentName, isReady }) {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile || null);
    setMessage("");
    setError("");

    if (selectedFile) {
      setDocumentName(selectedFile.name);
      setDocumentId(null);
      setMetadataSuggestions(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Choose a document before uploading.");
      return;
    }

    setIsUploading(true);
    setError("");

    try {
      const res = await uploadFile(file);
      setMessage(res.message || "Document uploaded successfully.");
      setDocumentId(res.document_id);
      setDocumentName(res.file_name || file.name);
      setMetadataSuggestions(res.metadata_suggestions ? { ...res.metadata_suggestions, saved: Boolean(res.duplicate) } : null);
    } catch (error) {
      setError(error.message || "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="panel upload-panel" aria-labelledby="upload-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">Step 1</p>
          <h2 id="upload-title">Upload document</h2>
        </div>
        <span className={isReady ? "badge success" : "badge"}>{isReady ? "Ready" : "Required"}</span>
      </div>

      <label className={file ? "drop-zone has-file" : "drop-zone"}>
        <input type="file" onChange={handleFileChange} />
        <span className="drop-icon" aria-hidden="true">+</span>
        <span className="drop-title">{file ? file.name : "Choose a document"}</span>
        <span className="drop-copy">
          {file
            ? `${(file.size / 1024 / 1024).toFixed(2)} MB selected`
            : "PDF, text, or docx files only. (Max 5 MB)"}
        </span>
      </label>

      <button className="primary-button" onClick={handleUpload} disabled={isUploading || !file}>
        {isUploading ? "Uploading..." : isReady ? "Replace document" : "Upload document"}
      </button>

      {documentName && isReady && (
        <div className="active-source-card">
          <span className="active-source-label">Active source</span>
          <strong>{documentName}</strong>
          <span>This is the document used for chat and field search.</span>
        </div>
      )}
      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}
    </section>
  );
}
