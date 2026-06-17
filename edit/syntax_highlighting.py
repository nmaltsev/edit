import keyword
import os
import re

ENABLE_SYNTAX_HIGHLIGHTING = True

RESET = "\033[0m"

COLORS = {
    "keyword": "\033[94m",
    "string": "\033[92m",
    "comment": "\033[90m",
    "number": "\033[96m",
    "tag": "\033[95m",
    "property": "\033[36m",
}


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".svg": "svg",
    ".css": "css",
    ".php": "php",
    ".sh": "bash",
    ".bash": "bash",
}


SUPPORTED_FILENAMES = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
}


JS_KEYWORDS = {
    "const",
    "let",
    "var",
    "function",
    "return",
    "if",
    "else",
    "for",
    "while",
    "class",
    "new",
    "import",
    "export",
    "extends",
    "interface",
    "type",
    "enum",
    "implements",
    "async",
    "await",
    "from",
    "try",
    "catch",
    "finally",
    "throw",
    "default",
}


PHP_KEYWORDS = {
    "function",
    "class",
    "public",
    "private",
    "protected",
    "static",
    "return",
    "if",
    "else",
    "elseif",
    "foreach",
    "for",
    "while",
    "new",
    "namespace",
    "use",
    "trait",
    "interface",
}


DOCKERFILE_KEYWORDS = {
    "FROM",
    "RUN",
    "CMD",
    "ENTRYPOINT",
    "WORKDIR",
    "COPY",
    "ADD",
    "ENV",
    "ARG",
    "LABEL",
    "EXPOSE",
    "USER",
    "VOLUME",
    "SHELL",
    "STOPSIGNAL",
    "HEALTHCHECK",
    "ONBUILD",
}


STRING_PATTERN = (
    r'"""(?:.|\n)*?"""'
    r"|'''(?:.|\n)*?'''"
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
)

JS_STRING_PATTERN = (
    r'`(?:\\.|[^`\\])*`'
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
)


def get_language(path):
    if not path:
        return None

    filename = os.path.basename(path)

    if filename in SUPPORTED_FILENAMES:
        return SUPPORTED_FILENAMES[filename]

    if filename.endswith(".Dockerfile"):
        return "dockerfile"

    _, ext = os.path.splitext(filename)

    return SUPPORTED_EXTENSIONS.get(ext)


def _build_spans(pattern, token_type, text, flags=0):
    spans = []

    for match in re.finditer(pattern, text, flags):
        spans.append(
            (
                match.start(),
                match.end(),
                token_type,
            )
        )

    return spans


def _python_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            STRING_PATTERN,
            "string",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            r"#.*$",
            "comment",
            text,
            re.MULTILINE,
        )
    )

    spans.extend(
        _build_spans(
            r"\b\d+(?:\.\d+)?\b",
            "number",
            text,
        )
    )

    for kw in keyword.kwlist:
        spans.extend(
            _build_spans(
                rf"\b{re.escape(kw)}\b",
                "keyword",
                text,
            )
        )

    return spans


def _json_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r'"(?:\\.|[^"\\])*"\s*:',
            "property",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r'"(?:\\.|[^"\\])*"',
            "string",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r"\b\d+(?:\.\d+)?\b",
            "number",
            text,
        )
    )

    return spans


def _yaml_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"^[ ]*[\w\-]+:",
            "property",
            text,
            re.MULTILINE,
        )
    )

    spans.extend(
        _build_spans(
            STRING_PATTERN,
            "string",
            text,
            re.DOTALL,
        )
    )

    return spans


def _html_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"<!--(?:.|\n)*?-->",
            "comment",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            r"</?[\w:\-]+",
            "tag",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r'=\s*"(?:\\.|[^"\\])*"',
            "string",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r"=\s*'(?:\\.|[^'\\])*'",
            "string",
            text,
        )
    )

    return spans


def _css_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"/\*(?:.|\n)*?\*/",
            "comment",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            STRING_PATTERN,
            "string",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            r"(?<![\w-])\.[A-Za-z_-][A-Za-z0-9_-]*",
            "tag",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r"#[A-Za-z0-9_-]+",
            "property",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r"\b\d+(?:\.\d+)?(?:px|em|rem|vh|vw|%)?\b",
            "number",
            text,
        )
    )

    return spans


def _jsx_html_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"</?[A-Za-z_][A-Za-z0-9_.:-]*",
            "tag",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r'=\s*"(?:\\.|[^"\\])*"',
            "string",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r"=\s*'(?:\\.|[^'\\])*'",
            "string",
            text,
        )
    )

    return spans


def _javascript_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"/\*(?:.|\n)*?\*/",
            "comment",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            r"//.*$",
            "comment",
            text,
            re.MULTILINE,
        )
    )

    spans.extend(
        _build_spans(
            JS_STRING_PATTERN,
            "string",
            text,
        )
    )

    spans.extend(
        _build_spans(
            r"\b\d+(?:\.\d+)?\b",
            "number",
            text,
        )
    )

    spans.extend(
        _jsx_html_spans(text)
    )

    for kw in JS_KEYWORDS:
        spans.extend(
            _build_spans(
                rf"\b{kw}\b",
                "keyword",
                text,
            )
        )

    return spans


def _php_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"/\*(?:.|\n)*?\*/",
            "comment",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            r"//.*$",
            "comment",
            text,
            re.MULTILINE,
        )
    )

    spans.extend(
        _build_spans(
            r"#.*$",
            "comment",
            text,
            re.MULTILINE,
        )
    )

    spans.extend(
        _build_spans(
            STRING_PATTERN,
            "string",
            text,
            re.DOTALL,
        )
    )

    spans.extend(
        _build_spans(
            r"\b\d+(?:\.\d+)?\b",
            "number",
            text,
        )
    )

    for kw in PHP_KEYWORDS:
        spans.extend(
            _build_spans(
                rf"\b{kw}\b",
                "keyword",
                text,
            )
        )

    return spans


def _dockerfile_spans(text):
    spans = []

    spans.extend(
        _build_spans(
            r"#.*$",
            "comment",
            text,
            re.MULTILINE,
        )
    )

    spans.extend(
        _build_spans(
            STRING_PATTERN,
            "string",
            text,
            re.DOTALL,
        )
    )

    for kw in DOCKERFILE_KEYWORDS:
        spans.extend(
            _build_spans(
                rf"^{kw}\b",
                "keyword",
                text,
                re.MULTILINE,
            )
        )

    return spans


def tokenize_line(path, text):
    if not ENABLE_SYNTAX_HIGHLIGHTING:
        return []

    language = get_language(path)

    if language == "python":
        return _python_spans(text)

    if language == "json":
        return _json_spans(text)

    if language == "yaml":
        return _yaml_spans(text)

    if language in ("html", "svg"):
        return _html_spans(text)

    if language == "css":
        return _css_spans(text)

    if language in (
        "javascript",
        "jsx",
        "typescript",
        "tsx",
    ):
        return _javascript_spans(text)

    if language == "php":
        return _php_spans(text)

    if language == "dockerfile":
        return _dockerfile_spans(text)

    return []


def render_line(path, text):
    spans = tokenize_line(path, text)

    if not spans:
        return text

    spans.sort(
        key=lambda item: (
            item[0],
            -(item[1] - item[0]),
        )
    )

    result = []
    pos = 0

    for start, end, token_type in spans:
        if start < pos:
            continue

        result.append(text[pos:start])
        result.append(COLORS[token_type])
        result.append(text[start:end])
        result.append(RESET)

        pos = end

    result.append(text[pos:])

    return "".join(result)