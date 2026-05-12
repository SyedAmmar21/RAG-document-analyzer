const BASE_URL = "http://127.0.0.1:8000";

const parseResponse = async (res) => {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || data.message || "Something went wrong.");
  }

  return data;
};

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/ingest`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(res);
};

export const queryAgent = async (query, document_id) => {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      document_id,
    }),
  });

  return parseResponse(res);
};

export const searchFields = async (fields, document_id) => {
  const res = await fetch(`${BASE_URL}/field-search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fields,
      document_id,
    }),
  });

  return parseResponse(res);
};

export const getDocuments = async () => {
  const res = await fetch(`${BASE_URL}/documents`);

  return parseResponse(res);
};

export const deleteDocument = async (document_id) => {
  const res = await fetch(`${BASE_URL}/documents/${document_id}`, {
    method: "DELETE",
  });

  return parseResponse(res);
};

export const saveDocumentMetadata = async (document_id, metadata, domain) => {
  const res = await fetch(`${BASE_URL}/metadata/save`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_id,
      metadata,
      domain_id: domain?.domain_id || null,
      confidence: domain?.confidence ?? null,
    }),
  });

  return parseResponse(res);
};

export const getDocumentMetadata = async (document_id) => {
  const res = await fetch(`${BASE_URL}/documents/${document_id}/metadata`);

  return parseResponse(res);
};

export const getDomains = async () => {
  const res = await fetch(`${BASE_URL}/domains`);

  return parseResponse(res);
};

export const createDomain = async ({ name, description }) => {
  const res = await fetch(`${BASE_URL}/domains`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name,
      description,
    }),
  });

  return parseResponse(res);
};

export async function getFolderDocuments(domainId) {
  const response = await fetch(
    `${BASE_URL}/domains/${domainId}/documents`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch folder documents");
  }

  return response.json();
}