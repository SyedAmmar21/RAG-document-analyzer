import { useCallback, useEffect, useState } from "react";
import {
  clearActiveOutput,
  deleteOutput,
  getActiveOutput,
  getOutputs,
  getOutputViewUrl,
  setActiveOutput,
} from "../services/api";

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return "-";
  if (bytes < 1024) return `${bytes} B`;

  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

function formatCreatedDate(value) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function OutputsView({ threadId }) {
  const [outputs, setOutputs] = useState([]);
  const [activeFileName, setActiveFileName] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [deletingFileName, setDeletingFileName] = useState("");
  const [activatingFileName, setActivatingFileName] = useState("");

  const loadOutputs = useCallback(async () => {
    setIsLoading(true);
    setError("");

    try {
      const [outputsResponse, activeResponse] = await Promise.all([
        getOutputs(),
        getActiveOutput(threadId),
      ]);
      setOutputs(outputsResponse.outputs || []);
      setActiveFileName(activeResponse.active_output?.file_name || "");
    } catch (loadError) {
      setError(loadError.message || "Could not load generated outputs.");
    } finally {
      setIsLoading(false);
    }
  }, [threadId]);

  useEffect(() => {
    const timeoutId = window.setTimeout(loadOutputs, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadOutputs]);

  const handleOpen = (fileName) => {
    window.open(getOutputViewUrl(fileName), "_blank", "noopener,noreferrer");
  };

  const handleDelete = async (fileName) => {
    if (!window.confirm(`Delete generated file "${fileName}"?`)) return;

    setDeletingFileName(fileName);
    setError("");

    try {
      await deleteOutput(fileName);
      setOutputs((currentOutputs) => (
        currentOutputs.filter((output) => output.file_name !== fileName)
      ));
      if (activeFileName === fileName) {
        setActiveFileName("");
      }
    } catch (deleteError) {
      setError(deleteError.message || "Could not delete generated file.");
    } finally {
      setDeletingFileName("");
    }
  };

  const handleActiveDocument = async (output) => {
    setActivatingFileName(output.file_name);
    setError("");

    try {
      if (activeFileName === output.file_name) {
        await clearActiveOutput(threadId);
        setActiveFileName("");
      } else {
        const response = await setActiveOutput(threadId, output.file_name);
        setActiveFileName(response.active_output?.file_name || output.file_name);
      }
    } catch (activeError) {
      setError(activeError.message || "Could not update the active document.");
    } finally {
      setActivatingFileName("");
    }
  };

  return (
    <section className="panel repository-panel outputs-panel" aria-labelledby="outputs-title">
      <div className="panel-header">
        <div>
          <p className="section-kicker">AI Agent</p>
          <h2 id="outputs-title">Outputs</h2>
          <p className="outputs-subtitle">Files created by the AI agent are saved here for opening or deletion.</p>
        </div>
        <button className="secondary-button compact-button" type="button" onClick={loadOutputs} disabled={isLoading}>
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="table-wrap">
        <table className="repository-table outputs-table">
          <thead>
            <tr>
              <th>File Name</th>
              <th>Type</th>
              <th>Size</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {outputs.length === 0 ? (
              <tr>
                <td colSpan="5">
                  {isLoading ? "Loading generated files..." : "No AI-generated output files yet."}
                </td>
              </tr>
            ) : (
              outputs.map((output) => (
                <tr key={output.file_name} className={activeFileName === output.file_name ? "active-output-row" : ""}>
                  <td>
                    <div className="output-file-name">
                      <span>{output.file_name}</span>
                      {activeFileName === output.file_name && <span className="active-output-badge">Active document</span>}
                    </div>
                  </td>
                  <td>{output.file_type ? output.file_type.toUpperCase() : "-"}</td>
                  <td>{formatFileSize(output.size)}</td>
                  <td title={output.created_date || ""}>{formatCreatedDate(output.created_date)}</td>
                  <td>
                    <div className="output-actions" aria-label={`Actions for ${output.file_name}`}>
                      <button
                        className={`output-action-button output-active-button ${activeFileName === output.file_name ? "active" : ""}`}
                        type="button"
                        onClick={() => handleActiveDocument(output)}
                        disabled={!output.is_editable || Boolean(activatingFileName)}
                        title={
                          output.is_editable
                            ? activeFileName === output.file_name
                              ? "Deselect active document"
                              : "Make this the active document for the agent"
                            : "Only DOCX, PPTX, and XLSX files can be edited as active documents"
                        }
                      >
                        <span aria-hidden="true">{activeFileName === output.file_name ? "✓" : "＋"}</span>
                        {activatingFileName === output.file_name
                          ? "Setting"
                          : activeFileName === output.file_name
                            ? "Active"
                            : "Set active"}
                      </button>
                      <button
                        className="output-action-button output-open-button"
                        type="button"
                        onClick={() => handleOpen(output.file_name)}
                        title="Open generated file"
                      >
                        <span aria-hidden="true">↗</span>
                        Open
                      </button>
                      <button
                        className="output-action-button output-delete-button"
                        type="button"
                        onClick={() => handleDelete(output.file_name)}
                        disabled={deletingFileName === output.file_name}
                        title="Delete generated file"
                        aria-label={`Delete ${output.file_name}`}
                      >
                        <span aria-hidden="true">⌫</span>
                        {deletingFileName === output.file_name ? "Deleting" : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
