"""
Report export service — converts reports to Markdown, HTML, CSV, PDF, and JSON formats.

Provides two interfaces:
- ReportExporter class: works with section lists (used by internal report builder)
- Standalone functions (export_html, export_pdf, export_json): work with Report model objects
  (used by the download endpoint)

HTML and PDF share a single branded template; PDF is rendered via xhtml2pdf.
"""

import csv
import io
import json
import re
from io import BytesIO

import markdown
from xhtml2pdf import pisa

from ..utils.logger import get_logger

logger = get_logger('mirofish.services.report_exporter')

# Intercom-branded HTML template shared by HTML and PDF exports.
# PDF renderer (xhtml2pdf) requires inline styles — external CSS/Tailwind won't work.
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{
    size: A4;
    margin: 2cm;
    @frame footer {{
      -pdf-frame-content: page-footer;
      bottom: 0;
      height: 1cm;
      margin-left: 2cm;
      margin-right: 2cm;
    }}
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    line-height: 1.6;
    font-size: 14px;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }}
  h1 {{
    font-size: 1.75rem;
    font-weight: 700;
    color: #050505;
    border-bottom: 3px solid #2068FF;
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
  }}
  h2 {{
    font-size: 1.35rem;
    font-weight: 600;
    color: #050505;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
  }}
  h3 {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #333;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
  }}
  p {{ margin-bottom: 0.75rem; }}
  ul, ol {{ margin-bottom: 0.75rem; padding-left: 1.5rem; }}
  li {{ margin-bottom: 0.25rem; }}
  blockquote {{
    border-left: 3px solid #2068FF;
    padding-left: 1rem;
    margin: 1rem 0;
    color: #555;
    font-style: italic;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 0.875rem;
  }}
  th {{
    text-align: left;
    padding: 0.5rem;
    border-bottom: 2px solid #2068FF;
    font-weight: 600;
  }}
  td {{
    padding: 0.5rem;
    border-bottom: 1px solid #e0e0e0;
  }}
  code {{
    background: #f4f4f8;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.85em;
  }}
  pre {{
    background: #1a1a2e;
    color: #e0e0e0;
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1rem 0;
  }}
  pre code {{ background: none; padding: 0; }}
  hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 1.5rem 0; }}
  .report-header {{
    background: #f8faff;
    border: 1px solid #d4e3ff;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }}
  .report-header .meta {{
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.5rem;
  }}
  .report-header .meta span {{
    margin-right: 1.5rem;
  }}
  strong {{ font-weight: 600; color: #050505; }}
  #page-footer {{
    font-size: 0.7rem;
    color: #999;
    text-align: center;
  }}
  @media print {{
    body {{ padding: 0; max-width: none; }}
    h2 {{ page-break-before: always; }}
    h2:first-of-type {{ page-break-before: avoid; }}
    pre, table, blockquote {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="report-header">
  <div style="font-size:0.75rem;font-weight:600;color:#2068FF;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.25rem;">
    MiroFish GTM Report
  </div>
  <div class="meta">
    <span>Report: {report_id}</span>
    <span>Generated: {completed_at}</span>
  </div>
</div>
{body}
<div id="page-footer">
  MiroFish GTM &mdash; Predictive Report &mdash; {report_id}
</div>
</body>
</html>"""

# Markdown extensions for richer HTML output
_MD_EXTENSIONS = ['tables', 'fenced_code', 'toc', 'smarty']


def export_html(report) -> str:
    """Convert a Report to a standalone branded HTML document."""
    body_html = markdown.markdown(
        report.markdown_content or '',
        extensions=_MD_EXTENSIONS,
    )
    return _HTML_TEMPLATE.format(
        title=report.outline.title if report.outline else 'GTM Report',
        report_id=report.report_id,
        completed_at=report.completed_at or report.created_at or '',
        body=body_html,
    )


def export_pdf(report) -> bytes:
    """Convert a Report to PDF bytes via HTML intermediate."""
    html = export_html(report)
    buf = BytesIO()
    status = pisa.CreatePDF(html, dest=buf, encoding='utf-8')
    if status.err:
        logger.error(f"PDF generation errors for {report.report_id}: {status.err}")
    buf.seek(0)
    return buf.read()


def export_json(report) -> str:
    """Return structured JSON of the full report data."""
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


class ReportExporter:
    """Exports report content to multiple formats from section lists."""

    @staticmethod
    def to_markdown(sections):
        """Combine report sections into clean Markdown."""
        parts = []
        for s in sections:
            content = s.get('content', '') if isinstance(s, dict) else s
            parts.append(content.strip())
        return '\n\n---\n\n'.join(parts)

    @staticmethod
    def to_html(sections, title='Simulation Report'):
        """Render report as self-contained HTML with Intercom branding."""
        markdown_text = ReportExporter.to_markdown(sections)
        html_body = markdown.markdown(markdown_text, extensions=_MD_EXTENSIONS)
        return _HTML_TEMPLATE.format(
            title=title,
            report_id='',
            completed_at='',
            body=html_body,
        )

    @staticmethod
    def to_csv(sections):
        """Extract tabular data from markdown tables in the report."""
        markdown_text = ReportExporter.to_markdown(sections)
        tables = ReportExporter._extract_tables(markdown_text)

        if not tables:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Section', 'Content Summary'])
            for s in sections:
                content = s.get('content', '') if isinstance(s, dict) else s
                title_match = re.search(r'^##\s+(.+)', content, re.MULTILINE)
                title = title_match.group(1) if title_match else 'Untitled'
                paragraphs = [
                    l.strip() for l in content.split('\n')
                    if l.strip() and not l.strip().startswith('#')
                ]
                summary = paragraphs[0][:200] if paragraphs else ''
                writer.writerow([title, summary])
            return output.getvalue()

        output = io.StringIO()
        writer = csv.writer(output)
        for i, table in enumerate(tables):
            if i > 0:
                writer.writerow([])
            for row in table:
                writer.writerow(row)
        return output.getvalue()

    @staticmethod
    def _extract_tables(markdown_text):
        """Extract markdown tables as lists of rows."""
        tables = []
        current_table = []

        for line in markdown_text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                if re.match(r'^\|[\s\-:]+\|$', stripped.replace('|', '|').strip()):
                    continue
                cells = [c.strip() for c in stripped.split('|')[1:-1]]
                current_table.append(cells)
            else:
                if current_table:
                    tables.append(current_table)
                    current_table = []

        if current_table:
            tables.append(current_table)

        return tables
