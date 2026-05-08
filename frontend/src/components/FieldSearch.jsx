import { useEffect, useState } from "react";
import { createDomain, getDomains, saveDocumentMetadata } from "../services/api";

const listFields = ["entities", "economic_indicators", "regions"];

const emptyMetadata = {
  title: "",
  published_date: "",
  focus: "",
  entities: [],
  economic_indicators: [],
  regions: [],
};

const fieldLabels = {
  title: "Title",
  published_date: "Published date",
  focus: "Focus",
  entities: "Entities",
  economic_indicators: "Economic indicators",
  regions: "Regions",
};

function normalizeList(value) {
  if (!value) return [];
  return Array.isArray(value) ? value.filter(Boolean) : [value].filter(Boolean);
}

export default function FieldSearch({ documentId, metadataSuggestions, domainSuggestion, onMetadataSaved }) {
  const [metadataForm, setMetadataForm] = useState(emptyMetadata);
  const [domains, setDomains] = useState([]);
  const [selectedDomainId, setSelectedDomainId] = useState("");
  const [domainConfidence, setDomainConfidence] = useState(null);
  const [newDomain, setNewDomain] = useState({ name: "", description: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingDomain, setIsCreatingDomain] = useState(false);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [isCreateDomainOpen, setIsCreateDomainOpen] = useState(false);
  const [hasSavedMetadata, setHasSavedMetadata] = useState(false);

  useEffect(() => {
    const loadDomains = async () => {
      try {
        const res = await getDomains();
        setDomains(res.domains || []);
      } catch (error) {
        setError(error.message || "Could not load domains.");
      }
    };

    loadDomains();
  }, []);

  useEffect(() => {
    setError("");
    setMessage("");

    if (!documentId) {
      setMetadataForm(emptyMetadata);
      setSelectedDomainId("");
      setDomainConfidence(null);
      setIsReviewOpen(false);
      setHasSavedMetadata(false);
      return;
    }

    if (!metadataSuggestions) return;

    setMetadataForm({
      title: metadataSuggestions.title || "",
      published_date: metadataSuggestions.published_date || "",
      focus: metadataSuggestions.focus || "",
      entities: normalizeList(metadataSuggestions.entities),
      economic_indicators: normalizeList(metadataSuggestions.economic_indicators),
      regions: normalizeList(metadataSuggestions.regions),
    });
    setHasSavedMetadata(Boolean(metadataSuggestions.saved));
    setIsReviewOpen(!metadataSuggestions.saved);
  }, [documentId, metadataSuggestions]);

  useEffect(() => {
    if (!domainSuggestion) {
      setSelectedDomainId("");
      setDomainConfidence(null);
      return;
    }

    const domainId = domainSuggestion.domain_id || domains.find((domain) => domain.name === domainSuggestion.suggested_domain)?.id;
    setSelectedDomainId(domainId ? String(domainId) : "");
    setDomainConfidence(domainSuggestion.confidence ?? null);
  }, [domainSuggestion, domains]);

  const updateTextField = (field, value) => {
    setMetadataForm((currentMetadata) => ({
      ...currentMetadata,
      [field]: value,
    }));
  };

  const updateListField = (field, index, value) => {
    setMetadataForm((currentMetadata) => ({
      ...currentMetadata,
      [field]: currentMetadata[field].map((item, itemIndex) => (itemIndex === index ? value : item)),
    }));
  };

  const addListValue = (field) => {
    setMetadataForm((currentMetadata) => ({
      ...currentMetadata,
      [field]: [...currentMetadata[field], ""],
    }));
  };

  const removeListValue = (field, index) => {
    setMetadataForm((currentMetadata) => ({
      ...currentMetadata,
      [field]: currentMetadata[field].filter((_, itemIndex) => itemIndex !== index),
    }));
  };

  const handleSaveMetadata = async () => {
    if (!documentId) {
      setError("Upload a document first before saving metadata.");
      return;
    }

    if (!selectedDomainId) {
      setError("Choose a semantic domain before saving.");
      return;
    }

    setIsSaving(true);
    setError("");

    try {
      await saveDocumentMetadata(documentId, {
        title: metadataForm.title.trim() || null,
        published_date: metadataForm.published_date.trim() || null,
        focus: metadataForm.focus.trim() || null,
        entities: metadataForm.entities.map((value) => value.trim()).filter(Boolean),
        economic_indicators: metadataForm.economic_indicators.map((value) => value.trim()).filter(Boolean),
        regions: metadataForm.regions.map((value) => value.trim()).filter(Boolean),
      }, {
        domain_id: selectedDomainId ? Number(selectedDomainId) : null,
        confidence: domainConfidence,
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

  const handleCreateDomain = async () => {
    const name = newDomain.name.trim();

    if (!name) {
      setError("Domain name is required.");
      return;
    }

    setIsCreatingDomain(true);
    setError("");

    try {
      const res = await createDomain({
        name,
        description: newDomain.description.trim() || null,
      });
      const createdDomain = res.domain;
      setDomains((currentDomains) => [...currentDomains, createdDomain].sort((a, b) => a.name.localeCompare(b.name)));
      setSelectedDomainId(String(createdDomain.id));
      setDomainConfidence(null);
      setNewDomain({ name: "", description: "" });
      setIsCreateDomainOpen(false);
    } catch (error) {
      setError(error.message || "Could not create domain.");
    } finally {
      setIsCreatingDomain(false);
    }
  };

  const confidenceLabel = domainConfidence === null || domainConfidence === undefined
    ? "Manual"
    : `${Math.round(Number(domainConfidence) * 100)}%`;

  const renderSummaryValue = (field) => {
    const value = metadataForm[field];

    if (Array.isArray(value)) {
      return value.length > 0 ? value.join(", ") : "Null";
    }

    return value || "Null";
  };

  return (
    <section className="panel field-panel" aria-labelledby="field-search-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">Step 1B</p>
          <h2 id="field-search-title">{hasSavedMetadata ? "Saved document metadata" : "Confirm extracted metadata"}</h2>
        </div>
        <span className={documentId ? "badge success" : "badge"}>{documentId ? "Ready" : "Locked"}</span>
      </div>

      <div className="metadata-summary">
        {documentId ? (
          Object.keys(emptyMetadata).map((field) => (
            <div key={field}>
              <span>{fieldLabels[field]}</span>
              <strong>{renderSummaryValue(field)}</strong>
            </div>
          ))
        ) : (
          <div className="empty-state compact">
            <strong>No document yet</strong>
            <span>Upload a document to extract financial metadata.</span>
          </div>
        )}
      </div>

      <button
        className="secondary-button"
        type="button"
        onClick={() => setIsReviewOpen(true)}
        disabled={!documentId || isSaving}
      >
        Review metadata
      </button>

      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}

      {isReviewOpen && documentId && (
        <div className="modal-backdrop" role="presentation">
          <div className="metadata-modal" role="dialog" aria-modal="true" aria-labelledby="metadata-title">
            <div className="metadata-modal-header">
              <div>
                <p className="section-kicker">Step 1B</p>
                <h2 id="metadata-title">{hasSavedMetadata ? "Review saved metadata" : "Confirm extracted metadata"}</h2>
              </div>
            </div>

            <div className="metadata-form">
              {["title", "published_date", "focus"].map((field) => (
                <label key={field}>
                  <span>{fieldLabels[field]}</span>
                  <input
                    value={metadataForm[field]}
                    onChange={(event) => updateTextField(field, event.target.value)}
                    placeholder="Null"
                    disabled={isSaving}
                  />
                </label>
              ))}

              {listFields.map((field) => (
                <div className="metadata-list-field" key={field}>
                  <span>{fieldLabels[field]}</span>
                  <div className="metadata-list-values">
                    {metadataForm[field].length === 0 ? (
                      <p className="metadata-null-text">Null</p>
                    ) : (
                      metadataForm[field].map((value, index) => (
                        <div className="metadata-list-row" key={`${field}-${index}`}>
                          <input
                            value={value}
                            onChange={(event) => updateListField(field, index, event.target.value)}
                            placeholder="Null"
                            disabled={isSaving}
                          />
                          <button
                            className="icon-button"
                            type="button"
                            onClick={() => removeListValue(field, index)}
                            disabled={isSaving}
                            aria-label={`Remove ${fieldLabels[field]} value`}
                            title="Remove value"
                          >
                            -
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                  <button className="secondary-button compact-button" type="button" onClick={() => addListValue(field)} disabled={isSaving}>
                    Add {fieldLabels[field]}
                  </button>
                </div>
              ))}

              <div className="domain-review">
                <div>
                  <p className="section-kicker">Suggested Domain</p>
                  <h3>Semantic domain</h3>
                </div>

                <label>
                  <span>Domain</span>
                  <select
                    value={selectedDomainId}
                    onChange={(event) => {
                      setSelectedDomainId(event.target.value);
                      setDomainConfidence(null);
                    }}
                    disabled={isSaving || isCreatingDomain}
                  >
                    <option value="">Select domain</option>
                    {domains.map((domain) => (
                      <option key={domain.id} value={domain.id}>
                        {domain.name}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="domain-confidence">
                  <span>Confidence</span>
                  <strong>{confidenceLabel}</strong>
                </div>

                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setIsCreateDomainOpen(true)}
                  disabled={isSaving || isCreatingDomain}
                >
                  + Create New Domain
                </button>
              </div>
            </div>

            <button className="primary-button" type="button" onClick={handleSaveMetadata} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save metadata"}
            </button>
          </div>
        </div>
      )}

      {isCreateDomainOpen && (
        <div className="modal-backdrop domain-modal-backdrop" role="presentation">
          <div className="metadata-modal domain-modal" role="dialog" aria-modal="true" aria-labelledby="create-domain-title">
            <div className="metadata-modal-header">
              <div>
                <p className="section-kicker">Domain management</p>
                <h2 id="create-domain-title">Create semantic domain</h2>
              </div>
            </div>

            <div className="create-domain-panel">
              <span>Domain name</span>
              <input
                value={newDomain.name}
                onChange={(event) => setNewDomain((currentDomain) => ({ ...currentDomain, name: event.target.value }))}
                placeholder="Example: Currency Markets"
                disabled={isCreatingDomain}
              />
              <span>Description</span>
              <input
                value={newDomain.description}
                onChange={(event) => setNewDomain((currentDomain) => ({ ...currentDomain, description: event.target.value }))}
                placeholder="Optional semantic description"
                disabled={isCreatingDomain}
              />
            </div>

            <button className="primary-button" type="button" onClick={handleCreateDomain} disabled={isCreatingDomain}>
              {isCreatingDomain ? "Creating..." : "Create and use domain"}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setIsCreateDomainOpen(false)}
              disabled={isCreatingDomain}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
