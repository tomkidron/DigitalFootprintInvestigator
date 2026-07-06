from playwright.sync_api import expect


def test_download_buttons_appear_after_scan(page):
    """
    Test that the MD, HTML, PDF, and JSON download buttons appear after a successful scan.
    """
    page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
    page.route(
        "**/api/investigate",
        lambda route: route.fulfill(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            content_type="text/event-stream",
            body='data: {"type": "done", "filename": "test_report", "report": "Mock Report Content"}\n\n',
        ),
    )

    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_input.is_checked():
        consent_label.click()

    page.locator("input[aria-label='Target Identifier']").fill("Test User")
    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=5000)
    start_btn.click()

    md_btn = page.locator("a:has-text('Download MD')")
    html_btn = page.locator("a:has-text('Download HTML')")
    pdf_btn = page.locator("a:has-text('Download PDF')")
    json_btn = page.locator("a:has-text('Download JSON')")

    try:
        expect(md_btn).to_be_visible(timeout=10000)
    except AssertionError:
        with open("dom_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        raise
    expect(html_btn).to_be_visible()
    expect(pdf_btn).to_be_visible()
    expect(json_btn).to_be_visible()


def test_reports_tab_view_button(page):
    """
    Test that the Reports tab has a View button that opens a modal.
    """
    page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
    page.route(
        "**/api/reports",
        lambda route: route.fulfill(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            json=[{"name": "test_report.md", "size": 1000, "created_at": 1700000000}],
        ),
    )
    page.route(
        "**/api/reports/*",
        lambda route: route.fulfill(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            body="Mock report content",
        ),
    )

    page.locator("button.tab:has-text('Reports')").click()

    view_btn = page.locator("button:has-text('View')").first
    expect(view_btn).to_be_visible(timeout=8000)

    view_btn.click()
    modal = page.locator("div").filter(has=page.locator("h3:has-text('test_report.md')")).first
    expect(modal).to_be_visible(timeout=8000)

    close_btn = modal.locator("button:has-text('×')")
    expect(close_btn).to_be_visible()
    close_btn.click()
    expect(modal).not_to_be_visible()
