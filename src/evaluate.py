import sys

from agent import question_to_sql
from db import run_query

# (question in French, reference SQL written by hand)
EASY = [
    ("Combien de communes y a-t-il dans la base ?",
     "SELECT COUNT(*) FROM communes"),
    ("Combien de communes ont une couverture fibre inférieure à 50 % ?",
     "SELECT COUNT(*) FROM communes WHERE couverture_ftth_pct < 50"),
    ("Quelle est la couverture fibre moyenne dans le département 77 ?",
     "SELECT AVG(couverture_ftth_pct) FROM communes WHERE code_departement = '77'"),
    ("Quelles sont les 3 communes avec le plus de locaux dans le département 13 ?",
     "SELECT nom_commune FROM communes WHERE code_departement = '13' ORDER BY locaux DESC LIMIT 3"),
    ("Combien de communes du département 31 ont 100 % de couverture fibre ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '31' AND couverture_ftth_pct = 100"),
    ("Quel est le nombre total de locaux en France ?",
     "SELECT SUM(locaux) FROM communes"),
    ("Quelle commune a le plus de locaux ?",
     "SELECT nom_commune FROM communes ORDER BY locaux DESC LIMIT 1"),
    ("Combien de communes compte le département 2A ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '2A'"),
    ("Combien de communes du département 77 ont une couverture 4G fixe supérieure à 90 % ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '77' AND couverture_4g_fixe_pct > 90"),
    ("Quel département compte le plus de communes ?",
     "SELECT code_departement FROM communes GROUP BY code_departement ORDER BY COUNT(*) DESC LIMIT 1"),
]

HARD = [
    ("Combien de communes ont plus de 90 % de fibre et moins de 50 % de 4G fixe ?",
     "SELECT COUNT(*) FROM communes WHERE couverture_ftth_pct > 90 AND couverture_4g_fixe_pct < 50"),
    ("Quelle est la part des locaux éligibles à la fibre en France, en pourcentage ?",
     "SELECT 100.0 * SUM(locaux_eligibles_ftth) / SUM(locaux) FROM communes"),
    ("Quel département a la meilleure couverture fibre moyenne ?",
     "SELECT code_departement FROM communes GROUP BY code_departement ORDER BY AVG(couverture_ftth_pct) DESC LIMIT 1"),
    ("Combien de communes de l'Ain ont moins de 80 % de fibre ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '01' AND couverture_ftth_pct < 80"),
    ("Combien de communes du Rhône n'ont pas de cuivre ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '69' AND locaux_eligibles_cuivre = 0"),
    ("Combien de communes ont plus de 10000 locaux ?",
     "SELECT COUNT(*) FROM communes WHERE locaux > 10000"),
    ("Dans le département 77, combien de communes ont une meilleure couverture fibre que la moyenne du département ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '77' AND couverture_ftth_pct > (SELECT AVG(couverture_ftth_pct) FROM communes WHERE code_departement = '77')"),
]

# New questions written AFTER the prompt was improved, to check that the fixes generalize.
VALID = [
    ("Combien de communes de la Haute-Garonne ont moins de 70 % de fibre ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '31' AND couverture_ftth_pct < 70"),
    ("Quelle est la part des locaux éligibles à la 4G fixe en Seine-et-Marne, en pourcentage ?",
     "SELECT 100.0 * SUM(locaux_eligibles_4g_fixe) / SUM(locaux) FROM communes WHERE code_departement = '77'"),
    ("Combien de communes du Nord n'ont pas de coaxial ?",
     "SELECT COUNT(*) FROM communes WHERE code_departement = '59' AND locaux_eligibles_coaxial = 0"),
    ("Quelle est la part des locaux éligibles à la fibre dans le Finistère, en pourcentage ?",
     "SELECT 100.0 * SUM(locaux_eligibles_ftth) / SUM(locaux) FROM communes WHERE code_departement = '29'"),
]


def values(rows):
    """Flatten rows into a set of values (floats rounded)."""
    out = set()
    for row in rows:
        for v in row:
            out.add(round(v, 2) if isinstance(v, float) else v)
    return out


if "valid" in sys.argv:
    tests = VALID
elif "hard" in sys.argv:
    tests = HARD
else:
    tests = EASY
passed = 0
for question, reference in tests:
    _, expected = run_query(reference)
    try:
        sql = question_to_sql(question)
        _, got = run_query(sql)
        ok = values(expected) <= values(got)
    except Exception as error:
        sql, ok = f"ERROR: {error}", False
    passed += ok
    print("PASS" if ok else "FAIL", "-", question)
    if not ok:
        print("   generated:", sql)

print(f"\nScore: {passed}/{len(tests)}")
