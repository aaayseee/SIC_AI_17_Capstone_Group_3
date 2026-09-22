# ruff: noqa: E501 -- embedded public-site HTML is kept readable by semantic section
"""Interactive, synthetic marketing experiences for the ARGUS public site."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from argus.app.styles import anchor, section_heading

Navigate = Callable[[str], None]


@dataclass(frozen=True)
class CapacityEstimate:
    """Transparent workload calculation based only on visitor-supplied inputs."""

    monthly_alerts: float
    review_capacity: float
    capacity_gap: float


def calculate_investigation_capacity(
    monthly_alerts: float,
    analyst_count: float,
    average_case_minutes: float,
    working_hours_per_analyst: float,
) -> CapacityEstimate:
    """Calculate monthly review capacity without attributing gains to ARGUS."""

    values = {
        "monthly_alerts": monthly_alerts,
        "analyst_count": analyst_count,
        "average_case_minutes": average_case_minutes,
        "working_hours_per_analyst": working_hours_per_analyst,
    }
    for name, value in values.items():
        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite")
        if float(value) < 0:
            raise ValueError(f"{name} cannot be negative")
    if average_case_minutes == 0:
        raise ValueError("average_case_minutes must be greater than zero")

    review_capacity = analyst_count * working_hours_per_analyst * 60 / average_case_minutes
    capacity_gap = max(monthly_alerts - review_capacity, 0.0)
    return CapacityEstimate(
        monthly_alerts=float(monthly_alerts),
        review_capacity=float(review_capacity),
        capacity_gap=float(capacity_gap),
    )


def render_problem_flow() -> None:
    """Explain the investigation-capacity problem without claiming automated decisions."""

    anchor("problem")
    section_heading(
        "The investigation challenge",
        "10,000 alerts. Where should your analysts look first?",
        "ARGUS is designed to organize transaction and account-network context so a human "
        "investigator can decide what deserves review first.",
    )
    st.markdown(
        """
        <section class="argus-alert-flow" aria-label="Alert prioritization workflow">
          <article><span>01</span><strong>Alert workload</strong>
          <p>A large queue competes for finite analyst attention.</p></article>
          <i aria-hidden="true">&rarr;</i>
          <article><span>02</span><strong>ARGUS prioritization</strong>
          <p>Transaction history and network signals support ordering.</p></article>
          <i aria-hidden="true">&rarr;</i>
          <article><span>03</span><strong>Focused review</strong>
          <p>Analysts inspect the cases surfaced for attention.</p></article>
          <i aria-hidden="true">&rarr;</i>
          <article class="human"><span>04</span><strong>Analyst decision</strong>
          <p>A trained professional records the next action.</p></article>
        </section>
        <p class="argus-boundary-copy"><strong>Decision boundary:</strong> ARGUS does not
        accuse, block, or sanction customers. It provides prioritization and decision support.
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_before_after() -> None:
    """Contrast fragmented review with the intended ARGUS investigation workflow."""

    st.markdown(
        """
        <section class="argus-before-after" aria-label="Before ARGUS and with ARGUS">
          <article class="before">
            <span class="argus-card-label">Before ARGUS</span>
            <h3>Fragmented investigation context</h3>
            <ul>
              <li>Long alert queues</li>
              <li>Isolated transaction views</li>
              <li>Limited account-network context</li>
              <li>Manual prioritization</li>
            </ul>
          </article>
          <div class="argus-comparison-shift" aria-hidden="true">
            <span>CONTEXT</span><b>&rarr;</b>
          </div>
          <article class="with">
            <span class="argus-card-label">With ARGUS</span>
            <h3>A connected review workspace</h3>
            <ul>
              <li>Prioritized investigation queue</li>
              <li>Directed account-network visualization</li>
              <li>Transaction-history context</li>
              <li>Separate model evidence and human decision</li>
            </ul>
          </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _set_challenge_stage(stage: int, decision: str | None = None) -> None:
    st.session_state["argus_case_challenge_stage"] = stage
    if decision is not None:
        st.session_state["argus_case_challenge_decision"] = decision


def _open_case_workflow(navigate: Navigate) -> None:
    st.session_state["argus_post_login_page"] = "Case Investigator"
    navigate("login")


def render_case_challenge(navigate: Navigate) -> None:
    """Render a staged, explicitly illustrative investigation challenge."""

    anchor("case-challenge")
    section_heading(
        "Interactive case challenge",
        "Would you investigate this transaction?",
        "Start with one synthetic transfer, then reveal the context an investigator would "
        "want to examine.",
    )
    stage = int(st.session_state.get("argus_case_challenge_stage", 0))
    decision = st.session_state.get("argus_case_challenge_decision")

    with st.container(key="case_challenge_shell"):
        st.markdown(
            """
            <div class="argus-challenge-label">ILLUSTRATIVE SYNTHETIC SCENARIO</div>
            <div class="argus-transaction-ticket">
              <div><span>Sender</span><strong>SYN-1047</strong></div>
              <div class="route"><span>Directed transfer</span><b>&rarr;</b></div>
              <div><span>Receiver</span><strong>SYN-3382</strong></div>
              <div><span>Amount</span><strong>EUR 4,850</strong></div>
              <div><span>Time</span><strong>14:08</strong></div>
              <div><span>Channel</span><strong>Online transfer</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if stage == 0:
            st.markdown("#### Would you investigate this transaction?")
            yes, no, context = st.columns([1, 1, 1.5])
            yes.button(
                "YES",
                key="challenge_yes",
                type="primary",
                width="stretch",
                on_click=_set_challenge_stage,
                args=(1, "yes"),
            )
            no.button(
                "NO",
                key="challenge_no",
                width="stretch",
                on_click=_set_challenge_stage,
                args=(1, "no"),
            )
            context.button(
                "SHOW MORE CONTEXT",
                key="challenge_context",
                width="stretch",
                on_click=_set_challenge_stage,
                args=(1,),
            )
        else:
            if decision:
                st.caption(
                    f"Your initial choice: {str(decision).upper()}. There is no automatic "
                    "verdict in this illustrative exercise."
                )
            st.markdown(
                """
                <div class="argus-history-reveal">
                  <span>ADDITIONAL TRANSACTION HISTORY</span>
                  <div><b>13:42</b><p>SYN-6630 &rarr; SYN-3382<br>
                  <strong>EUR 4,900</strong></p></div>
                  <div><b>14:08</b><p>SYN-1047 &rarr; SYN-3382<br>
                  <strong>EUR 4,850</strong></p></div>
                  <div><b>14:19</b><p>SYN-3382 &rarr; SYN-7714<br>
                  <strong>EUR 9,600</strong></p></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if stage == 1:
                st.button(
                    "Reveal account network",
                    key="challenge_network",
                    type="primary",
                    on_click=_set_challenge_stage,
                    args=(2,),
                )
            else:
                st.markdown(
                    """
                    <div class="argus-challenge-network">
                      <div class="heading"><span>ACCOUNT NETWORK CONTEXT</span>
                      <small>Illustrative accounts and directed transfers</small></div>
                      <svg viewBox="0 0 620 250" role="img"
                           aria-label="Illustrative directed account network">
                        <defs><marker id="challenge-arrow" markerWidth="8" markerHeight="8"
                        refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z"/></marker></defs>
                        <g class="edges">
                          <path d="M105 65L286 118"/><path d="M105 188L286 132"/>
                          <path class="focal" d="M105 125L280 125"/>
                          <path d="M337 118L510 66"/><path d="M337 132L510 188"/>
                        </g>
                        <g class="nodes">
                          <circle cx="82" cy="65" r="24"/><circle cx="82" cy="125" r="29"/>
                          <circle cx="82" cy="188" r="24"/>
                          <circle class="core" cx="310" cy="125" r="34"/>
                          <circle cx="538" cy="65" r="25"/><circle cx="538" cy="188" r="25"/>
                        </g>
                        <g class="labels">
                          <text x="82" y="28">SYN-6630</text><text x="82" y="234">SYN-1047</text>
                          <text x="310" y="177">SYN-3382</text><text x="538" y="28">SYN-7714</text>
                          <text x="538" y="234">SYN-5821</text>
                        </g>
                      </svg>
                    </div>
                    <div class="argus-challenge-insight">
                    <strong>Context changes the question.</strong>
                    <p>A single transaction may appear ordinary. Network context can reveal patterns that are difficult to see in isolation. The pattern still requires
                    human investigation; it is not a finding of wrongdoing.</p></div>
                    """,
                    unsafe_allow_html=True,
                )
                primary, secondary = st.columns([2.1, 1])
                primary.button(
                    "Explore the ARGUS case workflow",
                    key="challenge_open_demo",
                    type="primary",
                    width="stretch",
                    on_click=_open_case_workflow,
                    args=(navigate,),
                )
                secondary.button(
                    "Restart challenge",
                    key="challenge_restart",
                    width="stretch",
                    on_click=_set_challenge_stage,
                    args=(0, ""),
                )


def render_capacity_calculator(navigate: Navigate) -> None:
    """Render an input-driven workload calculator with no product-performance claim."""

    anchor("calculator")
    section_heading(
        "AML investigation capacity calculator",
        "Make the review workload visible.",
        "Estimate how many alerts a team could review from staffing and time inputs alone.",
    )
    inputs, output = st.columns([0.9, 1.1], gap="large", vertical_alignment="center")
    with inputs:
        with st.container(key="capacity_inputs"):
            monthly_alerts = st.number_input(
                "Monthly AML alerts", min_value=0, value=10_000, step=500
            )
            analyst_count = st.number_input("Number of analysts", min_value=0, value=12, step=1)
            average_case_minutes = st.number_input(
                "Average investigation time per alert (minutes)",
                min_value=1,
                value=30,
                step=5,
            )
            working_hours = st.number_input(
                "Working hours per analyst per month", min_value=0, value=160, step=8
            )
    estimate = calculate_investigation_capacity(
        monthly_alerts,
        analyst_count,
        average_case_minutes,
        working_hours,
    )
    with output:
        with st.container(key="capacity_results"):
            st.markdown(
                '<div class="argus-card-label">Your workload estimate</div>',
                unsafe_allow_html=True,
            )
            first, second, third = st.columns(3)
            first.metric("Monthly Alerts", f"{estimate.monthly_alerts:,.0f}")
            second.metric("Estimated Review Capacity", f"{estimate.review_capacity:,.0f}")
            third.metric("Potential Capacity Gap", f"{estimate.capacity_gap:,.0f}")
            reviewed_share = (
                100.0
                if estimate.monthly_alerts == 0
                else min(estimate.review_capacity / estimate.monthly_alerts * 100, 100.0)
            )
            st.markdown(
                '<div class="argus-capacity-track" aria-label="Estimated share of alerts that '
                f'fit within review capacity"><span style="width:{reviewed_share:.2f}%"></span>'
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption("Capacity = analysts × working hours × 60 ÷ average investigation minutes.")
            st.info(
                "This calculator illustrates investigation workload only. It does not estimate "
                "ARGUS performance or guaranteed productivity gains."
            )
            st.button(
                "See how prioritization can help",
                key="capacity_open_demo",
                type="primary",
                on_click=navigate,
                args=("login",),
            )


def render_resource_cards() -> None:
    """Provide honest placeholders for future educational marketing content."""

    anchor("resources")
    section_heading(
        "Resources",
        "Build a shared language for network-aware investigation.",
        "A lightweight home for future conversations, exercises, and educational material.",
    )
    st.markdown(
        """
        <section class="argus-marketing-resources">
          <article><span>CONVERSATIONS</span><h3>ARGUS Talks</h3>
          <p>Expert conversations about financial crime, AML, and responsible AI.</p>
          <small>Content series planned</small></article>
          <article><span>INTERACTIVE LEARNING</span><h3>Case Challenges</h3>
          <p>Illustrative exercises that reveal investigation context step by step.</p>
          <small>First challenge available above</small></article>
          <article><span>EDUCATION</span><h3>AML Insights</h3>
          <p>Concise explainers for fraud, compliance, and data teams.</p>
          <small>Content series planned</small></article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_pilot_program(navigate: Navigate) -> None:
    """Describe a controlled pilot path without implying deployment readiness."""

    anchor("pilot-program")
    section_heading(
        "ARGUS Pilot Program",
        "Evaluate fit before considering deployment.",
        "A controlled pilot would test prioritization and network context with institutional "
        "governance, validation, and analyst oversight.",
    )
    st.markdown(
        """
        <ol class="argus-pilot-steps">
          <li><span>01</span><strong>Historical Data Evaluation</strong></li>
          <li><span>02</span><strong>Alert Prioritization Analysis</strong></li>
          <li><span>03</span><strong>Network Intelligence Review</strong></li>
          <li><span>04</span><strong>Analyst Feedback</strong></li>
          <li><span>05</span><strong>Pilot Results</strong></li>
        </ol>
        """,
        unsafe_allow_html=True,
    )
    copy, action = st.columns([4, 1.35], vertical_alignment="center")
    copy.caption(
        "A pilot is an evaluation process—not a production commitment or performance guarantee."
    )
    action.button(
        "Request ARGUS Pilot",
        key="pilot_program_request",
        type="primary",
        width="stretch",
        on_click=navigate,
        args=("demo",),
    )
