import os
from pathlib import Path

import pandas as pd
from flask import Flask, abort, render_template, request, send_file

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "cases.xlsx"

DOC_CONFIG = {
    "OPN": {"date_col": "OPN Updated Date"},
    "FIR": {"date_col": "FIR Date"},
    "Chargesheet": {"date_col": "Chargesheet Date"},
    "FR & Comments": {
        "date_col": "",
        "file_name": "FR and Comments",
        "extensions": [".pdf"],
    },
}


def _folder_path(raw_path):
    """Resolve stored paths while allowing the workbook to move with the app."""
    path = Path(str(raw_path).strip()).expanduser()
    if path.is_dir():
        return path
    portable_path = BASE_DIR / path.name
    return portable_path if portable_path.is_dir() else path


def _formatted_date(raw_date):
    if not raw_date:
        return ""
    parsed = pd.to_datetime(raw_date, errors="coerce")
    if pd.notnull(parsed):
        return parsed.strftime("%d.%m.%Y")
    return str(raw_date).split("T")[0]


def load_cases():
    if not EXCEL_FILE.exists():
        return []

    records = pd.read_excel(EXCEL_FILE).fillna("").to_dict(orient="records")
    for index, record in enumerate(records):
        record["id"] = index
        record["case_number"] = record.get("Case No / CC No", record.get("Case Number", ""))
        record["hio"] = record.get("HIO", record.get("Client Name", ""))
        folder = _folder_path(record.get("Folder Path", ""))
        record["doc_links"] = {}

        for document_name, config in DOC_CONFIG.items():
            found_path = ""
            file_name = config.get("file_name", document_name)
            extensions = config.get("extensions", [".pdf", ".docx", ".doc", ".txt", ".xlsx", ""])
            if folder.is_dir():
                for extension in extensions:
                    candidate = folder / f"{file_name}{extension}"
                    if candidate.is_file():
                        found_path = str(candidate.resolve())
                        break

            date_value = record.get(config["date_col"], "") if config["date_col"] else ""
            record["doc_links"][document_name] = {
                "path": found_path,
                "date": _formatted_date(date_value),
            }
    return records


@app.route("/")
def index():
    return render_template("index.html", cases=load_cases())


@app.route("/case/<int:case_id>")
def case_detail(case_id):
    cases = load_cases()
    if case_id < 0 or case_id >= len(cases):
        abort(404)
    return render_template("case_detail.html", case=cases[case_id])


@app.route("/view-file")
def view_file():
    requested_path = Path(request.args.get("path", "")).resolve()
    allowed_paths = {
        Path(info["path"]).resolve()
        for case in load_cases()
        for info in case["doc_links"].values()
        if info["path"]
    }
    if requested_path in allowed_paths and requested_path.is_file():
        mimetype = "application/pdf" if requested_path.suffix.lower() == ".pdf" else None
        return send_file(requested_path, mimetype=mimetype)
    abort(404, description="File not found.")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
