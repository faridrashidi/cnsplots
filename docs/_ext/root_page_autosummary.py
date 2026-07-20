from __future__ import annotations

import posixpath
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from docutils import nodes
from docutils.statemachine import StringList
from sphinx import addnodes
from sphinx.ext.autosummary import Autosummary, autosummary_table
from sphinx.ext.autosummary import generate as autosummary_generate
from sphinx.util.docutils import switch_source_input
from sphinx.util.parsing import nested_parse_to_nodes


def _rewrite_apirootsummary_lines(lines: list[str]) -> list[str]:
    return [
        line.replace(".. apirootsummary::", ".. autosummary::")
        if ".. apirootsummary::" in line
        else line
        for line in lines
    ]


class ApiRootSummary(Autosummary):
    """Autosummary variant that links to stub pages without object fragments."""

    def get_table(
        self, items: list[tuple[str, str | None, str, str]]
    ) -> list[nodes.Node]:
        if "toctree" not in self.options:
            return super().get_table(items)

        builder = getattr(self.env.app, "builder", None)
        if builder is None:
            return super().get_table(items)

        table_spec = addnodes.tabular_col_spec()
        table_spec["spec"] = r"\X{1}{2}\X{1}{2}"

        table = autosummary_table("")
        real_table = nodes.table(
            "", classes=["autosummary", "longtable", *self.options.get("class", ())]
        )
        table.append(real_table)
        group = nodes.tgroup("", cols=2)
        real_table.append(group)
        group.append(nodes.colspec("", colwidth=10))
        group.append(nodes.colspec("", colwidth=90))
        body = nodes.tbody("")
        group.append(body)

        source, line = self.state_machine.get_source_and_line()
        current_document = getattr(self.env, "current_document", None)
        current_doc = (
            current_document.docname
            if current_document is not None
            else self.env.docname
        )
        dirname = posixpath.dirname(current_doc)
        tree_prefix = self.options["toctree"].strip()
        filename_map = self.config.autosummary_filename_map

        for name, sig, summary, real_name in items:
            mapped_name = filename_map.get(real_name, real_name)
            docname = posixpath.join(tree_prefix, mapped_name)
            docname = posixpath.normpath(posixpath.join(dirname, docname))
            refuri = builder.get_relative_uri(current_doc, docname)

            row = nodes.row("")

            first_col = nodes.paragraph("")
            link = nodes.reference(
                "", "", internal=True, refuri=refuri, title=real_name
            )
            link += nodes.literal(
                name, name, classes=["xref", "py", "py-obj", "docutils", "literal"]
            )
            first_col += link
            if sig is not None:
                first_col += nodes.Text(f" {sig}")
            row.append(nodes.entry("", first_col))

            summary_lines = StringList([summary], f"{source}:{line}:<apirootsummary>")
            with switch_source_input(self.state, summary_lines):
                parsed = nested_parse_to_nodes(
                    self.state, summary_lines, allow_section_headings=False
                )
                if parsed and isinstance(parsed[0], nodes.paragraph):
                    second_col = parsed[0]
                else:
                    second_col = nodes.paragraph("")
            row.append(nodes.entry("", second_col))

            body.append(row)

        return [table_spec, table]


_ORIGINAL_FIND_AUTOSUMMARY_IN_LINES = autosummary_generate.find_autosummary_in_lines


def _find_autosummary_in_lines_with_apirootsummary(
    lines: list[str], module: str | None = None, filename: str | None = None
) -> list[Any]:
    return _ORIGINAL_FIND_AUTOSUMMARY_IN_LINES(
        _rewrite_apirootsummary_lines(lines), module=module, filename=filename
    )


def _strip_matching_api_fragments(
    app: Any, doctree: nodes.document, _docname: str
) -> None:
    if getattr(app.builder, "format", None) != "html":
        return

    for node in doctree.findall(nodes.reference):
        refuri = node.get("refuri")
        if not refuri:
            continue

        parts = urlsplit(refuri)
        if not parts.path.endswith(".html") or not parts.fragment:
            continue

        basename = posixpath.basename(parts.path)
        stem, _suffix = posixpath.splitext(basename)
        if not stem.startswith("cnsplots.") or parts.fragment != stem:
            continue

        node["refuri"] = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, parts.query, "")
        )


def setup(app: Any) -> dict[str, Any]:
    autosummary_generate.find_autosummary_in_lines = (
        _find_autosummary_in_lines_with_apirootsummary
    )
    app.add_directive("apirootsummary", ApiRootSummary)
    app.connect("doctree-resolved", _strip_matching_api_fragments)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
