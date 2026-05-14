"""
Convert a Tiptap/ProseMirror JSON document into HTML suitable for our print
templates. Only the node types actually produced by the editor are handled;
unknown types are silently skipped.
"""
from html import escape


_INLINE_MARKS = {
    "bold": ("strong", "tt-strong"),
    "italic": ("em", "tt-em"),
    "code": ("code", "tt-code"),
}


def _render_text_node(node: dict) -> str:
    text = escape(node.get("text", ""))
    for mark in node.get("marks") or []:
        spec = _INLINE_MARKS.get(mark.get("type"))
        if not spec:
            continue
        tag, cls = spec
        text = f'<{tag} class="{cls}">{text}</{tag}>'
    return text


def _render_children(node: dict) -> str:
    return "".join(_render(child) for child in node.get("content") or [])


def _render(node: dict) -> str:
    t = node.get("type")
    if t == "text":
        return _render_text_node(node)
    if t == "paragraph":
        body = _render_children(node)
        return f'<p class="tt-p">{body or "&nbsp;"}</p>'
    if t == "heading":
        level = (node.get("attrs") or {}).get("level", 2)
        level = 2 if level not in (2, 3) else level  # cap at h2/h3 in print
        return f'<h{level} class="tt-h{level}">{_render_children(node)}</h{level}>'
    if t == "bullet_list" or t == "bulletList":
        return f'<ul class="tt-ul">{_render_children(node)}</ul>'
    if t == "ordered_list" or t == "orderedList":
        return f'<ol class="tt-ol">{_render_children(node)}</ol>'
    if t == "list_item" or t == "listItem":
        return f'<li class="tt-li">{_render_children(node)}</li>'
    if t == "hard_break" or t == "hardBreak":
        return "<br/>"
    if t == "blockquote":
        return f'<blockquote class="tt-bq">{_render_children(node)}</blockquote>'
    if t == "doc":
        return _render_children(node)
    # Unknown / unsupported node types: render their children if any
    return _render_children(node)


def tiptap_to_html(doc: dict | None) -> str:
    """Public entry point. Returns sanitized HTML (no <script>, no on* attrs)."""
    if not doc or not isinstance(doc, dict):
        return ""
    return _render(doc)
