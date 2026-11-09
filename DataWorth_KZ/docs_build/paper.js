const fs = require('fs');
const d = require('docx');
const {Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun, LevelFormat, PageNumber, Footer, PageBreak, TableOfContents} = d;
const F = "Times New Roman", SZ = 28;
const FIG = "/home/claude/dw/DataWorth_KZ/figures/", RES = "/home/claude/dw/DataWorth_KZ/results/";
const sizeOf = (f) => { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
function runs(text, base = {}) {
  const out = []; const parts = text.split(/(\*\*[^*]+\*\*)/);
  for (const p of parts) { if (!p) continue;
    if (p.startsWith('**')) out.push(new TextRun({ text: p.slice(2, -2), bold: true, font: F, size: base.size || SZ, italics: base.italics }));
    else out.push(new TextRun({ text: p, font: F, size: base.size || SZ, italics: base.italics, bold: base.bold })); }
  return out;
}
const P = (t, o = {}) => new Paragraph({ indent: o.noIndent ? undefined : { firstLine: 709 }, alignment: o.align || AlignmentType.JUSTIFIED, spacing: { after: 0 }, children: runs(t, o) });
const W = 9638;
function csv(f) { const L = fs.readFileSync(RES + f, 'utf8').trim().split('\n'); const p = l => { const o = []; let c = '', q = false; for (const ch of l) { if (ch == '"') { q = !q; continue; } if (ch == ',' && !q) { o.push(c); c = ''; } else c += ch; } o.push(c); return o; };
  const h = p(L[0]); return L.slice(1).map(l => { const r = p(l); const o = {}; h.forEach((k, i) => o[k] = r[i]); return o; }); }
function T(head, rows, widths, fs = 22) {
  const cell = (t, i, h) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, shading: h ? { type: ShadingType.CLEAR, fill: "DCE6F5", color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 70, right: 70 }, children: [new Paragraph({ alignment: i == 0 ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), font: F, size: fs, bold: h })] })] });
  return new Table({ width: { size: widths.reduce((a, b) => a + b), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((t, i) => cell(t, i, true)) }), ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((t, i) => cell(t, i, false)) }))] });
}
const nf = (x, d = 0) => Number(x).toLocaleString('ru-RU', { minimumFractionDigits: d, maximumFractionDigits: d }).replace(/ /g, ' ');
const f3 = x => nf(x, 3), pc = x => nf(x * 100, 1) + '%';
const ALG = { LogReg: "Logistic Regression", RandomForest: "Random Forest", GradBoost: "Gradient Boosting" };
const mc = csv('model_comparison.csv'), fin = csv('financial_main_models.csv'), pdif = csv('paired_differences.csv'), summ = JSON.parse(fs.readFileSync(RES + 'dvf_summary.json')).profit_diff_bootstrap_base;
const dvfo = csv('dvf_frontier.csv');
const RM = JSON.parse(fs.readFileSync('refmap.json')); const rf = (...k) => '[' + k.map(x => RM[x]).sort((a, b) => a - b).join(',') + ']';
const TABLES = {
  kzstat: () => T(["Көрсеткіш", "Мәні", "Күні", "Дереккөз"], [
    ["Банк секторының активтері", "75,6 трлн ₸", "01.08.2026", "ҚНРДА [27]"],
    ["Экономикаға берілген кредиттер портфелі", "42,1 трлн ₸", "01.08.2026", "ҚНРДА [27]"],
    ["Жеке тұлғаларға кредиттер", "26,1 трлн ₸", "01.08.2026", "ҚНРДА [27]"],
    ["   оның ішінде тұтынушылық қарыздар", "17,4 трлн ₸", "01.08.2026", "ҚНРДА [27]"],
    ["   оның ішінде ипотека", "7,6 трлн ₸", "01.08.2026", "ҚНРДА [27]"],
    ["NPL90+, бүкіл портфель", "4,1% (1,9 трлн ₸)", "01.08.2026", "ҚНРДА [27]"],
    ["NPL90+, жеке тұлғалар портфелі", "4,7% (1,2 трлн ₸)", "01.08.2026", "ҚНРДА [27]"],
    ["NPL90+, бизнес портфелі", "3,9% (625 млрд ₸)", "01.08.2026", "ҚНРДА [27]"],
    ["Жұмыс істемейтін қарыздардың провизиялармен жабылуы", "60,4%", "01.08.2026", "ҚНРДА [27]"],
    ["Жеке тұлғаларға кредит мөлшерлемесі (₸)", "20,3%", "2026, шілде", "ҚНРДА [27]"],
    ["Тұтынушылық қарыздар мөлшерлемесі (₸)", "22,5%", "2026, шілде", "ҚНРДА [27]"],
    ["Жеке тұлғалардың мерзімді депозиттері (₸)", "14,7%", "2026, шілде", "ҚНРДА [27]"],
    ["Ұлттық Банктің базалық мөлшерлемесі", "15,75%", "23.10.2026 шешімі", "Ұлттық Банк [32]"],
    ["Кредиттік бюродағы халық қарызы", "27,5 трлн ₸; 8,95 млн қарыз алушы; 39,4 млн кредит", "01.01.2026", "БКБ, Tengrinews [33]"]],
    [3600, 2500, 1500, 2038], 19),
  hybrid: () => T(["Міндет", "Тайвань деректері (UCI, 2005)", "Қазақстан деректері (2026)"], [
    ["Клиент деңгейіндегі PD болжамы", "Иә — модельдер оқытылады", "Жоқ"],
    ["Алгоритмдерді салыстыру (LR, RF, GB)", "Иә", "Жоқ"],
    ["ROC-AUC, PR-AUC, Precision, Recall, Brier", "Иә", "Жоқ"],
    ["Ақпарат жиынтықтарының болжам сапасы, 64 комбинация", "Иә", "Жоқ"],
    ["Маржа m (кредит және қаржыландыру мөлшерлемесі)", "Жоқ (бастапқыда болжам)", "Иә — ресми мөлшерлемелер"],
    ["Нарық көлемі, портфель құрылымы, NPL90+", "Жоқ", "Иә — тек контекст"],
    ["Сомаларды теңгеге масштабтау (Ē_KZ)", "Жоқ", "Иә — бюро деректерінен есептелген"],
    ["LGD, CCF, c, λ", "Болжам", "Болжам (ресми статистика табылмады)"],
    ["Клиенттік деректер мен дефолт белгісі", "Иә", "Пайдаланылмады (қолжетімсіз)"]],
    [3900, 2800, 2938], 19),
  kzpar: () => T(["Параметр", "1 — базалық", "2 — жоғары тәуекел", "3 — деректер құны жоғары", "Мәртебесі"], [
    ["Кредит мөлшерлемесі r_кредит", "22,5%", "22,5%", "22,5%", "Ресми [27]"],
    ["Қаржыландыру құны", "14,7% (депозит)", "15,75% (базалық мөлш.)", "14,7% (депозит)", "Ресми [27,32]"],
    ["Маржа m, жылдық", "7,8%", "6,75%", "7,8%", "Есептелген, (9)"],
    ["LGD", "75%", "90%", "75%", "Болжам"],
    ["CCF", "50%", "50%", "50%", "Болжам"],
    ["Ē_KZ, ₸", "≈ 698 000", "≈ 698 000", "≈ 698 000", "Есептелген [33]"],
    ["c, б.п./топ", "0", "0", "10", "Болжам"],
    ["λ, б.п./өріс", "0", "0", "5", "Болжам"],
    ["Бейс шегі t* = m/(m+LGD)", "0,094", "0,070", "0,094", "Есептелген"]],
    [2700, 1500, 1800, 1900, 1738], 19),
  kzres: () => { const m = csv('kz_models.csv'), b = csv('kz_bootstrap.csv');
    const SC = { TW_base: "Тайвань параметрлері (m 10%; LGD 75%)", KZ1_base: "1 — базалық (7,8%; 75%)", KZ2_high_risk: "2 — жоғары тәуекел (6,75%; 90%)" };
    const rows = [];
    for (const sc of Object.keys(SC)) for (const a of ["GradBoost", "RandomForest"]) {
      const v = s => nf(m.find(r => r.scenario == sc && r.algo == a && r.set == s).profit_pc_kzt);
      const cb = b.find(r => r.scenario == sc && r.algo == a && r.comparison == 'C-B');
      rows.push([SC[sc], ALG[a], v('A'), v('B'), v('C'), `${Number(cb.mean_diff_kzt) >= 0 ? '+' : ''}${nf(cb.mean_diff_kzt)} (${nf(cb.ci95_lo)}…${nf(cb.ci95_hi)})`, nf(cb.U95_pct_of_PiB, 1) + '%']); }
    return T(["Сценарий", "Алгоритм", "Π(A)", "Π(B)", "Π(C)", "C − B (95% CI)", "U95 / Π(B)"], rows, [2500, 1600, 900, 900, 900, 1838, 1000], 18); },
  kzopt: () => { const o = csv('kz_optimal.csv');
    const SC = { TW_base: ["Тайвань параметрлері", "10%; 75%; 0; 0"], KZ1_base: ["1 — базалық", "7,8%; 75%; 0; 0"], KZ2_high_risk: ["2 — жоғары тәуекел", "6,75%; 90%; 0; 0"], KZ3_data_cost: ["3 — деректер құны жоғары", "7,8%; 75%; 10; 5"], KZ_monthly: ["Айлық көкжиек (тексеріс)", "0,65%; 75%; 0; 0"] };
    return T(["Сценарий", "m; LGD; c; λ", "Оңтайлы жиынтық (өріс)", "V(S*)", "V(B)", "V(C)"],
      Object.keys(SC).map(k => { const r = o.find(x => x.scenario == k); return [SC[k][0], SC[k][1], `${r.optimal_subset} (${r.n_fields})`, nf(r.test_net_value_pc_kzt), nf(r.B_test_net_value_pc_kzt), nf(r.C_test_net_value_pc_kzt)]; }),
      [2500, 1700, 2000, 1100, 1100, 1238], 19); },

  opt: () => { const c = csv('revision_cost_scan.csv');
    return T(["Деректер тобының құны c, б.п.", "Оңтайлы жиынтық", "Өрістер", "Test V(S), NT$/клиент"], c.map(r => [r.data_cost_bp, r.optimal_subset, r.n_fields, nf(r.test_net_value_pc)]), [3000, 2600, 1400, 2638], 20); },
  boot: () => { const b = csv('revision_bootstrap.csv').filter(r => r.ead == 'balance_based');
    const SC = { base: "Базалық", conservative: "Консервативті", optimistic: "Оптимистік", monthly_2pct: "Айлық (2%; 75%)" };
    const rows = [];
    for (const sc of ["base", "conservative", "optimistic", "monthly_2pct"]) for (const a of ["GradBoost", "RandomForest"]) {
      const ba = b.find(r => r.scenario == sc && r.algo == a && r.comparison == 'B-A'), cb = b.find(r => r.scenario == sc && r.algo == a && r.comparison == 'C-B');
      const pctB = cb.U95_pct_of_PiB === '' || cb.U95_pct_of_PiB === undefined || isNaN(Number(cb.U95_pct_of_PiB)) || cb.U95_pct_of_PiB === 'nan' ? '—' : nf(cb.U95_pct_of_PiB, 1) + '%';
      rows.push([SC[sc], ALG[a], `${Number(ba.mean_diff) >= 0 ? '+' : ''}${nf(ba.mean_diff)} (${nf(ba.ci95_lo)}…${nf(ba.ci95_hi)})`, `${Number(cb.mean_diff) >= 0 ? '+' : ''}${nf(cb.mean_diff)} (${nf(cb.ci95_lo)}…${nf(cb.ci95_hi)})`, nf(cb.one_sided_U95), pctB]); }
    return T(["Сценарий", "Алгоритм", "B − A (95% CI)", "C − B (95% CI)", "U95(C − B)", "U95 / Π(B)"], rows, [1500, 1800, 2000, 2000, 1138, 1200], 19); },
  scen: () => { const b = csv('revision_bootstrap.csv').filter(r => r.algo == 'GradBoost' && r.comparison == 'C-B'); const o = csv('revision_optimal_by_ead.csv');
    const SC = { conservative: "Консервативті (5%; 90%)", base: "Базалық (10%; 75%)", optimistic: "Оптимистік (20%; 45%)", monthly_2pct: "Айлық (2%; 75%)" };
    const rows = [];
    for (const e of ["balance_based", "limit_based"]) for (const sc of Object.keys(SC)) { const r = b.find(x => x.ead == e && x.scenario == sc); const op = o.find(x => x.ead == e && x.scenario == sc);
      rows.push([SC[sc], e == 'balance_based' ? 'Шот қалдығы' : 'Лимит', nf(r.profit_A), nf(r.profit_B), nf(r.profit_C), `${op.optimal_subset} (${op.n_scoring_fields})`]); }
    return T(["Сценарий (m; LGD)", "EAD", "Π(A)", "Π(B)", "Π(C)", "Оңтайлы жиынтық"], rows, [2500, 1300, 1100, 1100, 1100, 2538], 19); },
  lit: () => T(["Зерттеу", "Сұрақ", "Құн өлшемі", "Деректер шығыны / құпиялық"], [
    ["Lessmann т.б., 2015 [7]", "Қай алгоритм жақсы?", "AUC, Brier т.б.", "Ескерілмейді"],
    ["Verbraken т.б., 2014 [9]", "Скорингті пайда арқылы бағалау", "Күтілетін пайда өлшемі", "Ескерілмейді"],
    ["Óskarsdóttir т.б., 2019 [10]", "Мобильді деректер құнды ма?", "AUC және пайда", "Сапалық талқылау"],
    ["Berg т.б., 2020 [11]", "Цифрлық із бюроны толықтыра ма?", "AUC, дефолт үлесі", "Сапалық талқылау"],
    ["Ghorbani, Zou, 2019 [18]", "Әр деректер нүктесінің үлесі", "Модель сапасы", "Ескерілмейді"],
    ["He т.б., 2023 [12]; Babina т.б., 2025 [13]", "Open Banking бәсекеге әсері", "Әл-ауқат, нарыққа кіру", "Теориялық / нарық деңгейі"],
    ["Осы жұмыс", "Қай деректерден бас тартуға болады?", "Шешімдегі Π(S), V(S), фронтир", "C(S) және λ ашық параметр"]], [2500, 2500, 2300, 2338], 20),
  sets: () => T(["Жиынтық / топ", "Өрістер", "Саны", "Мазмұны"], [
    ["S₀ (Model A)", "LIMIT_BAL, PAY_0", "2", "Лимит және соңғы ай мәртебесі"],
    ["G1", "PAY_2, PAY_3", "2", "2–3 ай бұрынғы төлем мәртебесі"],
    ["G2", "BILL_AMT1", "1", "Соңғы шот қалдығы"],
    ["G3", "PAY_AMT1", "1", "Соңғы төлем сомасы"],
    ["G4", "PAY_4 – PAY_6", "3", "4–6 ай бұрынғы мәртебе"],
    ["G5", "BILL_AMT2 – BILL_AMT6", "5", "2–6 айлық шот тарихы"],
    ["G6", "PAY_AMT2 – PAY_AMT6", "5", "2–6 айлық төлем тарихы"],
    ["Model B = S₀+G1+G2+G3", "—", "6", "Іріктелген ақпарат"],
    ["Model C = S₀+G1…G6", "—", "19", "Кеңейтілген ақпарат"]], [2700, 2600, 900, 3438], 20),
  models: () => T(["Модель", "Алгоритм", "ROC-AUC", "PR-AUC", "Brier", "Precision", "Recall", "F1"],
    mc.map(r => [`${r.set} (${r.n_features})`, ALG[r.algo], `${f3(r.roc_auc)} (${f3(r.roc_auc_ci_lo)}–${f3(r.roc_auc_ci_hi)})`, f3(r.pr_auc), nf(r.brier, 4), f3(r.precision), f3(r.recall), f3(r.f1)]),
    [900, 2000, 2138, 900, 900, 950, 900, 950], 20),
  paired: () => T(["Алгоритм", "Салыстыру", "ΔROC-AUC", "95% CI", "ΔPR-AUC", "95% CI"],
    ["LogReg", "RandomForest", "GradBoost"].flatMap(a => ["B-A", "C-B", "C-A"].map(c => { const r = pdif.find(x => x.type == 'information_effect' && x.algo == a && x.comparison == c && x.metric == 'roc_auc'); const q = pdif.find(x => x.type == 'information_effect' && x.algo == a && x.comparison == c && x.metric == 'pr_auc');
      return [ALG[a], c.replace('-', ' − '), (r.diff >= 0 ? '+' : '') + f3(r.diff), `${f3(r.ci_lo)}…${f3(r.ci_hi)}`, (q.diff >= 0 ? '+' : '') + f3(q.diff), `${f3(q.ci_lo)}…${f3(q.ci_hi)}`]; })),
    [2300, 1300, 1400, 1700, 1400, 1538], 20),
  fin: () => T(["Модель", "Шек t", "Мақұлдау", "Мақұлдан. дефолт", "Π, NT$/кл"],
    fin.filter(r => r.scenario == 'base').map(r => [r.model == 'approve_all' ? 'Барлығын мақұлдау' : `${r.model[0]} · ${ALG[r.model.slice(2)]}`, r.model == 'approve_all' ? '—' : f3(r.threshold), pc(r.approval_rate), pc(r.bad_rate_approved), nf(r.profit_per_client)]),
    [3338, 1400, 1600, 1800, 1500], 20),

  lit: () => T(["Зерттеу", "Сұрақ", "Құн өлшемі", "Деректер шығыны / құпиялық"], [
    [`Lessmann т.б., 2015 ${rf('lessmann')}`, "Қай алгоритм жақсы?", "AUC, Brier т.б.", "Ескерілмейді"],
    [`Verbraken т.б., 2014 ${rf('verbraken')}`, "Скорингті пайда арқылы бағалау", "Күтілетін пайда өлшемі", "Ескерілмейді"],
    [`Óskarsdóttir т.б., 2019 ${rf('oskarsdottir')}`, "Мобильді деректер құнды ма?", "AUC және пайда", "Сапалық талқылау"],
    [`Berg т.б., 2020 ${rf('berg')}`, "Цифрлық із бюроны толықтыра ма?", "AUC, дефолт үлесі", "Сапалық талқылау"],
    [`Ghorbani, Zou, 2019 ${rf('ghorbani')}`, "Әр деректер нүктесінің үлесі", "Модель сапасы", "Ескерілмейді"],
    [`He т.б., 2023; Babina т.б., 2025 ${rf('he', 'babina')}`, "Open Banking бәсекеге әсері", "Әл-ауқат, нарыққа кіру", "Теориялық / нарық деңгейі"],
    ["Осы жұмыс", "Қай деректерден бас тартуға болады?", "Шешімдегі Π(S), V(S), ₸", "C(S) және λ ашық параметр"]], [2500, 2500, 2300, 2338], 20),
  kzstat: () => T(["Көрсеткіш", "Мәні", "Күні", "Дереккөз"], [
    ["Жеке тұлғаларға кредиттер", "24,8 трлн ₸ (2025 ж. +19,8%)", "01.01.2026", rf('forbes_2601')],
    ["Жеке тұлғаларға кредиттер", "26,7 трлн ₸", "01.10.2026", rf('kz24_2610')],
    ["   оның ішінде тұтынушылық", "17,7 трлн ₸", "01.10.2026", rf('kz24_2610')],
    ["   оның ішінде ипотека", "7,9 трлн ₸", "01.10.2026", rf('kz24_2610')],
    ["Жеке тұлғаларға жаңа кредиттер (қыркүйек)", "1,6 трлн ₸ (жылдық −8,8%)", "2026, қыркүйек", rf('kz24_2610')],
    ["NPL90+, бүкіл банк портфелі", "3,9% (1,8 трлн ₸)", "01.10.2026", rf('kz24_2610')],
    ["NPL90+, жеке тұлғалар портфелі", "4,7% (1,2 трлн ₸)", "01.08.2026", rf('ardfm_2608')],
    ["NPL90+, жеке тұлғалар портфелі", "3,4% (575 млрд ₸)", "01.01.2024", rf('ardfm_2501')],
    ["Провизиялармен жабу", "61,5%", "01.10.2026", rf('kz24_2610')],
    ["Тұтынушылық қарыз мөлшерлемесі (₸)", "22,5%", "2026, шілде", rf('ardfm_2608')],
    ["Жеке тұлғалардың мерзімді депозиттері (₸)", "14,7%", "2026, шілде", rf('ardfm_2608')],
    ["Базалық мөлшерлеме", "15,75%", "23.10.2026", rf('nbk_rate')],
    ["Банктердің таза пайдасы / ROE", "2,7 трлн ₸ / 28,4%", "2025 ж.", rf('forbes_2601')]], [3700, 2600, 1500, 1838], 19),
  kzdebt: () => T(["Көрсеткіш", "Мәні", "Күні", "Дереккөз"], [
    ["Кредиттік бюродағы халық қарызы", "27,5 трлн ₸", "01.01.2026", rf('tengri_bureau')],
    ["Қарыз алушылар / кредиттер саны", "8,95 млн / 39,4 млн", "01.01.2026", rf('tengri_bureau')],
    ["Бір қарыз алушыға: кредит / қарыз", "4,4 / ≈ 3,1 млн ₸ (есеп)", "01.01.2026", rf('tengri_bureau')],
    ["Халық саны", "20 590 589 адам", "01.07.2026", rf('zakon_pop')],
    ["Мерзімі 90 күннен асқан қарыз алушылар", "1,5 млн адам", "2023, мамыр", rf('nur_15')],
    ["Мерзімі 90 күннен асқан қарыз алушылар", "≈ 1,6 млн адам", "2025, қазан", rf('finratings_16')],
    ["МҚҰ қарыз алушылары / 90+ кешіккендер", "1,5 млн / 194,6 мың", "2026, мамыр", rf('inbusiness_mfo')],
    ["МҚҰ, жеке тұлғалар NPL90+", "5,1% (бір жыл бұрын 7,4%)", "01.07.2026", rf('ardfm_mfo_2607')],
    ["Банкроттыққа өтініштер (2023 ж. наурыздан)", "270 мыңнан астам, 73%-ы қайтарылған", "2025, шілде", rf('financekz_bk')],
    ["Банкрот деп танылғандар / есептен шығарылған қарыз", "51 мыңнан астам / 188 млрд ₸", "2025 ж.", rf('bes_minfin')],
    ["Жан басына орташа номиналды табыс", "252 619 ₸/ай", "2026, I тоқсан", rf('statgov')]], [3900, 2700, 1400, 1638], 19),
  kzpar: () => T(["Параметр", "1 — базалық", "2 — жоғары тәуекел", "3 — деректер құны жоғары", "Мәртебесі"], [
    ["Кредит мөлшерлемесі r_кредит", "22,5%", "22,5%", "22,5%", `Ресми ${rf('ardfm_2608')}`],
    ["Қаржыландыру құны", "14,7% (депозит)", "15,75% (базалық мөлш.)", "14,7% (депозит)", `Ресми ${rf('ardfm_2608', 'nbk_rate')}`],
    ["Маржа m, жылдық", "7,8%", "6,75%", "7,8%", "Есептелген, (6)"],
    ["LGD", "75%", "90%", "75%", "Болжам"],
    ["CCF", "50%", "50%", "50%", "Болжам"],
    ["Ē_KZ, ₸", "≈ 698 000", "≈ 698 000", "≈ 698 000", `Есептелген ${rf('tengri_bureau')}`],
    ["c, б.п./топ", "0", "0", "10", "Болжам"],
    ["λ, б.п./өріс", "0", "0", "5", "Болжам"],
    ["Шек t* = m/(m+LGD)", "0,094", "0,070", "0,094", "Есептелген"]],
    [2700, 1500, 1800, 1900, 1738], 19),
  kzres: () => { const m = csv('kz_models.csv'), b = csv('kz_bootstrap.csv');
    const SC = { KZ1_base: "1 — базалық (7,8%; 75%)", KZ2_high_risk: "2 — жоғары тәуекел (6,75%; 90%)", TW_base: "Салыстыру: маржа 10%, LGD 75%" };
    const rows = [];
    for (const sc of Object.keys(SC)) for (const a of (sc == 'TW_base' ? ["GradBoost"] : ["GradBoost", "RandomForest"])) {
      const v = s => nf(m.find(r => r.scenario == sc && r.algo == a && r.set == s).profit_pc_kzt);
      const cb = b.find(r => r.scenario == sc && r.algo == a && r.comparison == 'C-B');
      rows.push([SC[sc], ALG[a], v('A'), v('B'), v('C'), `${Number(cb.mean_diff_kzt) >= 0 ? '+' : ''}${nf(cb.mean_diff_kzt)} (${nf(cb.ci95_lo)}…${nf(cb.ci95_hi)})`, nf(cb.U95_pct_of_PiB, 1) + '%']); }
    return T(["Сценарий", "Алгоритм", "Π(A)", "Π(B)", "Π(C)", "C − B (95% CI)", "U95 / Π(B)"], rows, [2500, 1600, 900, 900, 900, 1838, 1000], 18); },
  kzopt: () => { const o = csv('kz_optimal.csv');
    const SC = { KZ1_base: ["1 — базалық", "7,8%; 75%; 0; 0"], KZ2_high_risk: ["2 — жоғары тәуекел", "6,75%; 90%; 0; 0"], KZ3_data_cost: ["3 — деректер құны жоғары", "7,8%; 75%; 10; 5"], KZ_monthly: ["Айлық көкжиек", "0,65%; 75%; 0; 0"] };
    return T(["Сценарий", "m; LGD; c; λ", "Оңтайлы жиынтық (өріс)", "V(S*)", "V(B)", "V(C)"],
      Object.keys(SC).map(k => { const r = o.find(x => x.scenario == k); return [SC[k][0], SC[k][1], `${r.optimal_subset} (${r.n_fields})`, nf(r.test_net_value_pc_kzt), nf(r.B_test_net_value_pc_kzt), nf(r.C_test_net_value_pc_kzt)]; }),
      [2500, 1700, 2000, 1100, 1100, 1238], 19); },
  kzcost: () => { const c = csv('kz_cost_scan.csv');
    return T(["Параметр", "б.п.", "₸ / клиент", "Оңтайлы жиынтық", "Өріс", "V(S*), ₸ (тест)"],
      c.filter(r => ['0', '4', '8', '10', '12', '20'].includes(r.bp) || (r.param == 'lambda' && ['0', '4', '8', '10'].includes(r.bp))).filter((r, i, a) => r.param == 'c' ? ['0', '4', '8', '10', '12', '20'].includes(r.bp) : ['4', '8', '10'].includes(r.bp))
       .map(r => [r.param == 'c' ? 'c (бір топ)' : 'λ (бір өріс)', r.bp, nf(r.kzt_per_client), r.optimal_subset, r.n_fields, nf(r.test_V_kzt)]),
      [2300, 900, 1500, 2300, 900, 1738], 19); },
};
const ch = [];
// title page
const C = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: o.after || 0, before: o.before || 0 }, children: [new TextRun({ text: t, font: F, size: o.size || SZ, bold: o.bold, italics: o.italics })] });
ch.push(C("Narxoz University", { bold: true }), C("«Finance Intelligence: a new era of financial solutions» республикалық ғылыми жобалар конкурсы", { after: 2400 }));
ch.push(C("Ғылыми жұмыс", { after: 240, italics: true }));
ch.push(C("DataWorth KZ: Қазақстанның Open Banking экожүйесінде қаржылық деректердің экономикалық құнын бағалау және құпиялықты ескере отырып кредиттік тәуекелдерді оңтайландыру моделін әзірлеу", { bold: true, after: 240, size: 30 }));
ch.push(C("DataWorth KZ: An Intelligent Framework for Financial Data Valuation and Privacy-Aware Credit Risk Optimization in Kazakhstan’s Open Banking Ecosystem", { italics: true, after: 2400 }));
const R = (t) => new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: t, font: F, size: SZ })] });
ch.push(R("Орындаған: [Аты-жөні], «Қаржы» мамандығының 4-курс студенті"), R("[Университет атауы]"), R("Ғылыми жетекші: [Аты-жөні, ғылыми дәрежесі, лауазымы]"));
ch.push(C("Алматы, 2026", { before: 2200 }));
ch.push(new Paragraph({ children: [new PageBreak()] }));
// TOC page
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "МАЗМҰНЫ", font: F, size: SZ, bold: true })] }));
const toc = fs.existsSync('toc.json') ? JSON.parse(fs.readFileSync('toc.json')) : [];
for (const e of toc) ch.push(new Paragraph({ spacing: { after: 40 }, indent: e.lvl == 2 ? { left: 425 } : undefined, tabStops: [{ type: "right", position: 9638, leader: "dot" }],
  children: [new TextRun({ text: e.text, font: F, size: SZ, bold: e.lvl == 1 }), new TextRun({ text: "\t" + (e.page || ""), font: F, size: SZ })] }));
ch.push(new Paragraph({ children: [new PageBreak()] }));

const lines = fs.readFileSync('paper.txt', 'utf8').split('\n');
let fig = 0;
for (let raw of lines) {
  const l = raw.trimEnd(); if (!l) continue;
  if (l.startsWith('## ')) { ch.push(new Paragraph({ heading: HeadingLevel.HEADING_2, indent: { firstLine: 709 }, children: [new TextRun({ text: l.slice(3), font: F, size: SZ, bold: true })] })); continue; }
  if (l.startsWith('#')) {
    const brk = l.startsWith('#REF') || l.startsWith('#! КІРІСПЕ');
    const txt = l.replace(/^#(!|REF|ANN)?\s*/, '');
    if (brk && ch.length > 0 && !l.startsWith('#ANN')) ch.push(new Paragraph({ children: [new PageBreak()] }));
    ch.push(new Paragraph({ heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, spacing: { before: brk || l.startsWith('#ANN') ? 0 : 360, after: 240 }, children: [new TextRun({ text: txt, font: F, size: SZ, bold: true })] }));
    continue; }
  if (l.startsWith('- ')) { ch.push(new Paragraph({ numbering: { reference: "bul", level: 0 }, alignment: AlignmentType.JUSTIFIED, children: runs(l.slice(2)) })); continue; }
  if (l.startsWith('EQ: ')) { const m = l.slice(4).match(/^(.*)\s(\(\d+\))$/);
    ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 100 }, tabStops: [{ type: "right", position: 9638 }],
      children: [new TextRun({ text: m[1], font: F, size: SZ, italics: true }), new TextRun({ text: "\t" + m[2], font: F, size: SZ })] })); continue; }
  if (l.startsWith('FIG: ')) { const [f, w, cap] = l.slice(5).split(' | '); const [pw, ph] = sizeOf(FIG + f); const ww = Number(w);
    ch.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + f), transformation: { width: ww, height: Math.round(ww * ph / pw) } })] }));
    ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 160 }, children: [new TextRun({ text: cap, font: F, size: 24 })] })); continue; }
  if (l.startsWith('TAB: ')) { const [id, cap] = l.slice(5).split(' | ');
    ch.push(new Paragraph({ alignment: AlignmentType.RIGHT, keepNext: true, spacing: { before: 120, after: 60 }, children: [new TextRun({ text: cap, font: F, size: 24 })] }));
    ch.push(TABLES[id]()); if (id == 'scen') ch.push(P("Оңтайлы жиынтық — деректер құны нөлге тең болғанда validation бойынша таңдалған ең пайдалы жиынтық (жақшада скоринг өрістерінің саны). «Лимит» — EAD = 0,5 × LIMIT_BAL.", { size: 22, noIndent: true }));
    ch.push(new Paragraph({ spacing: { after: 120 }, children: [] })); continue; }
  if (l.startsWith('KW: ')) { ch.push(new Paragraph({ spacing: { before: 120 }, alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 709 }, children: [new TextRun({ text: "Түйін сөздер: ", bold: true, font: F, size: SZ }), new TextRun({ text: l.slice(4).replace('Түйін сөздер: ', ''), font: F, size: SZ, italics: true })] })); continue; }
  if (l.startsWith('REF: ')) { ch.push(new Paragraph({ numbering: { reference: "ref", level: 0 }, alignment: AlignmentType.JUSTIFIED, children: [new TextRun({ text: l.slice(5), font: F, size: SZ })] })); continue; }
  ch.push(P(l));
}
const doc = new Document({
  features: { updateFields: true },
  styles: { default: { document: { run: { font: F, size: SZ } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F, size: SZ, bold: true }, paragraph: { spacing: { before: 0, after: 240 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F, size: SZ, bold: true }, paragraph: { spacing: { before: 200, after: 120 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 993, hanging: 284 } } } }] },
    { reference: "ref", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 709, hanging: 709 } } } }] }] },
  sections: [{ properties: { titlePage: true, page: { size: { width: 11906, height: 16838 }, margin: { left: 1701, top: 1134, right: 567, bottom: 1417 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: F, size: 24 })] })] }), first: new Footer({ children: [] }) },
    children: ch }] });
Packer.toBuffer(doc).then(b => { fs.writeFileSync("DataWorth_KZ_Research.docx", b); console.log("ok"); });
