import { useState } from "react";
import MarkdownMessage from "./MarkdownMessage";
import { searchFields } from "../services/api";

const defaultFields = ["Name", "Location", "Date"];

export default function FieldSearch({ documentId }) {
  const [fields, setFields] = useState(defaultFields);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const updateField = (index, value) => {
    setFields((currentFields) => currentFields.map((field, fieldIndex) => (fieldIndex === index ? value : field)));
  };

  const addField = () => {
    setFields((currentFields) => [...currentFields, ""]);
  };

  const removeField = (index) => {
    setFields((currentFields) => currentFields.filter((_, fieldIndex) => fieldIndex !== index));
  };

  const handleSearch = async () => {
    const activeFields = fields.map((field) => field.trim()).filter(Boolean);

    if (!documentId) {
      setError("Upload a document first before searching for fields.");
      return;
    }

    if (activeFields.length === 0) {
      setError("Add at least one field or search key.");
      return;
    }

    setIsSearching(true);
    setError("");

    try {
      const res = await searchFields(activeFields, documentId);
      setResult(res.answer || "No matching fields were found.");
    } catch (error) {
      setError(error.message || "Field search failed. Please try again.");
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <section className="panel field-panel" aria-labelledby="field-search-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">Step 1B</p>
          <h2 id="field-search-title">Field search</h2>
        </div>
        <span className={documentId ? "badge success" : "badge"}>{documentId ? "Ready" : "Locked"}</span>
      </div>

      <div className="field-search-grid">
        <div className="field-builder">
          <div className="field-list">
            {fields.map((field, index) => (
              <div className="field-row" key={index}>
                <input
                  value={field}
                  onChange={(event) => updateField(index, event.target.value)}
                  placeholder="Name, location, date, total..."
                  disabled={isSearching}
                />
                <button
                  className="icon-button"
                  type="button"
                  onClick={() => removeField(index)}
                  disabled={isSearching || fields.length === 1}
                  aria-label={`Remove field ${index + 1}`}
                  title="Remove field"
                >
                  -
                </button>
              </div>
            ))}
          </div>

          <button className="secondary-button" type="button" onClick={addField} disabled={isSearching}>
            Add field
          </button>

          <button className="primary-button" type="button" onClick={handleSearch} disabled={!documentId || isSearching}>
            {isSearching ? "Searching..." : "Search fields"}
          </button>

          {error && <p className="error-text">{error}</p>}
        </div>

        <div className="field-output" aria-live="polite">
          {result ? (
            <MarkdownMessage text={result} />
          ) : (
            <div className="empty-state compact">
              <strong>Field output</strong>
              <span>Results will be recorded here.</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
