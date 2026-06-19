const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function buildTrajetsQuery(filters = {}) {
  return Object.fromEntries(
    Object.entries(filters).filter(
      ([, value]) => value !== "" && value !== null && value !== undefined,
    ),
  );
}

export function getApiErrorMessage(payload, fallback) {
  return (
    payload?.error?.message ||
    payload?.detail?.message ||
    (typeof payload?.detail === "string" ? payload.detail : null) ||
    fallback
  );
}

async function requestJson(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      "Impossible de contacter l'API ObRail. Verifiez que le backend est demarre.",
    );
  }

  if (!response.ok) {
    let message = `Erreur API ${response.status}`;
    try {
      const payload = await response.json();
      message = getApiErrorMessage(payload, message);
    } catch {
      // La reponse peut etre vide ou non JSON en cas d'erreur reseau/proxy.
    }
    throw new Error(message);
  }

  try {
    return await response.json();
  } catch {
    throw new Error("La reponse API est illisible.");
  }
}

export function fetchHealth() {
  return requestJson("/health");
}

export function fetchStats() {
  return requestJson("/stats/volumes");
}

export function fetchTrajets(filters) {
  const params = new URLSearchParams(buildTrajetsQuery(filters));
  const query = params.toString();
  return requestJson(query ? `/trajets?${query}` : "/trajets");
}
