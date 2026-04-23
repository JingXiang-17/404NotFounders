from __future__ import annotations

from html.parser import HTMLParser

from app.core.exceptions import DependencyNotAvailableError

try:
    import trafilatura  # type: ignore
except ImportError:  # pragma: no cover - exercised through runtime behavior
    trafilatura = None


class _FallbackHTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.chunks.append(data.strip())

    def text(self) -> str:
        return "\n".join(self.chunks)


class TrafilaturaExtractor:
    def extract_text(self, html: str) -> str:
        if trafilatura is not None:
            result = trafilatura.extract(html, include_comments=False, include_tables=False)
            if result:
                return result
        parser = _FallbackHTMLTextExtractor()
        parser.feed(html)
        text = parser.text()
        if not text.strip():
            raise DependencyNotAvailableError(
                "Trafilatura is not installed and fallback extraction produced empty text."
            )
        return text

