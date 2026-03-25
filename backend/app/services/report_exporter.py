"""
Report export service — converts markdown reports to HTML, PDF, and JSON.

All formats derive from the same canonical markdown source stored on disk.
HTML and PDF share a single branded template; JSON returns structured report data.
"""

import json
import tempfile
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
