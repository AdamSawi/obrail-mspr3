from playwright.sync_api import expect, sync_playwright


FRONTEND_URL = "http://localhost:5173"
TIMEOUT_MS = 15000


def open_dashboard(page):
    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=TIMEOUT_MS)
    expect(page.get_by_role("heading", name="Tableau de bord ferroviaire")).to_be_visible(
        timeout=TIMEOUT_MS,
    )
    return page


def test_page_charge_et_affiche_les_donnees():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        open_dashboard(page)

        expect(page.get_by_text("ObRail Europe").first).to_be_visible(timeout=TIMEOUT_MS)
        expect(page.locator(".metric-card").first).to_contain_text("142", timeout=TIMEOUT_MS)

        browser.close()


def test_filtre_par_pays_fonctionne():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        open_dashboard(page)

        result_count = page.locator(".table-count")
        expect(result_count).to_contain_text("resultats", timeout=TIMEOUT_MS)
        initial_count = result_count.inner_text(timeout=TIMEOUT_MS)

        page.get_by_label("Filtrer par pays").select_option("FR", timeout=TIMEOUT_MS)
        expect(result_count).not_to_have_text(initial_count, timeout=TIMEOUT_MS)

        browser.close()


def test_navigation_repond_sans_erreur_serveur():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        response = page.goto(FRONTEND_URL, wait_until="networkidle", timeout=TIMEOUT_MS)

        assert response is not None
        assert response.status < 500
        expect(page.locator("body")).not_to_contain_text("Erreur API 500", timeout=TIMEOUT_MS)

        browser.close()


def test_api_health_visible_dans_le_frontend():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        open_dashboard(page)

        expect(page.get_by_text("API operationnelle")).to_be_visible(timeout=TIMEOUT_MS)

        browser.close()
