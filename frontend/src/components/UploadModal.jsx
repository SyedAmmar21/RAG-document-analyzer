import { useState } from "react";
import { uploadFile } from "../services/api";
import DuplicateAlert from "./DuplicateAlert";

export default function UploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
}) {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [showDuplicateAlert, setShowDuplicateAlert] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState({});

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile || null);
    setMessage("");
    setError("");
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
      
      if (res.is_duplicate) {
        // Show duplicate alert and don't close the modal yet
        setDuplicateInfo({
          fileName: res.file_name || file.name,
          documentNumber: res.document_number,
        });
        setShowDuplicateAlert(true);
      } else {
        setMessage(res.message || "Document uploaded successfully.");
        // Only close for non-duplicate uploads
        setTimeout(onClose, 500);
      }
      
      onUploadSuccess({
        document_id: res.document_id,
        file_name: res.file_name || file.name,
        metadata_suggestions: res.metadata_suggestions,
        domain_suggestion: res.domain_suggestion,
        is_duplicate: Boolean(res.is_duplicate),
      });

      setFile(null);
      setMessage("");
    } catch (error) {
      setError(error.message || "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDuplicateAlertClose = () => {
    setShowDuplicateAlert(false);
    // Close the upload modal after acknowledging the duplicate alert
    onClose();
  };

  // Keep modal open if showing duplicate alert, even if parent tries to close it
  if (!isOpen && !showDuplicateAlert) return null;

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-modal-title">
        <div className="modal-header">
          <div>
            <p className="section-kicker">Upload Document</p>
            <h2 id="upload-modal-title">Add to workspace</h2>
          </div>
          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close upload modal"
            type="button"
          >
            ✕
          </button>
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

        <div className="modal-actions">
          <button className="secondary-button" onClick={onClose} type="button">
            Cancel
          </button>
          <button className="primary-button" onClick={handleUpload} disabled={isUploading || !file}>
            {isUploading ? "Uploading..." : "Upload document"}
          </button>
        </div>

        {message && <p className="success-text">{message}</p>}
        {error && <p className="error-text">{error}</p>}
      </div>
      
      <DuplicateAlert
        isOpen={showDuplicateAlert}
        onClose={handleDuplicateAlertClose}
        fileName={duplicateInfo.fileName}
        documentNumber={duplicateInfo.documentNumber}
      />
    </div>
  );
}
