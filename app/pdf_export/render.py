"""Jinja2-to-LaTeX-to-PDF rendering (data-sharing-pdf-export's design.md):
Jinja2 reuses the same templating engine as the HTML dashboard, with
LaTeX-safe custom delimiters so `{`/`}`/`%` keep their normal LaTeX meaning;
Tectonic is invoked as a subprocess over the rendered `.tex` source, since it
has no stable first-party Python binding.
"""

import re
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# Single-pass alternation so each character is escaped exactly once from the
# original string -- chaining sequential .replace() calls would re-escape
# the backslashes a replacement like "\&" introduces.
_LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_ESCAPE_RE = re.compile("|".join(re.escape(c) for c in _LATEX_SPECIAL_CHARS))


def latex_escape(value: object) -> str:
    return _LATEX_ESCAPE_RE.sub(lambda m: _LATEX_SPECIAL_CHARS[m.group()], str(value))


def get_environment() -> Environment:
    # `\BLOCK{`/`\VAR{`/`}` (not doubled-paren delimiters): Jinja2's lexer
    # balances parentheses inside an expression to find where it ends (e.g.
    # a filter call like `format(x)`), and a literal "(" from a pgfplots
    # coordinate written right before a doubled-paren variable -- `(((x)),
    # ((y)))` -- throws off that balance and fails to parse. Word-prefixed
    # brace delimiters don't share a character with LaTeX's own parentheses.
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters["latex_escape"] = latex_escape
    return env


def render_tex(context: dict) -> str:
    template = get_environment().get_template("report.tex.j2")
    return template.render(**context)


def compile_pdf(tex_source: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tex_path = tmp_path / "report.tex"
        tex_path.write_text(tex_source, encoding="utf-8")
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        subprocess.run(
            ["tectonic", "--outdir", str(out_dir), str(tex_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return (out_dir / "report.pdf").read_bytes()


def generate_report_pdf(context: dict) -> bytes:
    return compile_pdf(render_tex(context))
