import os
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "BRIDGE · Enterprise CMS Migrator & Schema Transformation Engine")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(558, 32, page_str)
        self.drawString(54, 32, "Enterprise Content Intelligence Platform · Confidential & Proprietary")
        self.restoreState()


def build_pdf(filename="BRIDGE_BEGINNER_STUDY_GUIDE.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#B45309"),
        spaceAfter=14,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#92400E"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    )
    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )

    story = []

    # Title block
    story.append(Paragraph("BRIDGE — CMS MIGRATOR & SCHEMA ENGINE", title_style))
    story.append(Paragraph("Architecture, Schema Transformation & Operational Study Guide · Agent #5", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#F59E0B"), spaceAfter=12))

    # Meta banner table
    meta_data = [
        [
            Paragraph("<b>Agent ID:</b> BRIDGE (#5)", body_style),
            Paragraph("<b>AWS Account:</b> 984625844016 (us-east-1)", body_style),
        ],
        [
            Paragraph("<b>CloudFront UI:</b> https://d23utb1q5zn42x.cloudfront.net", body_style),
            Paragraph("<b>API Gateway:</b> https://hjwkic438k.execute-api.us-east-1.amazonaws.com", body_style),
        ],
        [
            Paragraph("<b>AI Engine:</b> Amazon Bedrock (Nova Pro Converse)", body_style),
            Paragraph("<b>Security Standard:</b> Zero-Bug Manifesto Compliant", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FCD34D")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Section 1
    story.append(Paragraph("1. Executive Summary & Purpose", h1_style))
    story.append(Paragraph(
        "Enterprise digital transformation initiatives frequently fail or stall during content migration. Organizations attempting to transition from legacy monolithic Content Management Systems (e.g., WordPress, Drupal 7/8, Adobe Experience Manager, Sitecore) to modern headless architectures (e.g., Contentful, Strapi, Sanity) face massive schema mismatches, loss of custom metadata, unformatted HTML tags, and broken asset relationships.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>BRIDGE</b> was engineered as Agent #5 in the 10-Agent Content Intelligence Platform to solve this challenge. It provides an automated, high-precision migration and schema transformation engine that analyzes source databases, HTML exports, or raw document drafts and produces a production-ready field mapping matrix, JSON ingestion payloads, and risk-rated exception logs.",
        body_style,
    ))

    # Section 2
    story.append(Paragraph("2. System Architecture & AWS Infrastructure", h1_style))
    story.append(Paragraph(
        "BRIDGE is deployed across a 100% serverless, cloud-native AWS footprint engineered for sub-second latency, zero maintenance overhead, and enterprise-grade resilience:",
        body_style,
    ))

    arch_rows = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>AWS Technology</b>", body_style), Paragraph("<b>Specification & Purpose</b>", body_style)],
        [
            Paragraph("Frontend UI", body_style),
            Paragraph("CloudFront + S3", body_style),
            Paragraph("React 18 SPA bundled via Vite. Hosted in S3 with Origin Access Control (OAC) and distributed via CloudFront edge locations globally.", body_style),
        ],
        [
            Paragraph("API Layer", body_style),
            Paragraph("HTTP API Gateway v2", body_style),
            Paragraph("Ultra-low latency HTTP API with native CORS headers and direct Lambda payload routing.", body_style),
        ],
        [
            Paragraph("Backend Compute", body_style),
            Paragraph("AWS Lambda (Python 3.11)", body_style),
            Paragraph("512 MB memory, 120s timeout. Pure native Python handler parsing multipart file uploads, JSON payloads, and Bedrock orchestrations.", body_style),
        ],
        [
            Paragraph("AI Reasoning", body_style),
            Paragraph("Amazon Bedrock", body_style),
            Paragraph("Amazon Nova Pro Converse (`us.amazon.nova-pro-v1:0`) executing schema synthesis and AST transform generation.", body_style),
        ],
        [
            Paragraph("Security & Storage", body_style),
            Paragraph("AWS IAM + S3 DAM", body_style),
            Paragraph("Strict least-privilege IAM roles, automated document extraction, and pre-signed preview URLs.", body_style),
        ],
    ]
    arch_table = Table(arch_rows, colWidths=[100, 120, 284])
    arch_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(arch_table)
    story.append(Spacer(1, 12))

    # Section 3
    story.append(Paragraph("3. Core Migration Deliverables & Schema Matrix", h1_style))
    story.append(Paragraph(
        "For every content package or document submitted, BRIDGE outputs structured artifacts:",
        body_style,
    ))
    story.append(Paragraph("• <b>Migration Readiness Score (0–100):</b> Algorithmic index reflecting schema parity, type conflicts, and automated transform feasibility.", bullet_style))
    story.append(Paragraph("• <b>Field Mapping Matrix:</b> Explicit pairs of source field vs. target field with required data type conversions (e.g., HTML string &rarr; RichText AST, timestamp &rarr; ISO 8601 UTC).", bullet_style))
    story.append(Paragraph("• <b>Target Ingestion Payload:</b> Production-ready JSON formatted according to the target Headless CMS schema specification (Contentful / Strapi / Sanity), ready to copy with a single click.", bullet_style))
    story.append(Paragraph("• <b>Exception & Risk Log:</b> Detailed enumeration of unmapped assets, orphan taxonomy terms, or missing mandatory fields with recommended remediation steps.", bullet_style))

    story.append(PageBreak())

    # Section 4
    story.append(Paragraph("4. Enterprise Zero-Bug Architecture Compliance", h1_style))
    story.append(Paragraph(
        "BRIDGE strictly implements every design rule and fix mandated in the <b>Global Agent Zero-Bug Manifesto</b>:",
        body_style,
    ))

    bug_rows = [
        [Paragraph("<b>Standard Rule</b>", body_style), Paragraph("<b>BRIDGE Implementation Detail</b>", body_style)],
        [
            Paragraph("Single Navigation Button", body_style),
            Paragraph("Header strictly features one unified HOME button. No redundant workspace buttons or duplicate links.", body_style),
        ],
        [
            Paragraph("Hover-Only Sidebar Actions", body_style),
            Paragraph("Edit and Delete icons remain completely invisible (`display: none;`) until the user hovers over the conversation row (`.histRow:hover .histActions { display: flex; }`).", body_style),
        ],
        [
            Paragraph("Smart Title Derivation", body_style),
            Paragraph("Conversational noise ('Can you please', 'Kindly migrate', 'ji', 'hi') is automatically stripped. Titles are derived from schema filenames or AI structured topics.", body_style),
        ],
        [
            Paragraph("Sleek Findings Ribbon", body_style),
            Paragraph("Eliminated bulky oversized square boxes. Replaced with an ultra-compact horizontal metrics bar (~36px height) with glowing status indicators.", body_style),
        ],
        [
            Paragraph("No Empty Voids in Cards", body_style),
            Paragraph("Recent cards feature compact geometry (`min-height: auto; padding: 14px 16px;`). Snippets prioritize migration summary and never show bare 'hi'.", body_style),
        ],
        [
            Paragraph("Inline Document Viewer", body_style),
            Paragraph("Uploaded documents generate immediate local blob previews with zero re-upload latency. No duplicate 'Open in Viewer' button in AI cards.", body_style),
        ],
    ]
    bug_table = Table(bug_rows, colWidths=[150, 354])
    bug_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEF3C7")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FCD34D")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(bug_table)
    story.append(Spacer(1, 14))

    # Section 5
    story.append(Paragraph("5. Verification & Live Operational Endpoints", h1_style))
    story.append(Paragraph(
        "All live endpoints and UI distributions have been tested and verified 100% operational:",
        body_style,
    ))

    story.append(Paragraph("• <b>CloudFront Production URL:</b> https://d23utb1q5zn42x.cloudfront.net", bullet_style))
    story.append(Paragraph("• <b>API Gateway Production URL:</b> https://hjwkic438k.execute-api.us-east-1.amazonaws.com", bullet_style))
    story.append(Paragraph("• <b>Health Endpoint:</b> GET /api/health &rarr; HTTP 200 OK", bullet_style))
    story.append(Paragraph("• <b>Migration Endpoint:</b> POST /api/migrate & POST /api/bridge/migrate &rarr; HTTP 200 OK", bullet_style))
    story.append(Paragraph("• <b>Typo Interceptor:</b> Instant greeting response without Bedrock latency or hallucination for 'ji', 'hi', 'helo'.", bullet_style))

    story.append(Spacer(1, 14))
    story.append(Paragraph("6. Quick Start Guide for Engineers", h1_style))
    story.append(Paragraph(
        "1. Open the CloudFront URL in your browser.<br/>"
        "2. Click the attachment icon to select an export file (.json, .csv, .docx, .html, .txt) or paste a schema dump into the input field.<br/>"
        "3. Press Enter or click the arrow button to trigger schema analysis.<br/>"
        "4. Review the Migration Readiness Score and inspect the Field Mapping Matrix tabs.<br/>"
        "5. Click 'Copy Payload' to copy the formatted target headless CMS payload for automated API ingestion.",
        body_style,
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Study Guide PDF generated successfully: {filename}")


if __name__ == "__main__":
    out_path = Path("bridge/BRIDGE_BEGINNER_STUDY_GUIDE.pdf")
    build_pdf(str(out_path))

