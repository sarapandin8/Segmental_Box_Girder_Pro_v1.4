"""Report-driven workspace definitions for Segmental Box Girder Pro.

UI labels intentionally omit the word "Chapter" while keeping report numbering
for traceability. Commercial M3F separates Loads into a dedicated workspace and
combines bridge geometry, analysis-model documentation, coordinate-driven section preview, and section properties.
"""

from __future__ import annotations

WORKSPACES = [
    {
        "id": "dashboard",
        "label": "Project Dashboard",
        "title": "Project Dashboard",
        "subpages": ["Overview", "Workflow Status", "Governing Results", "Report Readiness"],
    },
    {
        "id": "criteria",
        "label": "1 Criteria",
        "title": "1 Design Criteria",
        "subpages": ["1.1 Standards", "1.2 Materials", "1.3 Design Basis / Units", "QA / Report Preview"],
    },
    {
        "id": "bridge_geometry",
        "label": "2 Bridge Geometry / Section Properties",
        "title": "2 Bridge Geometry / Section Properties",
        "subpages": [
            "2.1 Bridge Description",
            "2.2 Geometry and Analysis Model",
            "2.3 Section Properties",
            "2.4 Tendon Layout Reference",
            "2.5 Consistency Checks",
            "QA / Report Preview",
        ],
    },
    {
        "id": "loads",
        "label": "3 Loads",
        "title": "3 Loads",
        "subpages": [
            "3.1 Dead Load",
            "3.2 SDL",
            "3.3 LL + IM",
            "3.4 LF / 3.5 HF",
            "3.6 CF",
            "3.7 Wind",
            "3.8 CR&SH",
            "3.9 EQ",
            "3.10 FEA Load Input Summary",
            "QA / Report Preview",
        ],
    },
    {
        "id": "prestress_losses",
        "label": "4 Prestress Losses",
        "title": "4 Prestress Losses",
        "subpages": ["4.1 General", "4.2 Friction", "4.3 Anchor Set", "4.4 Elastic Shortening", "4.5 Time-Dependent Losses", "4.6 Effective Prestress", "QA / Report Preview"],
    },
    {
        "id": "fea_results",
        "label": "5 FEA Results",
        "title": "5 Analysis Results",
        "subpages": [
            "5.1 Import / Data Hub",
            "5.2 ULS Envelope",
            "5.3 Transfer Stage",
            "5.4 Final Service SLS",
            "5.5 QA / Source Trace",
        ],
    },
    {
        "id": "uls_flexure",
        "label": "6 ULS Flexure",
        "title": "6 ULS Flexural Design",
        "subpages": ["6.1 Basis", "6.2 Capacity", "6.3 Span Results", "QA / Report Preview"],
    },
    {
        "id": "uls_shear_torsion",
        "label": "7 ULS Shear / Torsion",
        "title": "7 ULS Shear and Torsion Design",
        "subpages": ["7.1 Basis", "7.2 Critical Section", "7.3 Shear Check", "7.4 Torsion Check", "7.5 Reinforcement", "QA / Report Preview"],
    },
    {
        "id": "sls_stress",
        "label": "8 SLS Stress",
        "title": "8 SLS Stress Check",
        "subpages": ["8.1 Basis", "8.2 Transfer", "8.3 Final", "QA / Report Preview"],
    },
    {
        "id": "deflection",
        "label": "9 Deflection",
        "title": "9 Deflection Check",
        "subpages": ["9.1 Criteria", "9.2 Camber", "9.3 Live Load Deflection", "QA / Report Preview"],
    },
    {
        "id": "report_qa",
        "label": "Report / QA",
        "title": "Report / QA",
        "subpages": ["QA Summary", "Validation Issues", "Report Preview", "Export"],
    },
]

WORKSPACE_BY_LABEL = {w["label"]: w for w in WORKSPACES}
WORKSPACE_BY_ID = {w["id"]: w for w in WORKSPACES}
WORKSPACE_LABELS = [w["label"] for w in WORKSPACES]


def get_workspace(label: str) -> dict:
    return WORKSPACE_BY_LABEL.get(label, WORKSPACES[0])
