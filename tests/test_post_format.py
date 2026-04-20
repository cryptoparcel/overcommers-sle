"""Tests for the post_format helper — renders a plain-text post with a
small, safe set of markdown-style formatting."""

from __future__ import annotations

from app.utils import format_post_body


def test_plain_text_passes_through():
    out = str(format_post_body("hello there"))
    assert out == "hello there"


def test_bold_wraps_in_strong():
    out = str(format_post_body("say **hi** now"))
    assert "<strong>hi</strong>" in out


def test_explicit_link():
    out = str(format_post_body("see [docs](https://example.com)"))
    assert '<a href="https://example.com"' in out
    assert ">docs</a>" in out
    assert "target=\"_blank\"" in out
    assert "rel=\"noopener nofollow\"" in out


def test_bare_url_auto_links():
    out = str(format_post_body("visit https://example.com today"))
    assert '<a href="https://example.com"' in out
    assert ">https://example.com</a>" in out


def test_bare_url_inside_explicit_link_not_double_wrapped():
    out = str(format_post_body("see [here](https://example.com)"))
    # The URL should only appear once as an href, not twice
    assert out.count("<a href") == 1


def test_html_is_escaped_and_not_rendered():
    out = str(format_post_body("<script>alert(1)</script>"))
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_javascript_protocol_is_not_linked():
    # Only http/https/mailto are recognised as link protocols
    out = str(format_post_body("[click](javascript:alert(1))"))
    assert "javascript:" not in out.lower() or 'href="javascript:' not in out
    assert "<a href=\"javascript:" not in out


def test_newlines_are_preserved_as_text():
    # Rendering relies on CSS white-space: pre-wrap, so \n is kept literal
    # rather than replaced with <br>. Confirm we don't mangle it.
    out = str(format_post_body("line 1\nline 2"))
    assert "\n" in out


def test_empty_string_is_empty():
    assert str(format_post_body("")) == ""
    assert str(format_post_body(None)) == ""
