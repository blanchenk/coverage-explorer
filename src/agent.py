import re
import sys

import ollama

from db import run_query
from departments import find_departments

MODEL = "qwen2.5-coder:7b"

SYSTEM_PROMPT = """You turn questions (in French or English) into one SQLite query.

Table: communes (one row per French commune, ARCEP data on fixed internet coverage)
Columns:
- code_insee (text): commune code
- nom_commune (text): commune name
- code_departement (text): department code such as '01', '77', '2A'
- locaux (integer): number of premises
- locaux_eligibles_ftth (integer): premises eligible to fibre (FTTH)
- couverture_ftth_pct (real): fibre coverage in percent (0 to 100)
- locaux_eligibles_coaxial, locaux_eligibles_cuivre, locaux_eligibles_4g_fixe,
  locaux_eligibles_thd_radio, locaux_eligibles_hd_radio, locaux_eligibles_satellite (integer):
  premises eligible to each technology
- couverture_coaxial_pct, couverture_cuivre_pct, couverture_4g_fixe_pct,
  couverture_thd_radio_pct, couverture_hd_radio_pct, couverture_satellite_pct (real):
  coverage in percent for cable, copper, fixed 4G, radio and satellite
- millesime_arcep (text): date of the data

Rules:
- Answer with exactly one SELECT query inside a ```sql code block, nothing else.
- Department codes are text: write code_departement = '77'.
- If the question comes with a note giving a department code, use that code.
- A share of premises for a department or for France must be weighted by the number of
  premises, not an average of commune percentages. Example for fibre:
  100.0 * SUM(locaux_eligibles_ftth) / SUM(locaux). Use AVG(couverture_..._pct) only when
  the question asks for the average of the communes' percentages.
- Add LIMIT 20 unless the question asks for a count or an average.
"""


def add_department_note(question):
    """Convert department names to codes with plain code, not with the model."""
    found = find_departments(question)
    if not found:
        return question
    codes = ", ".join(f"{name} = '{code}'" for code, name in found.items())
    return f"{question}\n\nNote: department codes (column code_departement): {codes}."


def question_to_sql(question):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": add_department_note(question)},
        ],
    )
    text = response["message"]["content"]
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip()


def explain(question, columns, rows):
    data = f"columns: {columns}\nrows: {rows[:20]}"
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Answer the question in one or two clear sentences in French, "
                    "using only the data below.\n\n"
                    f"Question: {question}\n{data}"
                ),
            }
        ],
    )
    return response["message"]["content"].strip()


if __name__ == "__main__":
    question = sys.argv[1]
    sql = question_to_sql(question)
    print("SQL generated:", sql)
    columns, rows = run_query(sql)
    print("Raw result:", rows[:5])
    print("Answer:", explain(question, columns, rows))
