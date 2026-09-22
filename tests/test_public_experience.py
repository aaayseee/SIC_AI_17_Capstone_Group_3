from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from argus.app.marketing import calculate_investigation_capacity
from argus.app.public_site import _preview_figure, validate_demo_request


def _button(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def _element(elements, label: str):
    return next(element for element in elements if element.label == label)


def _visible_text(app: AppTest) -> str:
    groups = (app.markdown, app.caption, app.info, app.success, app.error)
    return " ".join(str(item.value) for group in groups for item in group)


def _demo_artifact_root() -> Path:
    return Path(__file__).resolve().parents[1] / "demo" / "artifacts"


def _app() -> AppTest:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    return AppTest.from_file(str(app_path)).run(timeout=20)


def test_public_home_and_open_demo_routes_work(monkeypatch) -> None:
    monkeypatch.delenv("ARGUS_DEMO_EMAIL", raising=False)
    monkeypatch.delenv("ARGUS_DEMO_PASSWORD", raising=False)
    app = _app()

    assert not app.exception
    markup = " ".join(str(item.value) for item in app.markdown)
    assert '<a class="argus-primary-cta" href="#case-challenge">Explore ARGUS</a>' in markup
    assert _button(app, "Request a Pilot")
    _button(app, "Open Demo").click()
    app.run(timeout=20)

    assert not app.exception
    assert [item.label for item in app.text_input] == ["Corporate email", "Password"]
    app.text_input[0].set_value("not-an-email")
    app.text_input[1].set_value("prototype-access")
    _button(app, "Sign in").click()
    app.run(timeout=20)
    assert any("valid corporate email" in item.value for item in app.error)


def test_public_navigation_anchors_have_matching_sections() -> None:
    app = _app()
    markup = " ".join(str(item.value) for item in app.markdown)

    assert 'class="argus-skip-link" href="#argus-main-content"' in markup
    assert 'id="argus-main-content"' in markup
    assert '<details class="argus-mobile-nav">' in markup
    assert "<summary>Explore</summary>" in markup
    for section_id in (
        "product",
        "how-it-works",
        "case-challenge",
        "calculator",
        "resources",
        "pilot-program",
    ):
        assert f'href="#{section_id}"' in markup
        assert f'id="{section_id}"' in markup

    for copy in (
        "See beyond the transaction.",
        "10,000 alerts. Where should your analysts look first?",
        "Before ARGUS",
        "With ARGUS",
        "ILLUSTRATIVE SYNTHETIC SCENARIO",
        "AML investigation capacity calculator",
        "ARGUS Talks",
        "Case Challenges",
        "AML Insights",
        "Historical Data Evaluation",
        "Pilot Results",
    ):
        assert copy in markup
    assert "ARGUS does not" in markup
    assert "accuse, block, or sanction customers" in markup


def test_capacity_calculator_uses_only_workload_inputs_and_clamps_the_gap() -> None:
    estimate = calculate_investigation_capacity(
        monthly_alerts=10_000,
        analyst_count=12,
        average_case_minutes=30,
        working_hours_per_analyst=160,
    )

    assert estimate.monthly_alerts == 10_000
    assert estimate.review_capacity == 3_840
    assert estimate.capacity_gap == 6_160

    over_capacity = calculate_investigation_capacity(
        monthly_alerts=1_000,
        analyst_count=12,
        average_case_minutes=30,
        working_hours_per_analyst=160,
    )
    assert over_capacity.capacity_gap == 0


@pytest.mark.parametrize(
    ("monthly_alerts", "analyst_count", "average_case_minutes", "working_hours"),
    [
        (1_000, 2, 0, 160),
        (-1, 2, 30, 160),
        (1_000, float("inf"), 30, 160),
    ],
)
def test_capacity_calculator_rejects_invalid_inputs(
    monthly_alerts: float,
    analyst_count: float,
    average_case_minutes: float,
    working_hours: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_investigation_capacity(
            monthly_alerts,
            analyst_count,
            average_case_minutes,
            working_hours,
        )


def test_capacity_calculator_renders_metrics_disclaimer_and_demo_cta() -> None:
    app = _app()
    metrics = {metric.label: metric.value for metric in app.metric}

    assert metrics == {
        "Monthly Alerts": "10,000",
        "Estimated Review Capacity": "3,840",
        "Potential Capacity Gap": "6,160",
    }
    visible = _visible_text(app)
    assert "illustrates investigation workload only" in visible
    assert "does not estimate ARGUS performance or guaranteed productivity gains" in visible

    _element(app.number_input, "Monthly AML alerts").set_value(1_000)
    app.run(timeout=20)
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Potential Capacity Gap"] == "0"

    _button(app, "See how prioritization can help").click()
    app.run(timeout=20)
    assert [item.label for item in app.text_input] == ["Corporate email", "Password"]


def test_case_challenge_reveals_history_network_and_resumes_in_case_investigator(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ARGUS_ARTIFACT_DIR", str(_demo_artifact_root()))
    monkeypatch.delenv("ARGUS_DEMO_EMAIL", raising=False)
    monkeypatch.delenv("ARGUS_DEMO_PASSWORD", raising=False)
    app = _app()

    visible = _visible_text(app)
    assert "ILLUSTRATIVE SYNTHETIC SCENARIO" in visible
    assert "ADDITIONAL TRANSACTION HISTORY" not in visible
    for label in ("YES", "NO", "SHOW MORE CONTEXT"):
        assert _button(app, label)

    _button(app, "SHOW MORE CONTEXT").click()
    app.run(timeout=20)
    assert "ADDITIONAL TRANSACTION HISTORY" in _visible_text(app)
    assert _button(app, "Reveal account network")

    _button(app, "Reveal account network").click()
    app.run(timeout=20)
    visible = _visible_text(app)
    assert "ACCOUNT NETWORK CONTEXT" in visible
    assert "Network context can reveal patterns that are difficult to see in isolation" in visible
    assert "not a finding of wrongdoing" in visible

    _button(app, "Explore the ARGUS case workflow").click()
    app.run(timeout=20)
    assert [item.label for item in app.text_input] == ["Corporate email", "Password"]
    _element(app.text_input, "Corporate email").set_value("analyst@bank.example")
    _element(app.text_input, "Password").set_value("prototype-access")
    _button(app, "Sign in").click()
    app.run(timeout=20)
    assert not app.exception
    assert app.title[0].value == "Case Investigator"


def test_public_resource_and_legal_routes_render() -> None:
    routes = {
        "View Model Evidence": "Review the evidence behind the ARGUS project.",
        "Privacy": "Privacy notice",
        "Terms": "Terms of use",
    }

    for button_label, expected_copy in routes.items():
        app = _app()
        _button(app, button_label).click()
        app.run(timeout=20)
        visible = " ".join(str(item.value) for item in app.markdown)
        assert not app.exception
        assert expected_copy in visible


def test_pilot_request_validation_rejects_missing_and_invalid_values() -> None:
    errors = validate_demo_request(
        {
            "name": "",
            "work_email": "invalid",
            "company": "",
            "role": "",
            "organization_type": "Select organization type",
            "main_challenge": "Select main challenge",
            "optional_message": "",
            "consent": False,
        }
    )

    assert set(errors) == {
        "name",
        "work_email",
        "company",
        "role",
        "organization_type",
        "main_challenge",
        "consent",
    }


def test_pilot_request_valid_payload_allows_an_empty_optional_message() -> None:
    assert not validate_demo_request(
        {
            "name": "Gizem Özcan",
            "work_email": "gizem@institution.example",
            "company": "Example Institution",
            "role": "AML Manager",
            "organization_type": "Bank",
            "main_challenge": "Alert Prioritization",
            "optional_message": "",
            "consent": True,
        }
    )


def test_pilot_request_form_completes_as_session_only_flow() -> None:
    app = _app()
    _button(app, "Request a Pilot").click()
    app.run(timeout=20)

    _element(app.text_input, "Name").set_value("Gizem Özcan")
    _element(app.text_input, "Company").set_value("Example Institution")
    _element(app.text_input, "Work Email").set_value("gizem@institution.example")
    _element(app.text_input, "Role").set_value("AML Manager")
    _element(app.selectbox, "Organization Type").set_value("Bank")
    _element(app.selectbox, "Main Challenge").set_value("Alert Prioritization")
    _element(app.text_area, "Optional Message").set_value("Evaluate the workflow.")
    _element(
        app.checkbox,
        "I understand this demo form validates inputs but does not send or store them.",
    ).check()
    _button(app, "Request ARGUS Pilot").click()
    app.run(timeout=20)

    assert not app.exception
    assert any("Gizem Özcan" in item.value for item in app.success)
    confirmation = _visible_text(app).casefold()
    assert "demo" in confirmation
    assert "not stored" in confirmation
    assert "or sent" in confirmation


def test_pilot_request_form_shows_required_errors_but_not_an_optional_message_error() -> None:
    app = _app()
    _button(app, "Request a Pilot").click()
    app.run(timeout=20)
    _button(app, "Request ARGUS Pilot").click()
    app.run(timeout=20)

    assert not app.exception
    assert any("Please correct" in item.value for item in app.error)
    visible = _visible_text(app)
    assert "Enter your name." in visible
    assert "Enter your work email." in visible
    assert "Select your organization type." in visible
    assert "Select your main challenge." in visible
    assert "Confirm that you understand this demo form" in visible
    assert "optional message" not in visible.casefold()


def test_login_uses_enterprise_copy_and_reveals_sso_limit_only_after_click() -> None:
    app = _app()
    _button(app, "Open Demo").click()
    app.run(timeout=20)

    visible = " ".join(str(item.value) for group in (app.markdown, app.caption) for item in group)
    assert "ANALYST ACCESS" in visible
    assert "Sign in with your institutional account." in visible
    assert "Demo Environment" in visible
    assert "Demo actions are not persisted after sign-out." in visible
    assert "SECURE-STYLE ANALYST ACCESS" not in visible
    assert "Prototype access" not in visible
    assert not app.info

    _button(app, "Corporate SSO").click()
    app.run(timeout=20)
    assert any("Corporate SSO is not connected" in item.value for item in app.info)


def test_public_network_preview_expands_context_without_scientific_claims() -> None:
    single = _preview_figure(False)
    expanded = _preview_figure(True)

    assert len(single.data[-1].x) == 2
    assert len(expanded.data[-1].x) == 6
    assert len(single.data) == 2
    assert len(expanded.data) == 8
    assert single.data[0].line.color == "#B7791F"
    assert single.data[0].line.width > expanded.data[1].line.width
    assert single.layout.height == 270
    assert expanded.layout.height == 338
    assert "scaleanchor" not in single.layout.yaxis.to_plotly_json()
    assert all("Account" in str(label) for label in expanded.data[-1].text)


def test_public_network_preview_control_switches_to_expanded_context() -> None:
    app = _app()

    app.radio[0].set_value("Explore network")
    app.run(timeout=20)

    assert not app.exception
    assert app.radio[0].value == "Explore network"
    assert any("6 accounts" in str(item.value) for item in app.markdown)


def test_streamlit_product_chrome_uses_supported_minimal_configuration() -> None:
    config_path = Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))

    assert config["client"]["toolbarMode"] == "minimal"
    assert config["client"]["showSidebarNavigation"] is False


def test_public_and_portal_styles_include_responsive_guards() -> None:
    styles_path = Path(__file__).resolve().parents[1] / "src" / "argus" / "app" / "styles.py"
    styles = styles_path.read_text(encoding="utf-8")

    assert "transform: none !important" not in styles
    assert "max-width: 86vw !important" in styles
    assert "min-width: 0 !important" in styles
    assert ".argus-mobile-nav { display: block; }" in styles
    responsive_rules = styles[styles.index("@media (max-width: 900px)") :]
    for selector in (
        ".argus-alert-flow",
        ".argus-before-after",
        ".argus-transaction-ticket",
        ".argus-marketing-resources",
        ".argus-pilot-steps",
    ):
        assert selector in responsive_rules
