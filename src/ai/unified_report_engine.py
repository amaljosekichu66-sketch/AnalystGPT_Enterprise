"""
Unified AI report generation engine.

Generates the complete AI report in a single LLM request.

Architectural contract:
------------------------
- One prompt → one LLM response.
- Parsing extracts four required sections.
- All exceptions are raised and handled by the caller (AIManager).
- No streaming, retries, caching, or multi-step logic.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.prompt_builder import PromptBuilder
from src.llm.response_parser import ResponseParser
from src.reporting.reporting_report import ReportingReport


# ==========================================================
# Constants
# ==========================================================

_LOG_SEPARATOR = "=" * 60

# Private section name constants (as they appear in the LLM response)
_EXECUTIVE_SUMMARY = "EXECUTIVE SUMMARY"
_RECOMMENDATIONS = "RECOMMENDATIONS"
_EXPLANATIONS = "EXPLANATIONS"
_NARRATIVE = "NARRATIVE"

_SECTION_NAMES = (
    _EXECUTIVE_SUMMARY,
    _RECOMMENDATIONS,
    _EXPLANATIONS,
    _NARRATIVE,
)

# Expanded aliases for robustness
_SECTION_ALIASES = {
    _EXECUTIVE_SUMMARY: (
        "EXECUTIVE SUMMARY",
        "EXECUTIVE OVERVIEW",
        "SUMMARY",
        "OVERVIEW",
        "EXECUTIVE SYNOPSIS",
    ),
    _RECOMMENDATIONS: (
        "RECOMMENDATIONS",
        "RECOMMENDATION",
        "KEY INSIGHTS",
        "INSIGHTS",
        "ACTIONABLE INSIGHTS",
    ),
    _EXPLANATIONS: (
        "EXPLANATIONS",
        "EXPLANATION",
        "ANALYSIS",
        "DETAILED ANALYSIS",
        "BUSINESS INSIGHTS",
        "OBSERVATIONS",
        "FINDINGS",
        "KEY OBSERVATIONS",
    ),
    _NARRATIVE: (
        "NARRATIVE",
        "EXECUTIVE NARRATIVE",
        "CONCLUSION",
        "FINAL THOUGHTS",
        "OVERALL ASSESSMENT",
        "FINAL SUMMARY",
        "SUMMARY NARRATIVE",
    ),
}

# Minimum acceptable response length (characters)
_MIN_RESPONSE_LENGTH = 10

# Estimated maximum token limit (based on current Ollama config)
# 512 tokens ≈ 2000 characters (approx. 4 chars/token).
_ESTIMATED_MAX_CHARS = 2000

# Compiled regex for bullet list parsing (reused)
_BULLET_PATTERN = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


@dataclass(frozen=True)
class AISections:
    """
    Immutable container for AI-generated sections.

    This dataclass defines the exact contract between the UnifiedReportEngine
    and the AIManager. Every field must be present and non‑empty.
    """
    executive_summary: str
    recommendations: list[str]
    explanations: list[str]
    narrative: str


class UnifiedReportEngine:
    """
    Generates all AI report sections using a single LLM request.

    Responsibilities:
    - Build a prompt from the ReportingReport.
    - Call the LLM once.
    - Parse the response into four named sections.
    - Validate the result and raise clear exceptions on failure.
    """

    def __init__(self, llm: BaseLLM) -> None:
        """
        Initialise the engine with a concrete LLM instance.

        Parameters
        ----------
        llm : BaseLLM
            The LLM adapter used for generation.
        """
        self._llm = llm

        # Pre-compile heading patterns with line anchors for robustness
        self._heading_patterns = {
            name: re.compile(
                r"^\s*(?:=+\s*)?(?:" + "|".join(
                    re.escape(alias) for alias in _SECTION_ALIASES[name]
                ) + r")\s*:?(?:\s*=+)?\s*$",
                re.IGNORECASE | re.MULTILINE,
            )
            for name in _SECTION_NAMES
        }

        # Compile a single pattern to detect any heading alias (for truncation detection)
        all_aliases = set()
        for aliases in _SECTION_ALIASES.values():
            all_aliases.update(aliases)
        self._any_heading_pattern = re.compile(
            r"^\s*(?:=+\s*)?(?:" + "|".join(re.escape(a) for a in all_aliases) + r")\s*:?(?:\s*=+)?\s*$",
            re.IGNORECASE | re.MULTILINE,
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def generate(self, reporting_report: ReportingReport) -> AISections:
        """
        Execute the full report generation pipeline.

        Parameters
        ----------
        reporting_report : ReportingReport
            The input report from the analytics stage.

        Returns
        -------
        AISections
            An immutable container with all required sections.

        Raises
        ------
        ValueError
            If the report is None, the LLM response is empty,
            required sections are missing, or sections are empty.
        RuntimeError
            For unexpected errors during generation or parsing.

        Notes
        -----
        This method does not catch exceptions; the caller is responsible
        for handling them (e.g., AIManager wraps them in AIResult).
        """
        if reporting_report is None:
            raise ValueError("reporting_report cannot be None.")

        logger.info(_LOG_SEPARATOR)
        logger.info("UNIFIED REPORT ENGINE")
        logger.info(_LOG_SEPARATOR)

        total_start = time.perf_counter()

        # ---- Prompt Building ----
        prompt_start = time.perf_counter()
        prompt = self._build_prompt(reporting_report)
        prompt_time = time.perf_counter() - prompt_start

        # ---- LLM Call ----
        llm_start = time.perf_counter()
        response = self._call_llm(prompt)
        logger.info("=" * 80)
        logger.info("RAW GEMMA RESPONSE")
        logger.info("=" * 80)
        logger.info(response)
        logger.info("=" * 80)
        # Log last few chars to detect truncation
        if len(response) > 100:
            logger.info("Response tail: ...%s", response[-100:])
        llm_time = time.perf_counter() - llm_start

        # ---- Parsing ----
        parse_start = time.perf_counter()
        sections = self._parse_sections(response)
        parse_time = time.perf_counter() - parse_start

        total_time = time.perf_counter() - total_start

        self._log_performance(prompt_time, llm_time, parse_time, total_time, response, sections)

        logger.info(_LOG_SEPARATOR)
        return sections

    # ==========================================================
    # Prompt Building
    # ==========================================================

    def _build_prompt(self, reporting_report: ReportingReport) -> str:
        """
        Build the full prompt for the LLM.

        Parameters
        ----------
        reporting_report : ReportingReport
            The input report.

        Returns
        -------
        str
            The complete prompt string.

        Raises
        ------
        ValueError
            If the prompt is empty after construction.
        """
        prompt = PromptBuilder.full_report(reporting_report)

        if not prompt or not prompt.strip():
            raise ValueError("Built prompt is empty.")

        logger.info("Prompt Length : %d characters", len(prompt))
        return prompt

    # ==========================================================
    # LLM Interaction
    # ==========================================================

    def _call_llm(self, prompt: str) -> str:
        """
        Execute the single LLM request.

        Parameters
        ----------
        prompt : str
            The prompt to send.

        Returns
        -------
        str
            The raw LLM response.

        Raises
        ------
        ValueError
            If the response is empty or too short.
        RuntimeError
            If the LLM call fails unexpectedly.
        """
        logger.info("Calling LLM...")

        try:
            response = self._llm.generate(prompt)
        except (ConnectionError, TimeoutError, ValueError) as exc:
            # Specific LLM-related exceptions; re-raise with context
            logger.exception("LLM call failed (network/timeout/input error).")
            raise RuntimeError("LLM generation failed.") from exc
        except Exception as exc:
            # Catch-all for unexpected errors, still re-raise
            logger.exception("LLM call failed (unexpected error).")
            raise RuntimeError("LLM generation failed.") from exc

        if not response:
            raise ValueError("LLM response is empty.")
        if len(response.strip()) < _MIN_RESPONSE_LENGTH:
            raise ValueError(
                f"LLM response is too short ({len(response)} chars)."
            )

        logger.info("LLM returned %d characters.", len(response))
        return response

    # ==========================================================
    # Section Parsing
    # ==========================================================

    def _parse_sections(self, response: str) -> AISections:
        """
        Parse the LLM response into structured sections.

        Strategy:
        - Locate each required heading using pre‑compiled regexes.
        - If any heading is missing, check for signs of truncation.
        - Extract the content between headings.
        - Convert recommendations and explanations to lists.
        - Validate that mandatory sections are non‑empty.

        Parameters
        ----------
        response : str
            The raw LLM output.

        Returns
        -------
        AISections
            A dataclass with all four sections.

        Raises
        ------
        ValueError
            If any required section is missing, duplicated, or empty.
            If the response appears truncated, a detailed message is provided.
        """
        response = ResponseParser.parse(response)

        # 1. Find all headings (with duplicate detection)
        headings = self._find_headings(response)

        # 2. Log found headings for debugging
        found_names = list(headings.keys())
        logger.info("Parsed headings found: %s", found_names if found_names else "none")

        missing = [name for name in _SECTION_NAMES if name not in headings]
        if missing:
            # Check for truncation indicators
            truncation_info = self._detect_truncation(response, headings)

            error_msg = (
                f"Missing required AI sections: {', '.join(missing)}.\n"
                f"Found headings: {found_names if found_names else 'none'}.\n"
                f"Response length: {len(response)} characters.\n"
            )
            if truncation_info:
                error_msg += truncation_info
            else:
                error_msg += (
                    "No clear truncation detected; the response may simply lack the required sections. "
                    "Check the prompt and the model's output."
                )

            raise ValueError(error_msg)

        # 3. Order headings by their start index
        ordered = sorted(headings.items(), key=lambda item: item[1][0])  # sort by start position

        # 4. Extract text for each section
        raw: dict[str, str] = {}
        for idx, (heading, (start, end)) in enumerate(ordered):
            section_text = self._extract_section_text(
                response=response,
                ordered=ordered,
                current_idx=idx,
                heading_end=end,  # use the end of the match to skip the heading
            )
            raw[heading] = section_text

        # 5. Build the dataclass
        sections = AISections(
            executive_summary=raw[_EXECUTIVE_SUMMARY],
            recommendations=self._parse_bullet_list(raw[_RECOMMENDATIONS]),
            explanations=self._parse_bullet_list(raw[_EXPLANATIONS]),
            narrative=raw[_NARRATIVE],
        )

        # 6. Validate mandatory sections (executive summary and narrative must have content)
        if not sections.executive_summary.strip():
            raise ValueError("Executive summary is empty.")
        if not sections.narrative.strip():
            raise ValueError("Narrative is empty.")

        # Warning for optional list sections
        if not sections.recommendations:
            logger.warning("No recommendations generated.")
        if not sections.explanations:
            logger.warning("No explanations generated.")

        return sections

    def _find_headings(self, response: str) -> dict[str, tuple[int, int]]:
        """
        Locate all required headings in the response.

        Returns a dictionary mapping heading name to a tuple (start, end) of the match.
        Raises ValueError if a heading is duplicated.

        Parameters
        ----------
        response : str
            The raw LLM output.

        Returns
        -------
        dict[str, tuple[int, int]]
            Mapping from heading name to (start, end) positions.

        Raises
        ------
        ValueError
            If a heading appears more than once.
        """
        headings: dict[str, tuple[int, int]] = {}

        for heading, pattern in self._heading_patterns.items():
            matches = list(pattern.finditer(response))
            if not matches:
                continue
            if len(matches) > 1:
                raise ValueError(
                    f"Duplicate heading detected: {heading}. "
                    f"Expected exactly one occurrence."
                )
            match = matches[0]
            headings[heading] = (match.start(), match.end())

        return headings

    def _detect_truncation(self, response: str, headings: dict[str, tuple[int, int]]) -> str | None:
        """
        Detect whether the response appears to be truncated before the missing sections.

        Heuristics:
        - Response ends with an incomplete structure (e.g., colon, comma, quote, bracket).
        - Response length near or exceeding estimated max token capacity.
        - Last found heading is a required one and the text after it is very short or missing.

        Returns a diagnostic message if truncation is suspected, else None.
        """
        # If all headings are present, no truncation issue
        if set(headings.keys()) == set(_SECTION_NAMES):
            return None

        # Check for obvious incomplete endings
        if self._looks_truncated(response):
            return (
                f"The response appears to be truncated mid-structure (ends with an incomplete character). "
                f"Response length: {len(response)} characters. "
                f"Consider increasing the LLM output token limit (currently likely 512 tokens) or reducing the prompt size."
            )

        # Check if response is near the estimated max length
        if len(response) >= _ESTIMATED_MAX_CHARS * 0.85:
            return (
                f"Response length ({len(response)} chars) is close to the estimated maximum "
                f"({_ESTIMATED_MAX_CHARS} chars for 512 tokens). This suggests the response may have been truncated.\n"
                f"Consider increasing the LLM output token limit or reducing the prompt size."
            )

        # Check if response ends with a heading alias (or partial heading)
        lines = response.splitlines()
        if lines:
            last_line = lines[-1].strip()
            if self._any_heading_pattern.match(last_line):
                return (
                    f"Response ends with a heading-like line: '{last_line}'. "
                    "This likely indicates truncation immediately after that heading, before content was generated.\n"
                    f"Consider increasing the LLM output token limit or reducing the prompt size."
                )
            # If last line ends with a colon or is very short, could be truncation
            if last_line.endswith(":") or len(last_line) < 20:
                return (
                    f"Response ends with a partial line: '{last_line}'. "
                    "This may indicate truncation in the middle of content.\n"
                    f"Consider increasing the LLM output token limit or reducing the prompt size."
                )

        # If the last found heading is one of the later ones (e.g., RECOMMENDATIONS) and missing later ones
        # check if the text after the last found heading is empty or only whitespace
        if headings:
            last_heading = max(headings.items(), key=lambda item: item[1][0])
            heading_name, (start, end) = last_heading
            rest = response[end:].strip()
            if not rest:
                return (
                    f"The last found heading is '{heading_name}', but no content follows it. "
                    "The response was likely cut off just after this heading.\n"
                    f"Consider increasing the LLM output token limit or reducing the prompt size."
                )

        return None

    def _looks_truncated(self, response: str) -> bool:
        """
        Return True if the response ends with a character that suggests it was cut off mid-content.
        """
        text = response.rstrip()
        if not text:
            return False
        return (
            text.endswith(":")
            or text.endswith("{")
            or text.endswith("[")
            or text.endswith(",")
            or text.endswith("'")
            or text.endswith('"')
            or text.endswith("...")   # sometimes models emit ellipsis before cutoff
        )

    def _extract_section_text(
        self,
        response: str,
        ordered: list[tuple[str, tuple[int, int]]],
        current_idx: int,
        heading_end: int,
    ) -> str:
        """
        Extract the text of a single section, starting immediately after the heading match.

        Filters out blank lines and markdown-style separator lines (e.g., "---", "===", "___").

        Parameters
        ----------
        response : str
            The full response string.
        ordered : list[tuple[str, tuple[int, int]]]
            All found headings with their (start, end) positions in order.
        current_idx : int
            Index of the current heading in the ordered list.
        heading_end : int
            The character position right after the heading match.

        Returns
        -------
        str
            The extracted section text, with blank and separator lines removed.
        """
        # Start after the heading
        body_start = heading_end

        # Find the next heading's start (if any)
        if current_idx == len(ordered) - 1:
            body_end = len(response)
        else:
            body_end = ordered[current_idx + 1][1][0]  # start of next heading

        # Extract the raw section
        section = response[body_start:body_end]

        # Process lines: filter out blanks and separator lines
        lines = []
        for line in section.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Skip markdown separator lines (e.g., ---, ===, ___, etc.)
            if re.fullmatch(r"[-=_]{3,}", stripped):
                continue
            lines.append(stripped)

        return "\n".join(lines).strip()

    def _parse_bullet_list(self, text: str) -> list[str]:
        """
        Convert a bullet list section into a clean list of strings.

        Supports lines starting with:
        -   •   *   or numbers (1.  2.  etc.)
        Removes extraneous whitespace.

        Parameters
        ----------
        text : str
            The raw section text.

        Returns
        -------
        list[str]
            The extracted list items.
        """
        items: list[str] = []
        for line in text.splitlines():
            cleaned = _BULLET_PATTERN.sub("", line).strip()
            if cleaned:
                items.append(cleaned)
        return items

    # ==========================================================
    # Performance Logging
    # ==========================================================

    def _log_performance(
        self,
        prompt_time: float,
        llm_time: float,
        parse_time: float,
        total_time: float,
        response: str,
        sections: AISections,
    ) -> None:
        """
        Log detailed performance metrics and section statistics.

        Parameters
        ----------
        prompt_time : float
            Time spent building the prompt.
        llm_time : float
            Time spent in the LLM call.
        parse_time : float
            Time spent parsing the response.
        total_time : float
            Total generation time.
        response : str
            The raw LLM response (for length logging).
        sections : AISections
            The parsed sections.
        """
        logger.info(_LOG_SEPARATOR)
        logger.info("Report Generation Performance:")
        logger.info("  Prompt Build : %.3f s", prompt_time)
        logger.info("  LLM Call     : %.3f s", llm_time)
        logger.info("  Parsing      : %.3f s", parse_time)
        logger.info("  Total        : %.3f s", total_time)
        logger.info("  Response Length : %d chars", len(response))
        logger.info("Section Metrics:")
        logger.info(
            "  Executive Summary : %d chars",
            len(sections.executive_summary),
        )
        logger.info(
            "  Recommendations   : %d items",
            len(sections.recommendations),
        )
        logger.info(
            "  Explanations      : %d items",
            len(sections.explanations),
        )
        logger.info(
            "  Narrative         : %d chars",
            len(sections.narrative),
        )
        logger.info(_LOG_SEPARATOR)