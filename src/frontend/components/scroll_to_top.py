"""
Scroll-to-top component for AnalystGPT Enterprise.

Resets the scroll position of the main Streamlit container to the top
when navigating between views.
"""

from __future__ import annotations

import streamlit.components.v1 as components


def scroll_to_top() -> None:
    """
    Reset viewport scroll position to the top.

    Executes a clientside JavaScript scroll reset targeting the Streamlit
    main container (.main), the document root, and the parent window.
    """
    js_code = """
    <script>
        try {
            const selectors = [
                '.main',
                '[data-testid="stAppViewContainer"]',
                '[data-testid="stMainBlockContainer"]',
                'section.main'
            ];
            for (const sel of selectors) {
                const el = window.parent.document.querySelector(sel);
                if (el && typeof el.scrollTo === 'function') {
                    el.scrollTo({top: 0, left: 0, behavior: 'auto'});
                }
            }
            if (window.parent.document.documentElement) {
                window.parent.document.documentElement.scrollTo({top: 0, left: 0, behavior: 'auto'});
            }
            window.parent.scrollTo({top: 0, left: 0, behavior: 'auto'});
        } catch (e) {
            // Ignore cross-origin or non-browser test environment exceptions
        }
    </script>
    """
    components.html(js_code, height=0, width=0)
