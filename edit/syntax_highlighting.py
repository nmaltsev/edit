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
    ".jsm": "javascript",
    ".tsm": "typescript",
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


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def get_language(path):
    if not path:
        return None

    filename = os.path.basename(path)

    if filename in SUPPORTED_FILENAMES:
        return SUPPORTED_FILENAMES[filename]

    if filename.endswith(".Dockerfile"):
        return "dockerfile"

    _, ext = os.path.splitext(filename)

    return SUPPORTED_EXTENSIONS.get(ext.lower())


# ---------------------------------------------------------------------------
# Span helpers
#
# A span is:
#
#     (start, end, token_type)
#
# where start/end are offsets in the COMPLETE DOCUMENT.
# ---------------------------------------------------------------------------

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


def _overlaps(start, end, spans):
    for other_start, other_end, _ in spans:
        if start < other_end and end > other_start:
            return True

    return False


def _add_non_overlapping(spans, new_spans):
    """
    Add spans while preventing lower-priority rules from entering
    already-tokenized regions.
    """
    for start, end, token_type in new_spans:
        if start >= end:
            continue

        if not _overlaps(start, end, spans):
            spans.append((start, end, token_type))


def _sort_spans(spans):
    return sorted(
        spans,
        key=lambda item: (
            item[0],
            -(item[1] - item[0]),
        ),
    )


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

PYTHON_STRING_PATTERN = (
    # Triple quoted strings MUST come before normal strings.
    r'(?:"""(?:\\.|[\s\S])*?""")'
    r"|(?:'''(?:\\.|[\s\S])*?''')"
    r'|(?:"(?:\\.|[^"\\\n])*")'
    r"|'(?:\\.|[^'\\\n])*'"
)


def _python_spans(text):
    spans = []

    # Strings have highest priority.
    string_spans = _build_spans(
        PYTHON_STRING_PATTERN,
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    # Comments.
    comment_spans = _build_spans(
        r"#.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    # Numbers.
    number_spans = _build_spans(
        r"\b(?:0[xX][0-9a-fA-F]+|0[bB][01]+|"
        r"0[oO][0-7]+|\d+(?:\.\d+)?)\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    # Keywords.
    keyword_pattern = (
        r"\b(?:"
        + "|".join(re.escape(word) for word in keyword.kwlist)
        + r")\b"
    )

    keyword_spans = _build_spans(
        keyword_pattern,
        "keyword",
        text,
    )
    _add_non_overlapping(spans, keyword_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def _json_spans(text):
    spans = []

    # JSON properties first.
    property_spans = _build_spans(
        r'"(?:\\.|[^"\\])*"\s*(?=:)',
        "property",
        text,
    )
    _add_non_overlapping(spans, property_spans)

    string_spans = _build_spans(
        r'"(?:\\.|[^"\\])*"',
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    number_spans = _build_spans(
        r"-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# YAML
# ---------------------------------------------------------------------------

def _yaml_spans(text):
    spans = []

    property_spans = _build_spans(
        r"^[ ]*[\w.-]+(?=\s*:)",
        "property",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, property_spans)

    string_spans = _build_spans(
        PYTHON_STRING_PATTERN,
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    comment_spans = _build_spans(
        r"(?<!\\)#.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    number_spans = _build_spans(
        r"(?<![\w.-])-?\b\d+(?:\.\d+)?\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# HTML / SVG
# ---------------------------------------------------------------------------

def _html_spans(text):
    spans = []

    # HTML comments.
    comment_spans = _build_spans(
        r"<!--[\s\S]*?-->",
        "comment",
        text,
    )
    _add_non_overlapping(spans, comment_spans)

    # Tags.
    tag_spans = _build_spans(
        r"</?[A-Za-z][A-Za-z0-9_.:-]*",
        "tag",
        text,
    )
    _add_non_overlapping(spans, tag_spans)

    # Attributes.
    attribute_spans = _build_spans(
        r'(?<![\w-])([A-Za-z_:][\w:.-]*)(?=\s*=)',
        "property",
        text,
    )
    _add_non_overlapping(spans, attribute_spans)

    # Double-quoted attribute values.
    string_spans = _build_spans(
        r'"(?:\\.|[^"\\])*"',
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    # Single-quoted attribute values.
    string_spans = _build_spans(
        r"'(?:\\.|[^'\\])*'",
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def _css_spans(text):
    spans = []

    comment_spans = _build_spans(
        r"/\*[\s\S]*?\*/",
        "comment",
        text,
    )
    _add_non_overlapping(spans, comment_spans)

    string_spans = _build_spans(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    # CSS classes.
    class_spans = _build_spans(
        r"(?<![\w-])\.[A-Za-z_-][A-Za-z0-9_-]*",
        "tag",
        text,
    )
    _add_non_overlapping(spans, class_spans)

    # CSS IDs.
    id_spans = _build_spans(
        r"#[A-Za-z0-9_-]+",
        "property",
        text,
    )
    _add_non_overlapping(spans, id_spans)

    # Numbers.
    number_spans = _build_spans(
        r"\b\d+(?:\.\d+)?(?:px|em|rem|vh|vw|vmin|vmax|%|s|ms|deg)?\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# JavaScript / TypeScript / JSX
# ---------------------------------------------------------------------------

JS_STRING_PATTERN = (
    r"`(?:\\.|[\s\S])*?`"
    r'|"(?:\\.|[^"\\\n])*"'
    r"|'(?:\\.|[^'\\\n])*'"
)


def _jsx_html_spans(text):
    spans = []

    tag_spans = _build_spans(
        r"</?[A-Za-z_][A-Za-z0-9_.:-]*",
        "tag",
        text,
    )
    _add_non_overlapping(spans, tag_spans)

    attribute_spans = _build_spans(
        r"(?<![\w-])([A-Za-z_:][\w:.-]*)(?=\s*=)",
        "property",
        text,
    )
    _add_non_overlapping(spans, attribute_spans)

    double_string_spans = _build_spans(
        r'"(?:\\.|[^"\\])*"',
        "string",
        text,
    )
    _add_non_overlapping(spans, double_string_spans)

    single_string_spans = _build_spans(
        r"'(?:\\.|[^'\\])*'",
        "string",
        text,
    )
    _add_non_overlapping(spans, single_string_spans)

    return spans


def _javascript_spans(text):
    spans = []

    # Block comments can span many lines.
    comment_spans = _build_spans(
        r"/\*[\s\S]*?\*/",
        "comment",
        text,
    )
    _add_non_overlapping(spans, comment_spans)

    # Line comments.
    comment_spans = _build_spans(
        r"//.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    # Strings, including multiline template literals.
    string_spans = _build_spans(
        JS_STRING_PATTERN,
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    number_spans = _build_spans(
        r"\b(?:0[xX][0-9a-fA-F]+|0[bB][01]+|"
        r"\d+(?:\.\d+)?)\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    jsx_spans = _jsx_html_spans(text)

    for span in jsx_spans:
        if not _overlaps(span[0], span[1], spans):
            spans.append(span)

    keyword_pattern = (
        r"\b(?:"
        + "|".join(re.escape(word) for word in JS_KEYWORDS)
        + r")\b"
    )

    keyword_spans = _build_spans(
        keyword_pattern,
        "keyword",
        text,
    )
    _add_non_overlapping(spans, keyword_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# PHP
# ---------------------------------------------------------------------------

def _php_spans(text):
    spans = []

    # Block comments.
    comment_spans = _build_spans(
        r"/\*[\s\S]*?\*/",
        "comment",
        text,
    )
    _add_non_overlapping(spans, comment_spans)

    # // comments.
    comment_spans = _build_spans(
        r"//.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    # # comments.
    comment_spans = _build_spans(
        r"#.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    # Strings.
    string_spans = _build_spans(
        PYTHON_STRING_PATTERN,
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    # Numbers.
    number_spans = _build_spans(
        r"\b\d+(?:\.\d+)?\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    keyword_pattern = (
        r"\b(?:"
        + "|".join(re.escape(word) for word in PHP_KEYWORDS)
        + r")\b"
    )

    keyword_spans = _build_spans(
        keyword_pattern,
        "keyword",
        text,
    )
    _add_non_overlapping(spans, keyword_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# Dockerfile
# ---------------------------------------------------------------------------

def _dockerfile_spans(text):
    spans = []

    comment_spans = _build_spans(
        r"#.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    string_spans = _build_spans(
        PYTHON_STRING_PATTERN,
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    keyword_pattern = (
        r"^[ \t]*(?:"
        + "|".join(re.escape(word) for word in DOCKERFILE_KEYWORDS)
        + r")\b"
    )

    keyword_spans = _build_spans(
        keyword_pattern,
        "keyword",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    _add_non_overlapping(spans, keyword_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# Bash / Shell
# ---------------------------------------------------------------------------

BASH_KEYWORDS = {
    "if",
    "then",
    "else",
    "elif",
    "fi",
    "for",
    "while",
    "do",
    "done",
    "case",
    "esac",
    "in",
    "function",
    "select",
}


def _bash_spans(text):
    spans = []

    comment_spans = _build_spans(
        r"#.*$",
        "comment",
        text,
        re.MULTILINE,
    )
    _add_non_overlapping(spans, comment_spans)

    string_spans = _build_spans(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        "string",
        text,
    )
    _add_non_overlapping(spans, string_spans)

    number_spans = _build_spans(
        r"\b\d+(?:\.\d+)?\b",
        "number",
        text,
    )
    _add_non_overlapping(spans, number_spans)

    keyword_pattern = (
        r"\b(?:"
        + "|".join(re.escape(word) for word in BASH_KEYWORDS)
        + r")\b"
    )

    keyword_spans = _build_spans(
        keyword_pattern,
        "keyword",
        text,
    )
    _add_non_overlapping(spans, keyword_spans)

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

MARKDOWN_LANGUAGE_MAP = {
    "py": "python",
    "python": "python",
    "python3": "python",

    "js": "javascript",
    "javascript": "javascript",

    "jsx": "jsx",

    "ts": "typescript",
    "typescript": "typescript",

    "tsx": "tsx",

    "json": "json",

    "yaml": "yaml",
    "yml": "yaml",

    "html": "html",
    "htm": "html",

    "css": "css",

    "php": "php",

    "sh": "bash",
    "bash": "bash",

    "dockerfile": "dockerfile",
}


def _markdown_fenced_blocks(text):
    """
    Return:

        (opening_start, opening_end,
         content_start, content_end,
         closing_start, closing_end,
         language)

    for every fenced code block.
    """

    blocks = []

    # Supports:
    #
    # ```python
    # code
    # ```
    #
    # and:
    #
    # ~~~python
    # code
    # ~~~
    #
    pattern = re.compile(
        r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*"
        r"([A-Za-z0-9_+#.-]*)[^\n]*\n"
        r"([\s\S]*?)"
        r"^[ \t]{0,3}\1[ \t]*(?:\n|$)",
        re.MULTILINE,
    )

    for match in pattern.finditer(text):
        fence = match.group(1)
        language_name = match.group(2).strip().lower()

        opening_start = match.start()
        opening_end = match.start(3)

        content_start = match.start(3)
        content_end = match.end(3)

        closing_end = match.end()
        closing_line_start = text.rfind("\n", 0, match.end(3))

        if closing_line_start == -1:
            closing_line_start = match.end(3)
        else:
            closing_line_start += 1

        closing_start = closing_line_start

        # The regexp's group 3 includes the content immediately before
        # the closing fence.
        closing_start = match.end(3)

        # Remove the newline immediately before the closing fence.
        if closing_start > content_start and text[closing_start - 1] == "\n":
            closing_start -= 1

        content_end = closing_start

        blocks.append(
            (
                opening_start,
                opening_end,
                content_start,
                content_end,
                closing_start,
                closing_end,
                MARKDOWN_LANGUAGE_MAP.get(language_name),
            )
        )

    return blocks


def _markdown_inline_spans(text, excluded_ranges):
    spans = []

    def add(pattern, token_type):
        for match in re.finditer(pattern, text, re.MULTILINE):
            start = match.start()
            end = match.end()

            blocked = False

            for block_start, block_end in excluded_ranges:
                if start < block_end and end > block_start:
                    blocked = True
                    break

            if not blocked and not _overlaps(start, end, spans):
                spans.append((start, end, token_type))

    # Headings.
    add(
        r"^[ \t]{0,3}#{1,6}[ \t]+.*$",
        "keyword",
    )

    # Blockquotes.
    add(
        r"^[ \t]{0,3}>.*$",
        "comment",
    )

    # Unordered lists.
    add(
        r"^[ \t]{0,3}(?:[-+*])[ \t]+",
        "keyword",
    )

    # Ordered lists.
    add(
        r"^[ \t]{0,3}\d+\.[ \t]+",
        "keyword",
    )

    # Horizontal rules.
    add(
        r"^[ \t]{0,3}(?:\*\s*){3,}$|"
        r"^[ \t]{0,3}(?:-\s*){3,}$|"
        r"^[ \t]{0,3}(?:_\s*){3,}$",
        "keyword",
    )

    # Links.
    add(
        r"\[[^\]\n]+\]\([^)]+\)",
        "tag",
    )

    # Images.
    add(
        r"!\[[^\]\n]*\]\([^)]+\)",
        "property",
    )

    # Inline code.
    add(
        r"`[^`\n]+`",
        "string",
    )

    # Bold.
    add(
        r"\*\*[^*\n]+\*\*|__[^_\n]+__",
        "property",
    )

    # Italic.
    add(
        r"(?<!\*)\*[^*\n]+\*(?!\*)|"
        r"(?<!_)_[^_\n]+_(?!_)",
        "property",
    )

    # Strikethrough.
    add(
        r"~~[^~\n]+~~",
        "comment",
    )

    # Markdown HTML tags.
    add(
        r"</?[A-Za-z][A-Za-z0-9_.:-]*(?:\s+[^>]*?)?/?>",
        "tag",
    )

    return _sort_spans(spans)


def _markdown_spans(text):
    spans = []

    blocks = _markdown_fenced_blocks(text)

    excluded_ranges = []

    # Highlight fenced code blocks.
    for (
        opening_start,
        opening_end,
        content_start,
        content_end,
        closing_start,
        closing_end,
        language,
    ) in blocks:

        excluded_ranges.append((opening_start, closing_end))

        # Fence itself.
        spans.append(
            (
                opening_start,
                opening_end,
                "keyword",
            )
        )

        # If we know the fenced language, use its normal tokenizer.
        if language:
            code_text = text[content_start:content_end]

            code_spans = _language_spans(
                language,
                code_text,
            )

            for start, end, token_type in code_spans:
                spans.append(
                    (
                        content_start + start,
                        content_start + end,
                        token_type,
                    )
                )
        else:
            # Unknown fenced language: show the code as a string.
            if content_start < content_end:
                spans.append(
                    (
                        content_start,
                        content_end,
                        "string",
                    )
                )

        # Closing fence.
        spans.append(
            (
                closing_start,
                closing_end,
                "keyword",
            )
        )

    # Markdown syntax outside fenced blocks.
    spans.extend(
        _markdown_inline_spans(
            text,
            excluded_ranges,
        )
    )

    return _sort_spans(spans)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _language_spans(language, text):
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

    if language == "bash":
        return _bash_spans(text)

    if language == "markdown":
        return _markdown_spans(text)

    return []


# ---------------------------------------------------------------------------
# Document-level tokenizer
# ---------------------------------------------------------------------------

def tokenize_document(path, text):
    """
    Tokenize the COMPLETE document.

    This is the important change from the original implementation.

    Multiline constructs cannot be correctly recognized if the highlighter
    only receives one line at a time.
    """

    if not ENABLE_SYNTAX_HIGHLIGHTING:
        return []

    language = get_language(path)

    if not language:
        return []

    return _language_spans(language, text)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_text_with_spans(text, spans):
    """
    Render a complete piece of text using spans whose offsets refer
    to that same piece of text.
    """

    if not spans:
        return text

    spans = _sort_spans(spans)

    result = []
    pos = 0

    for start, end, token_type in spans:
        if start < pos:
            continue

        if start > len(text):
            break

        end = min(end, len(text))

        result.append(text[pos:start])
        result.append(COLORS[token_type])
        result.append(text[start:end])
        result.append(RESET)

        pos = end

    result.append(text[pos:])

    return "".join(result)


def render_document(path, text):
    """
    Highlight an entire document.

    Returns the highlighted document as a string.

    This is the preferred API.
    """

    if not ENABLE_SYNTAX_HIGHLIGHTING:
        return text

    spans = tokenize_document(path, text)

    return _render_text_with_spans(text, spans)


def render_lines(path, text):
    """
    Highlight a complete document and return a list of rendered lines.

    This is useful if your terminal/editor already works with a list
    of lines.

    Example:

        lines = render_lines("test.py", source)

        for line in lines:
            print(line, end="")
    """

    if not ENABLE_SYNTAX_HIGHLIGHTING:
        return text.splitlines(keepends=True)

    spans = tokenize_document(path, text)

    if not spans:
        return text.splitlines(keepends=True)

    # Map each document span to the appropriate line.
    result = []

    lines = text.splitlines(keepends=True)

    if not lines:
        return []

    # Start offset of every line.
    line_starts = []
    offset = 0

    for line in lines:
        line_starts.append(offset)
        offset += len(line)

    span_index = 0

    for line_index, line in enumerate(lines):
        line_start = line_starts[line_index]
        line_end = line_start + len(line)

        line_spans = []

        while span_index < len(spans):
            span_start, span_end, token_type = spans[span_index]

            if span_end <= line_start:
                span_index += 1
                continue

            if span_start >= line_end:
                break

            local_start = max(span_start, line_start) - line_start
            local_end = min(span_end, line_end) - line_start

            if local_start < local_end:
                line_spans.append(
                    (
                        local_start,
                        local_end,
                        token_type,
                    )
                )

            if span_end <= line_end:
                span_index += 1
            else:
                break

        result.append(
            _render_text_with_spans(
                line,
                line_spans,
            )
        )

    return result


def render_line(path, text):
    """
    Backwards-compatible helper.

    IMPORTANT:

    If `text` is an entire document, this works correctly for multiline
    constructs.

    If `text` is literally only ONE LINE of a larger document, multiline
    syntax cannot be known from that line alone.

    Prefer:

        render_document(path, document)

    or:

        render_lines(path, document)
    """

    return render_document(path, text)


# ---------------------------------------------------------------------------
# Optional stateful highlighter
# ---------------------------------------------------------------------------

class SyntaxHighlighter:
    """
    Convenience wrapper for applications that keep a document in memory.

    Example:

        highlighter = SyntaxHighlighter("example.py")

        output = highlighter.render(source)

    """

    def __init__(self, path):
        self.path = path

    def tokenize(self, text):
        return tokenize_document(self.path, text)

    def render(self, text):
        return render_document(self.path, text)

    def render_lines(self, text):
        return render_lines(self.path, text)


# ---------------------------------------------------------------------------
# Simple demonstration / self-test
# ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     python_example = '''\
# def hello():
#     message = """
# This is a multiline string.
# It contains the word return.
# It contains the number 123.
# """
#     # This is a comment.
#     return message
# '''

#     markdown_example = '''\
# # Markdown heading

# This is **bold**, this is *italic*, and this is `inline code`.

# > This is a blockquote.

# - First item
# - Second item

# [OpenAI](https://openai.com)

# ```python
# def hello():
#     message = """
# This is a multiline Python string.
# """
#     return message