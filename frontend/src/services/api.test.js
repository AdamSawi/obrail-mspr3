import { afterEach, describe, expect, it, vi } from "vitest";
import { buildTrajetsQuery, fetchTrajets, getApiErrorMessage } from "./api.js";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("buildTrajetsQuery", () => {
  it("removes empty filters before calling the API", () => {
    expect(
      buildTrajetsQuery({
        country: "FR",
        type_train: "",
        origin: "Lyon",
        destination: null,
        page: 1,
        page_size: 12,
      }),
    ).toEqual({
      country: "FR",
      origin: "Lyon",
      page: 1,
      page_size: 12,
    });
  });
});

describe("getApiErrorMessage", () => {
  it("reads the normalized backend error envelope first", () => {
    expect(
      getApiErrorMessage(
        {
          error: {
            message: "Trajet 'unknown-trip-id' introuvable",
          },
        },
        "Erreur API 404",
      ),
    ).toBe("Trajet 'unknown-trip-id' introuvable");
  });

  it("keeps FastAPI detail and fallback messages readable", () => {
    expect(getApiErrorMessage({ detail: "Champ invalide" }, "Erreur API 422")).toBe(
      "Champ invalide",
    );
    expect(getApiErrorMessage({}, "Erreur API 500")).toBe("Erreur API 500");
  });
});

describe("fetchTrajets", () => {
  it("does not append an empty query string", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ items: [], total: 0, total_pages: 0 }),
    });

    await fetchTrajets({});

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/trajets", {});
  });
});
