import csv
import io
from datetime import datetime


def employees_csv(employees: list[dict]) -> str:
    if not employees:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(employees[0].keys()))
    writer.writeheader()
    writer.writerows(employees)
    return output.getvalue()


def pdf_report(metrics: dict, employees: list[dict]) -> bytes:
    lines = [
        "AI Employee Attrition Analytics Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Total Employees: {metrics['total_employees']}",
        f"Employees At Risk: {metrics['employees_at_risk']}",
        f"Average Salary: {metrics['average_salary']}",
        f"Average Satisfaction: {metrics['average_satisfaction']}",
        f"Attrition Rate: {round(metrics['attrition_rate'] * 100, 2)}%",
        "",
        "Departments:",
    ]
    for department, total in metrics["departments"].items():
        lines.append(f"- {department}: {total}")
    lines.extend(["", "Sample Employees:"])
    for employee in employees[:18]:
        lines.append(
            f"#{employee['id']} {employee['Department']} | {employee['JobRole']} | "
            f"OverTime: {employee['OverTime']} | Attrition: {employee['Attrition']}"
        )
    return _simple_pdf(lines)


def _simple_pdf(lines: list[str]) -> bytes:
    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    text_ops = ["BT", "/F1 12 Tf", "50 780 Td"]
    for index, line in enumerate(escaped_lines):
        if index:
            text_ops.append("0 -18 Td")
        text_ops.append(f"({line}) Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)
