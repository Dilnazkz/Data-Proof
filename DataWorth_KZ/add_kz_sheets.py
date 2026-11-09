"""Adds the Kazakhstan-adaptation sheets to DataWorth_KZ_Results.xlsx (idempotent)."""
from pathlib import Path
import openpyxl, pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
R = Path("results"); OUT = Path("DataWorth_KZ_Results.xlsx")
wb = openpyxl.load_workbook(OUT)
for n in [s for s in wb.sheetnames if s.startswith("KZ_")]: del wb[n]
H = PatternFill("solid", fgColor="DCE6F5"); BLUE = Font(color="0000FF"); B = Font(bold=True)
def df_sheet(name, df, money=()):
    ws = wb.create_sheet(name)
    ws.append(list(df.columns))
    for c in ws[1]: c.font = B; c.fill = H
    for r in df.itertuples(index=False): ws.append(list(r))
    for j, col in enumerate(df.columns, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = max(12, min(40, len(str(col)) + 4))
        if col in money:
            for i in range(2, len(df) + 2): ws.cell(i, j).number_format = '#,##0;-#,##0'
    return ws
# sources
src = pd.DataFrame([
 ["Активтер", 75.6, "трлн ₸", "01.08.2026", "ҚНРДА", "https://www.gov.kz/memleket/entities/ardfm/press/news/details/1284782?lang=ru"],
 ["Экономикаға кредиттер", 42.1, "трлн ₸", "01.08.2026", "ҚНРДА", "сол"],
 ["Жеке тұлғаларға кредиттер", 26.1, "трлн ₸", "01.08.2026", "ҚНРДА", "сол"],
 ["Тұтынушылық қарыздар", 17.4, "трлн ₸", "01.08.2026", "ҚНРДА", "сол"],
 ["Ипотека", 7.6, "трлн ₸", "01.08.2026", "ҚНРДА", "сол"],
 ["NPL90+ сектор", 0.041, "%", "01.08.2026", "ҚНРДА", "сол"],
 ["NPL90+ жеке тұлғалар", 0.047, "%", "01.08.2026", "ҚНРДА", "сол"],
 ["NPL90+ бизнес", 0.039, "%", "01.08.2026", "ҚНРДА", "сол"],
 ["Провизиялармен жабу", 0.604, "%", "01.08.2026", "ҚНРДА", "сол"],
 ["Жеке тұлғаларға кредит мөлшерлемесі", 0.203, "%", "2026-07", "ҚНРДА", "сол"],
 ["Тұтынушылық қарыз мөлшерлемесі", 0.225, "%", "2026-07", "ҚНРДА", "сол"],
 ["Жеке тұлғалар депозиті", 0.147, "%", "2026-07", "ҚНРДА", "сол"],
 ["Базалық мөлшерлеме", 0.1575, "%", "23.10.2026", "Ұлттық Банк", "https://nationalbank.kz/en/news/press-relizy/20503"],
 ["Бюродағы халық қарызы", 27.5, "трлн ₸", "01.01.2026", "БКБ / Tengrinews", "https://tengrinews.kz/kazakhstan_news/kazahstantsyi-vzyali-kreditov-na-25-trillionov-tenge-601286/"],
 ["Қарыз алушылар", 8.95, "млн", "01.01.2026", "Tengrinews", "сол"],
 ["Кредиттер саны", 39.4, "млн", "01.01.2026", "Tengrinews", "сол"],
], columns=["Көрсеткіш", "Мәні", "Бірлік", "Күні", "Дереккөз", "URL"])
ws = df_sheet("KZ_Sources", src)
for i in range(2, len(src) + 2):
    if ws.cell(i, 3).value == "%": ws.cell(i, 2).number_format = "0.00%"
# parameters with live formulas (inputs blue)
wp = wb.create_sheet("KZ_Parameters")
wp.append(["Параметр", "1 — базалық", "2 — жоғары тәуекел", "3 — деректер құны жоғары", "Мәртебесі"])
for c in wp[1]: c.font = B; c.fill = H
rows = [
 ["Кредит мөлшерлемесі", "=KZ_Sources!B12", "=KZ_Sources!B12", "=KZ_Sources!B12", "Ресми (ҚНРДА)"],
 ["Қаржыландыру құны", "=KZ_Sources!B13", "=KZ_Sources!B14", "=KZ_Sources!B13", "Ресми (ҚНРДА / ҰБ)"],
 ["Маржа m = r − f", "=B2-B3", "=C2-C3", "=D2-D3", "Есептелген, (9)"],
 ["LGD", 0.75, 0.90, 0.75, "Болжам"],
 ["CCF", 0.5, 0.5, 0.5, "Болжам"],
 ["Бейс шегі t*", "=B4/(B4+B5)", "=C4/(C4+C5)", "=D4/(D4+D5)", "Есептелген"],
 ["Ē_KZ, ₸", "=KZ_Sources!B15*1E12/(KZ_Sources!B17*1E6)", "=B8", "=B8", "Есептелген"],
 ["c, б.п./топ", 0, 0, 10, "Болжам"],
 ["λ, б.п./өріс", 0, 0, 5, "Болжам"],
 ["Model B деректер шығыны, ₸/клиент (3 топ, 4 өріс)", "=(3*B9+4*B10)*1E-4*B8", "=(3*C9+4*C10)*1E-4*C8", "=(3*D9+4*D10)*1E-4*D8", "Есептелген, (6)"],
]
for r in rows: wp.append(r)
for i in (5, 6, 9, 10):
    for j in (2, 3, 4): wp.cell(i, j).font = BLUE
for i in (2, 3, 4, 5, 6):
    for j in (2, 3, 4): wp.cell(i, j).number_format = "0.00%"
for j in (2, 3, 4): wp.cell(7, j).number_format = "0.000"; wp.cell(8, j).number_format = "#,##0"; wp.cell(11, j).number_format = "#,##0"
wp.column_dimensions["A"].width = 46
for col in "BCD": wp.column_dimensions[col].width = 22
wp.column_dimensions["E"].width = 22
wp.append([]); wp.append(["Көк — енгізілетін болжамдар; қара — формула. Масштабтау сызықтық: жиынтықтардың реті Ē-ге тәуелді емес."])
df_sheet("KZ_Models", pd.read_csv(R / "kz_models.csv"), money=("profit_pc_kzt",))
df_sheet("KZ_Bootstrap", pd.read_csv(R / "kz_bootstrap.csv"), money=("mean_diff_kzt", "ci95_lo", "ci95_hi", "U95", "profit_B"))
df_sheet("KZ_Optimal", pd.read_csv(R / "kz_optimal.csv"), money=("test_net_value_pc_kzt", "B_test_net_value_pc_kzt", "C_test_net_value_pc_kzt", "S0_test_profit_pc_kzt"))
df_sheet("KZ_Frontier", pd.read_csv(R / "kz_frontier.csv"), money=("test_net_value_pc_kzt",))
df_sheet("KZ_Subsets", pd.read_csv(R / "kz_subsets.csv"), money=("val_profit_pc", "test_profit_pc", "data_cost_pc", "val_net_value_pc", "test_net_value_pc"))
wb.save(OUT); print(wb.sheetnames)
