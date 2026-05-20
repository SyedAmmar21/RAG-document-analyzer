export default function DuplicateAlert({
  isOpen,
  onClose,
  fileName,
  documentNumber,
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="alert-modal" role="dialog" aria-modal="true" aria-labelledby="duplicate-alert-title">
        <div className="modal-header">
          <h2 id="duplicate-alert-title">Document Already Uploaded</h2>
        </div>

        <div className="modal-content">
          <p className="alert-message">
            <strong>{fileName}</strong> has already been uploaded to the repository.
          </p>
          <p className="alert-info">
            Document Number: <strong>#{documentNumber}</strong>
          </p>
          <p className="alert-description">
            The existing document has been reused. No duplicate entry was created.
          </p>
        </div>

        <div className="modal-actions">
          <button className="primary-button" onClick={onClose} type="button">
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
