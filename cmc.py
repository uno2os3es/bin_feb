#!/usr/bin/env python3
from collections.abc import Callable
from dataclasses import dataclass
import enum
import itertools


@dataclass
class CommentMatch:
    from_pos: int
    to_pos: int


class CommentStyle(enum.Enum):
    C = enum.auto()
    XML = enum.auto()
    SHELL = enum.auto()
    ATOM = enum.auto()


def find_comments_impl(
    input_str: str,
    state_transition: Callable,
    do_action: Callable,
    start_state,
    end_state,
    initial_comment_state,
) -> list[CommentMatch]:
    matches = []
    current_parse_state = start_state
    current_comment_state = initial_comment_state
    for pos, ch in enumerate(input_str):
        next_parse_state, action = state_transition(current_parse_state, ch)
        current_comment_state, matches = do_action(action, current_comment_state, pos, matches)
        current_parse_state = next_parse_state
    next_parse_state, action = state_transition(current_parse_state, None)
    current_comment_state, matches = do_action(action, current_comment_state, len(input_str), matches)
    return matches


def find_comments(input_str: str, style: CommentStyle) -> list[CommentMatch]:
    if style == CommentStyle.C:
        from . import c

        return c.find_comments(input_str)
    elif style == CommentStyle.ATOM:
        from . import atom

        return atom.find_comments(input_str)
    elif style == CommentStyle.SHELL:
        from . import shell

        return shell.find_comments(input_str)
    elif style == CommentStyle.XML:
        from . import xml

        return xml.find_comments(input_str)
    else:
        raise ValueError(f"Unknown comment style: {style}")


def check_sorted_matches(input_str: str, matches: list[CommentMatch]) -> None:
    length = len(input_str)
    for m in matches:
        if m.from_pos >= length or m.to_pos > length:
            raise ValueError("match out of range")
    for m, n in itertools.pairwise(matches):
        if m.to_pos > n.from_pos:
            raise ValueError("matches overlapping")


def remove_matches(input_str: str, matches: list[CommentMatch]) -> str:
    chars = list(input_str)
    matches_sorted = sorted(matches, key=lambda m: m.from_pos, reverse=True)
    for m in matches_sorted:
        del chars[m.from_pos : m.to_pos]
    return "".join(chars)


def strip_comments(data: str, style: CommentStyle, remove_blanks: bool = False) -> str:
    comment_matches = find_comments(data, style)
    stripped = remove_matches(data, comment_matches)
    if remove_blanks:
        from . import blanklines

        blank_matches = blanklines.find_blanklines(stripped)
        stripped = remove_matches(stripped, blank_matches)
    return stripped


class _CParseState(enum.Enum):
    START = 0
    NORMAL = 1
    FIRST_SLASH = 2
    SINGLE_LINE_COMMENT = 3
    MULTI_LINE_COMMENT = 4
    MULTI_LINE_COMMENT_FINAL_STAR = 5
    MULTI_LINE_COMMENT_FINAL_SLASH = 6
    STRING_DOUBLE_QUOTES = 7
    STRING_DOUBLE_QUOTES_ESCAPED = 8
    STRING_SINGLE_QUOTES = 9
    STRING_SINGLE_QUOTES_ESCAPED = 10
    END = 11


class _CAction(enum.Enum):
    NOTHING = 0
    COMMENT_MIGHT_START = 1
    COMMENT_CONFIRMED = 2
    COMMENT_DISMISSED = 3
    COMMENT_ENDS = 4
    COMMENT_ENDS_AND_COMMENT_MIGHT_START = 5


def _c_state_transition(state: _CParseState, ch: str | None) -> tuple[_CParseState, _CAction]:
    if ch is None:
        if state in (
            _CParseState.FIRST_SLASH,
            _CParseState.MULTI_LINE_COMMENT,
            _CParseState.MULTI_LINE_COMMENT_FINAL_STAR,
        ):
            return _CParseState.END, _CAction.COMMENT_DISMISSED
        elif state in (_CParseState.SINGLE_LINE_COMMENT, _CParseState.MULTI_LINE_COMMENT_FINAL_SLASH):
            return _CParseState.END, _CAction.COMMENT_ENDS
        else:
            return _CParseState.END, _CAction.NOTHING
    if state in (_CParseState.START, _CParseState.NORMAL):
        if ch == "/":
            return _CParseState.FIRST_SLASH, _CAction.COMMENT_MIGHT_START
        elif ch == '"':
            return _CParseState.STRING_DOUBLE_QUOTES, _CAction.NOTHING
        elif ch == "'":
            return _CParseState.STRING_SINGLE_QUOTES, _CAction.NOTHING
        else:
            return _CParseState.NORMAL, _CAction.NOTHING
    elif state == _CParseState.FIRST_SLASH:
        if ch == "/":
            return _CParseState.SINGLE_LINE_COMMENT, _CAction.COMMENT_CONFIRMED
        elif ch == "*":
            return _CParseState.MULTI_LINE_COMMENT, _CAction.COMMENT_CONFIRMED
        elif ch == '"':
            return _CParseState.STRING_DOUBLE_QUOTES, _CAction.COMMENT_DISMISSED
        elif ch == "'":
            return _CParseState.STRING_SINGLE_QUOTES, _CAction.COMMENT_DISMISSED
        else:
            return _CParseState.NORMAL, _CAction.COMMENT_DISMISSED
    elif state == _CParseState.SINGLE_LINE_COMMENT:
        if ch == "\n":
            return _CParseState.NORMAL, _CAction.COMMENT_ENDS
        else:
            return _CParseState.SINGLE_LINE_COMMENT, _CAction.NOTHING
    elif state == _CParseState.MULTI_LINE_COMMENT:
        if ch == "*":
            return _CParseState.MULTI_LINE_COMMENT_FINAL_STAR, _CAction.NOTHING
        else:
            return _CParseState.MULTI_LINE_COMMENT, _CAction.NOTHING
    elif state == _CParseState.MULTI_LINE_COMMENT_FINAL_STAR:
        if ch == "/":
            return _CParseState.MULTI_LINE_COMMENT_FINAL_SLASH, _CAction.NOTHING
        elif ch == "*":
            return _CParseState.MULTI_LINE_COMMENT_FINAL_STAR, _CAction.NOTHING
        else:
            return _CParseState.MULTI_LINE_COMMENT, _CAction.NOTHING
    elif state == _CParseState.MULTI_LINE_COMMENT_FINAL_SLASH:
        if ch == "/":
            return _CParseState.FIRST_SLASH, _CAction.COMMENT_ENDS_AND_COMMENT_MIGHT_START
        else:
            return _CParseState.NORMAL, _CAction.COMMENT_ENDS
    elif state == _CParseState.STRING_DOUBLE_QUOTES:
        if ch == '"':
            return _CParseState.NORMAL, _CAction.NOTHING
        elif ch == "\\":
            return _CParseState.STRING_DOUBLE_QUOTES_ESCAPED, _CAction.NOTHING
        else:
            return _CParseState.STRING_DOUBLE_QUOTES, _CAction.NOTHING
    elif state == _CParseState.STRING_DOUBLE_QUOTES_ESCAPED:
        return _CParseState.STRING_DOUBLE_QUOTES, _CAction.NOTHING
    elif state == _CParseState.STRING_SINGLE_QUOTES:
        if ch == "'":
            return _CParseState.NORMAL, _CAction.NOTHING
        elif ch == "\\":
            return _CParseState.STRING_SINGLE_QUOTES_ESCAPED, _CAction.NOTHING
        else:
            return _CParseState.STRING_SINGLE_QUOTES, _CAction.NOTHING
    elif state == _CParseState.STRING_SINGLE_QUOTES_ESCAPED:
        return _CParseState.STRING_SINGLE_QUOTES, _CAction.NOTHING
    else:
        return _CParseState.END, _CAction.NOTHING


def _c_do_action(
    action: _CAction, comment_state: tuple[str, int | None], pos: int, matches: list[CommentMatch]
) -> tuple[tuple[str, int | None], list[CommentMatch]]:
    kind, start = comment_state
    if action == _CAction.NOTHING:
        pass
    elif action == _CAction.COMMENT_MIGHT_START:
        kind, start = "maybe", pos
    elif action == _CAction.COMMENT_CONFIRMED:
        if kind != "maybe":
            raise ValueError("c style parser error")
        kind, start = "in", start
    elif action == _CAction.COMMENT_DISMISSED:
        kind, start = "not", None
    elif action == _CAction.COMMENT_ENDS:
        if kind != "in":
            raise ValueError("c style parser error")
        matches.append(CommentMatch(start, pos))
        kind, start = "not", None
    elif action == _CAction.COMMENT_ENDS_AND_COMMENT_MIGHT_START:
        if kind != "in":
            raise ValueError("c style parser error")
        matches.append(CommentMatch(start, pos))
        kind, start = "maybe", pos
    return (kind, start), matches


def find_c_comments(input_str: str) -> list[CommentMatch]:
    return find_comments_impl(
        input_str, _c_state_transition, _c_do_action, _CParseState.START, _CParseState.END, ("not", None)
    )


def strip_c_comments(code: str) -> str:
    return strip_comments(code, CommentStyle.C, False)


class _ShellParseState(enum.Enum):
    START = 0
    NORMAL = 1
    SHEBANG_OR_COMMENT = 2
    SHEBANG = 3
    COMMENT = 4
    STRING_DOUBLE_QUOTES = 5
    STRING_DOUBLE_QUOTES_ESCAPED = 6
    STRING_SINGLE_QUOTES = 7
    STRING_SINGLE_QUOTES_ESCAPED = 8
    END = 9


class _ShellAction(enum.Enum):
    NOTHING = 0
    COMMENT_STARTS = 1
    COMMENT_ENDS = 2
    SHEBANG_OR_COMMENT_START = 3
    SHEBANG_FOUND = 4


def _shell_state_transition(state: _ShellParseState, ch: str | None) -> tuple[_ShellParseState, _ShellAction]:
    if ch is None:
        if state == _ShellParseState.COMMENT:
            return _ShellParseState.END, _ShellAction.COMMENT_ENDS
        elif state == _ShellParseState.SHEBANG_OR_COMMENT:
            return _ShellParseState.END, _ShellAction.SHEBANG_FOUND
        else:
            return _ShellParseState.END, _ShellAction.NOTHING
    if state == _ShellParseState.START:
        if ch == "#":
            return _ShellParseState.SHEBANG_OR_COMMENT, _ShellAction.SHEBANG_OR_COMMENT_START
        elif ch == '"':
            return _ShellParseState.STRING_DOUBLE_QUOTES, _ShellAction.NOTHING
        elif ch == "'":
            return _ShellParseState.STRING_SINGLE_QUOTES, _ShellAction.NOTHING
        else:
            return _ShellParseState.NORMAL, _ShellAction.NOTHING
    elif state == _ShellParseState.NORMAL:
        if ch == "#":
            return _ShellParseState.COMMENT, _ShellAction.COMMENT_STARTS
        elif ch == '"':
            return _ShellParseState.STRING_DOUBLE_QUOTES, _ShellAction.NOTHING
        elif ch == "'":
            return _ShellParseState.STRING_SINGLE_QUOTES, _ShellAction.NOTHING
        else:
            return _ShellParseState.NORMAL, _ShellAction.NOTHING
    elif state == _ShellParseState.SHEBANG_OR_COMMENT:
        if ch == "!":
            return _ShellParseState.SHEBANG, _ShellAction.SHEBANG_FOUND
        else:
            return _ShellParseState.COMMENT, _ShellAction.NOTHING
    elif state == _ShellParseState.SHEBANG:
        if ch == "\n":
            return _ShellParseState.NORMAL, _ShellAction.NOTHING
        elif ch == "#":
            return _ShellParseState.COMMENT, _ShellAction.COMMENT_STARTS
        elif ch == '"':
            return _ShellParseState.STRING_DOUBLE_QUOTES, _ShellAction.NOTHING
        elif ch == "'":
            return _ShellParseState.STRING_SINGLE_QUOTES, _ShellAction.NOTHING
        else:
            return _ShellParseState.SHEBANG, _ShellAction.NOTHING
    elif state == _ShellParseState.COMMENT:
        if ch == "\n":
            return _ShellParseState.NORMAL, _ShellAction.COMMENT_ENDS
        else:
            return _ShellParseState.COMMENT, _ShellAction.NOTHING
    elif state == _ShellParseState.STRING_DOUBLE_QUOTES:
        if ch == '"':
            return _ShellParseState.NORMAL, _ShellAction.NOTHING
        elif ch == "\\":
            return _ShellParseState.STRING_DOUBLE_QUOTES_ESCAPED, _ShellAction.NOTHING
        else:
            return _ShellParseState.STRING_DOUBLE_QUOTES, _ShellAction.NOTHING
    elif state == _ShellParseState.STRING_DOUBLE_QUOTES_ESCAPED:
        return _ShellParseState.STRING_DOUBLE_QUOTES, _ShellAction.NOTHING
    elif state == _ShellParseState.STRING_SINGLE_QUOTES:
        if ch == "'":
            return _ShellParseState.NORMAL, _ShellAction.NOTHING
        elif ch == "\\":
            return _ShellParseState.STRING_SINGLE_QUOTES_ESCAPED, _ShellAction.NOTHING
        else:
            return _ShellParseState.STRING_SINGLE_QUOTES, _ShellAction.NOTHING
    elif state == _ShellParseState.STRING_SINGLE_QUOTES_ESCAPED:
        return _ShellParseState.STRING_SINGLE_QUOTES, _ShellAction.NOTHING
    else:
        return _ShellParseState.END, _ShellAction.NOTHING


def _shell_do_action(
    action: _ShellAction, comment_state: tuple[str, int | None], pos: int, matches: list[CommentMatch]
) -> tuple[tuple[str, int | None], list[CommentMatch]]:
    kind, start = comment_state
    if action == _ShellAction.NOTHING:
        pass
    elif action == _ShellAction.COMMENT_STARTS:
        kind, start = "in", pos
    elif action == _ShellAction.SHEBANG_OR_COMMENT_START:
        kind, start = "maybe", pos
    elif action == _ShellAction.SHEBANG_FOUND:
        kind, start = "not", None
    elif action == _ShellAction.COMMENT_ENDS:
        if kind == "not":
            raise ValueError("shell style parse error")
        if kind in {"maybe", "in"}:
            matches.append(CommentMatch(start, pos))
        kind, start = "not", None
    return (kind, start), matches


def find_shell_comments(input_str: str) -> list[CommentMatch]:
    return find_comments_impl(
        input_str,
        _shell_state_transition,
        _shell_do_action,
        _ShellParseState.START,
        _ShellParseState.END,
        ("not", None),
    )


def strip_shell_comments(code: str) -> str:
    return strip_comments(code, CommentStyle.SHELL, False)


find_atom_comments = find_shell_comments
strip_atom_comments = strip_shell_comments


class _XMLParseState(enum.Enum):
    START = 0
    NORMAL = 1
    COMMENT_START_BRACKET = 2
    COMMENT_START_EXCL = 3
    COMMENT_START_MINUS1 = 4
    COMMENT_START_MINUS2 = 5
    COMMENT = 6
    COMMENT_END_MINUS1 = 7
    COMMENT_END_MINUS2 = 8
    COMMENT_END_BRACKET = 9
    STRING_DOUBLE_QUOTES = 10
    STRING_DOUBLE_QUOTES_ESCAPED = 11
    STRING_SINGLE_QUOTES = 12
    STRING_SINGLE_QUOTES_ESCAPED = 13
    END = 14


class _XMLAction(enum.Enum):
    NOTHING = 0
    COMMENT_OR_TAG_STARTS = 1
    COMMENT_CONFIRMED = 2
    COMMENT_DISMISSED = 3
    COMMENT_ENDS = 4
    COMMENT_ENDS_AND_COMMENT_OR_TAG_STARTS = 5


def _xml_state_transition(state: _XMLParseState, ch: str | None) -> tuple[_XMLParseState, _XMLAction]:
    if ch is None:
        if state in (
            _XMLParseState.COMMENT_START_BRACKET,
            _XMLParseState.COMMENT_START_EXCL,
            _XMLParseState.COMMENT_START_MINUS1,
            _XMLParseState.COMMENT_START_MINUS2,
            _XMLParseState.COMMENT,
            _XMLParseState.COMMENT_END_MINUS1,
            _XMLParseState.COMMENT_END_MINUS2,
        ):
            return _XMLParseState.END, _XMLAction.COMMENT_DISMISSED
        elif state == _XMLParseState.COMMENT_END_BRACKET:
            return _XMLParseState.END, _XMLAction.COMMENT_ENDS
        else:
            return _XMLParseState.END, _XMLAction.NOTHING
    if state in (_XMLParseState.START, _XMLParseState.NORMAL):
        if ch == "<":
            return _XMLParseState.COMMENT_START_BRACKET, _XMLAction.COMMENT_OR_TAG_STARTS
        elif ch == '"':
            return _XMLParseState.STRING_DOUBLE_QUOTES, _XMLAction.NOTHING
        elif ch == "'":
            return _XMLParseState.STRING_SINGLE_QUOTES, _XMLAction.NOTHING
        else:
            return _XMLParseState.NORMAL, _XMLAction.NOTHING
    elif state == _XMLParseState.COMMENT_START_BRACKET:
        if ch == "!":
            return _XMLParseState.COMMENT_START_EXCL, _XMLAction.NOTHING
        else:
            return _XMLParseState.NORMAL, _XMLAction.COMMENT_DISMISSED
    elif state == _XMLParseState.COMMENT_START_EXCL:
        if ch == "-":
            return _XMLParseState.COMMENT_START_MINUS1, _XMLAction.NOTHING
        else:
            return _XMLParseState.NORMAL, _XMLAction.COMMENT_DISMISSED
    elif state == _XMLParseState.COMMENT_START_MINUS1:
        if ch == "-":
            return _XMLParseState.COMMENT_START_MINUS2, _XMLAction.COMMENT_CONFIRMED
        else:
            return _XMLParseState.NORMAL, _XMLAction.COMMENT_DISMISSED
    elif state in (_XMLParseState.COMMENT_START_MINUS2, _XMLParseState.COMMENT):
        if ch == "-":
            return _XMLParseState.COMMENT_END_MINUS1, _XMLAction.NOTHING
        else:
            return _XMLParseState.COMMENT, _XMLAction.NOTHING
    elif state == _XMLParseState.COMMENT_END_MINUS1:
        if ch == "-":
            return _XMLParseState.COMMENT_END_MINUS2, _XMLAction.NOTHING
        else:
            return _XMLParseState.COMMENT, _XMLAction.NOTHING
    elif state == _XMLParseState.COMMENT_END_MINUS2:
        if ch == ">":
            return _XMLParseState.COMMENT_END_BRACKET, _XMLAction.NOTHING
        elif ch == "-":
            return _XMLParseState.COMMENT_END_MINUS2, _XMLAction.NOTHING
        else:
            return _XMLParseState.COMMENT, _XMLAction.NOTHING
    elif state == _XMLParseState.COMMENT_END_BRACKET:
        if ch == "<":
            return _XMLParseState.COMMENT_START_BRACKET, _XMLAction.COMMENT_ENDS_AND_COMMENT_OR_TAG_STARTS
        elif ch == '"':
            return _XMLParseState.STRING_DOUBLE_QUOTES, _XMLAction.COMMENT_ENDS
        elif ch == "'":
            return _XMLParseState.STRING_SINGLE_QUOTES, _XMLAction.COMMENT_ENDS
        else:
            return _XMLParseState.NORMAL, _XMLAction.COMMENT_ENDS
    elif state == _XMLParseState.STRING_DOUBLE_QUOTES:
        if ch == '"':
            return _XMLParseState.NORMAL, _XMLAction.NOTHING
        elif ch == "\\":
            return _XMLParseState.STRING_DOUBLE_QUOTES_ESCAPED, _XMLAction.NOTHING
        else:
            return _XMLParseState.STRING_DOUBLE_QUOTES, _XMLAction.NOTHING
    elif state == _XMLParseState.STRING_DOUBLE_QUOTES_ESCAPED:
        return _XMLParseState.STRING_DOUBLE_QUOTES, _XMLAction.NOTHING
    elif state == _XMLParseState.STRING_SINGLE_QUOTES:
        if ch == "'":
            return _XMLParseState.NORMAL, _XMLAction.NOTHING
        elif ch == "\\":
            return _XMLParseState.STRING_SINGLE_QUOTES_ESCAPED, _XMLAction.NOTHING
        else:
            return _XMLParseState.STRING_SINGLE_QUOTES, _XMLAction.NOTHING
    elif state == _XMLParseState.STRING_SINGLE_QUOTES_ESCAPED:
        return _XMLParseState.STRING_SINGLE_QUOTES, _XMLAction.NOTHING
    else:
        return _XMLParseState.END, _XMLAction.NOTHING


def _xml_do_action(
    action: _XMLAction, comment_state: tuple[str, int | None], pos: int, matches: list[CommentMatch]
) -> tuple[tuple[str, int | None], list[CommentMatch]]:
    kind, start = comment_state
    if action == _XMLAction.NOTHING:
        pass
    elif action == _XMLAction.COMMENT_OR_TAG_STARTS:
        kind, start = "or_tag", pos
    elif action == _XMLAction.COMMENT_CONFIRMED:
        if kind != "or_tag":
            raise ValueError("xml style parser error")
        kind, start = "in", start
    elif action == _XMLAction.COMMENT_DISMISSED:
        kind, start = "not", None
    elif action == _XMLAction.COMMENT_ENDS:
        if kind != "in":
            raise ValueError("xml style parser error")
        matches.append(CommentMatch(start, pos))
        kind, start = "not", None
    elif action == _XMLAction.COMMENT_ENDS_AND_COMMENT_OR_TAG_STARTS:
        if kind != "in":
            raise ValueError("xml style parser error")
        matches.append(CommentMatch(start, pos))
        kind, start = "or_tag", pos
    return (kind, start), matches


def find_xml_comments(input_str: str) -> list[CommentMatch]:
    return find_comments_impl(
        input_str, _xml_state_transition, _xml_do_action, _XMLParseState.START, _XMLParseState.END, ("not", None)
    )


def strip_xml_comments(code: str) -> str:
    return strip_comments(code, CommentStyle.XML, False)


class _BlankParseState(enum.Enum):
    START = 0
    NORMAL = 1
    SINGLE_BLANKLINE = 2
    MULTI_BLANKLINE = 3
    STRING_DOUBLE_QUOTES = 4
    STRING_DOUBLE_QUOTES_ESCAPED = 5
    STRING_SINGLE_QUOTES = 6
    STRING_SINGLE_QUOTES_ESCAPED = 7
    END = 8


class _BlankAction(enum.Enum):
    NOTHING = 0
    MULTI_BLANKLINE_START = 1
    MULTI_BLANKLINE_END = 2


def _blank_state_transition(state: _BlankParseState, ch: str | None) -> tuple[_BlankParseState, _BlankAction]:
    if ch is None:
        if state == _BlankParseState.MULTI_BLANKLINE:
            return _BlankParseState.END, _BlankAction.MULTI_BLANKLINE_END
        else:
            return _BlankParseState.END, _BlankAction.NOTHING
    if state == _BlankParseState.START:
        if ch == "\n":
            return _BlankParseState.MULTI_BLANKLINE, _BlankAction.MULTI_BLANKLINE_START
        elif ch == '"':
            return _BlankParseState.STRING_DOUBLE_QUOTES, _BlankAction.NOTHING
        elif ch == "'":
            return _BlankParseState.STRING_SINGLE_QUOTES, _BlankAction.NOTHING
        else:
            return _BlankParseState.NORMAL, _BlankAction.NOTHING
    elif state == _BlankParseState.NORMAL:
        if ch == "\n":
            return _BlankParseState.SINGLE_BLANKLINE, _BlankAction.NOTHING
        elif ch == '"':
            return _BlankParseState.STRING_DOUBLE_QUOTES, _BlankAction.NOTHING
        elif ch == "'":
            return _BlankParseState.STRING_SINGLE_QUOTES, _BlankAction.NOTHING
        else:
            return _BlankParseState.NORMAL, _BlankAction.NOTHING
    elif state == _BlankParseState.SINGLE_BLANKLINE:
        if ch == "\n":
            return _BlankParseState.MULTI_BLANKLINE, _BlankAction.MULTI_BLANKLINE_START
        elif ch == '"':
            return _BlankParseState.STRING_DOUBLE_QUOTES, _BlankAction.NOTHING
        elif ch == "'":
            return _BlankParseState.STRING_SINGLE_QUOTES, _BlankAction.NOTHING
        else:
            return _BlankParseState.NORMAL, _BlankAction.NOTHING
    elif state == _BlankParseState.MULTI_BLANKLINE:
        if ch == "\n":
            return _BlankParseState.MULTI_BLANKLINE, _BlankAction.NOTHING
        elif ch == '"':
            return _BlankParseState.STRING_DOUBLE_QUOTES, _BlankAction.MULTI_BLANKLINE_END
        elif ch == "'":
            return _BlankParseState.STRING_SINGLE_QUOTES, _BlankAction.MULTI_BLANKLINE_END
        else:
            return _BlankParseState.NORMAL, _BlankAction.MULTI_BLANKLINE_END
    elif state == _BlankParseState.STRING_DOUBLE_QUOTES:
        if ch == '"':
            return _BlankParseState.NORMAL, _BlankAction.NOTHING
        elif ch == "\\":
            return _BlankParseState.STRING_DOUBLE_QUOTES_ESCAPED, _BlankAction.NOTHING
        else:
            return _BlankParseState.STRING_DOUBLE_QUOTES, _BlankAction.NOTHING
    elif state == _BlankParseState.STRING_DOUBLE_QUOTES_ESCAPED:
        return _BlankParseState.STRING_DOUBLE_QUOTES, _BlankAction.NOTHING
    elif state == _BlankParseState.STRING_SINGLE_QUOTES:
        if ch == "'":
            return _BlankParseState.NORMAL, _BlankAction.NOTHING
        elif ch == "\\":
            return _BlankParseState.STRING_SINGLE_QUOTES_ESCAPED, _BlankAction.NOTHING
        else:
            return _BlankParseState.STRING_SINGLE_QUOTES, _BlankAction.NOTHING
    elif state == _BlankParseState.STRING_SINGLE_QUOTES_ESCAPED:
        return _BlankParseState.STRING_SINGLE_QUOTES, _BlankAction.NOTHING
    else:
        return _BlankParseState.END, _BlankAction.NOTHING


def _blank_do_action(
    action: _BlankAction, blank_state: tuple[str, int | None], pos: int, matches: list[CommentMatch]
) -> tuple[tuple[str, int | None], list[CommentMatch]]:
    kind, start = blank_state
    if action == _BlankAction.NOTHING:
        pass
    elif action == _BlankAction.MULTI_BLANKLINE_START:
        kind, start = "in", pos
    elif action == _BlankAction.MULTI_BLANKLINE_END:
        if kind != "in":
            raise ValueError("blankline parser error")
        matches.append(CommentMatch(start, pos))
        kind, start = "not", None
    return (kind, start), matches


def find_blanklines(input_str: str) -> list[CommentMatch]:
    return find_comments_impl(
        input_str,
        _blank_state_transition,
        _blank_do_action,
        _BlankParseState.START,
        _BlankParseState.END,
        ("not", None),
    )


class cpp:
    @staticmethod
    def strip(code: str) -> str:
        return strip_c_comments(code)


class rust:
    @staticmethod
    def strip(code: str) -> str:
        return strip_c_comments(code)


class python:
    @staticmethod
    def strip(code: str) -> str:
        return strip_shell_comments(code)


class html:
    @staticmethod
    def strip(code: str) -> str:
        return strip_xml_comments(code)


if __name__ == "__main__":
    test_cases = [
        ("C normal", "int main() { /* comment */ }", strip_c_comments, "int main() {  }"),
        ("C line", "main() // comment\n", strip_c_comments, "main() \n"),
        ("C multiline", "/* multi \nline\ncomment */", strip_c_comments, ""),
        ("C string", r'printf("//not comment")', strip_c_comments, r'printf("//not comment")'),
        ("Shell normal", "yes # line comment\n yes no\n", strip_shell_comments, "yes \n yes no\n"),
        ("Shell shebang", "#!/bin/bash\necho hi\n", strip_shell_comments, "#!/bin/bash\necho hi\n"),
        ("XML normal", "<t /><!-- comment -->", strip_xml_comments, "<t />"),
        ("XML in tag", "<tag <!-- comment -->></tag>", strip_xml_comments, "<tag ></tag>"),
        (
            "Blank lines",
            "\n\nhello\n\n\nworld\n\n",
            find_blanklines,
            [CommentMatch(0, 2), CommentMatch(8, 11), CommentMatch(15, 17)],
        ),
    ]
    for name, inp, func, expected in test_cases:
        if isinstance(expected, str):
            out = func(inp)
            assert out == expected, f"{name}: {out!r} != {expected!r}"
        else:
            out = func(inp)
            assert out == expected, f"{name}: {out} != {expected}"
    print("All tests passed.")
