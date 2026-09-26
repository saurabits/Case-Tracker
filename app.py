import os
from flask import Flask, abort, render_template, request, send_file
import pandas as pd

app = Flask(__name__)

EXCEL_FILE = "cases.xlsx"

# Map document types to their corresponding Excel date column names
DOC_CONFIG = {
    "OPN": {"date_col": "OPN Updated Date"},
    "FIR": {"date_col": "FIR Date"},
    "Chargesheet": {"date_col": "Chargesheet Date"},
    "Trial Plan & Calendar": {"date_col": ""},  # No date required
    "Charge Order": {"date_col": "Charge Date"},
    "Trial Progress": {"date_col": "Last Hearing Date"},
    "FRs and Comments": {
        "date_col": "",
        "file_name": "FR and Comments",
        "extensions": [".pdf"],
    },
}


def load_cases():
  if not os.path.exists(EXCEL_FILE):
    return []
  df = pd.read_excel(EXCEL_FILE)
  df = df.fillna("")
  records = df.to_dict(orient="records")

  for record in records:
    base_path = str(record.get("Folder Path", "")).strip()
    record["doc_links"] = {}

    for base_doc_name, config in DOC_CONFIG.items():
      # 1. Check file path availability in the local folder
      found_path = ""
      file_name = config.get("file_name", base_doc_name)
      if base_path and os.path.exists(base_path):
        extensions = config.get(
            "extensions", [".pdf", ".docx", ".doc", ".txt", ".xlsx", ""]
        )
        for ext in extensions:
          potential_path = os.path.join(base_path, f"{file_name}{ext}")
          if os.path.exists(potential_path) and os.path.isfile(potential_path):
            found_path = potential_path
            break

      # 2. Extract specific date with flexible column lookup
      date_col = config["date_col"]
      raw_date = ""
      if date_col:
        if date_col in record:
          raw_date = record[date_col]
        else:
          for k, v in record.items():
            if k.strip().lower() == date_col.strip().lower():
              raw_date = v
              break

      formatted_date = ""
      if raw_date:
        try:
          if isinstance(raw_date, pd.Timestamp):
            formatted_date = raw_date.strftime("%d.%m.%Y")
          else:
            # Convert string/date objects into DD.MM.YYYY if standard format
            parsed_date = pd.to_datetime(raw_date, errors="coerce")
            if pd.notnull(parsed_date):
              formatted_date = parsed_date.strftime("%d.%m.%Y")
            else:
              formatted_date = str(raw_date).split("T")[0]
        except Exception:
          formatted_date = str(raw_date)

      # 3. Construct label (Concatenate name with date if available)
      if formatted_date:
        button_label = f"{base_doc_name} {formatted_date}"
      else:
        button_label = base_doc_name

      record["doc_links"][base_doc_name] = {
          "path": found_path,
          "label": button_label,
      }

  return records


@app.route("/")
def index():
  cases = load_cases()
  return render_template("index.html", cases=cases)


@app.route("/view-file")
def view_file():
  file_path = request.args.get("path", "")
  if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
    mimetype = "application/pdf" if file_path.lower().endswith(".pdf") else None
    return send_file(file_path, mimetype=mimetype)
  return abort(404, description="File not found.")


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5001, debug=True)
