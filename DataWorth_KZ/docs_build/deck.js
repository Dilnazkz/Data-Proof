const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/root/.claude/skills/synced/370fe811-e530-4f42-aa74-b4a2b2c5548f_f289bea6-5f07-426d-96e7-00873b1ce888/pptx/scripts/apply_theme.js");
const FIG = "/home/claude/dw/DataWorth_KZ/figures/";

const THEME = { name: "DataWorth KZ", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: "0F1B2D", lt1: "FFFFFF", dk2: "0B1F3A", lt2: "F3F6FB", accent1: "1D4ED8", accent2: "EB6834", accent3: "1BAF7A",
            accent4: "2A78D6", accent5: "64748B", accent6: "DBEAFE", hlink: "1D4ED8", folHlink: "6250D6" } };
const HEX = { blue: "1D4ED8", a: "2A78D6", b: "EB6834", c: "1BAF7A", grid: "E6EAF0", muted: "5B6577", ink: "0F1B2D" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.33 x 7.5 in
pres.title = "DataWorth KZ"; pres.author = "[Аты-жөні]";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({ title: "TITLE_DARK", background: { color: C.text2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.3, fontSize: 54, bold: true, color: C.background1, align: "left", valign: "bottom", margin: 0 }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.75, w: 11.0, h: 1.4, fontSize: 20, color: C.accent6, align: "left", valign: "top", margin: 0 }, text: "" } }] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: C.background1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 0.8, fontSize: 32, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
            { text: { text: "DataWorth KZ · Finance Intelligence 2026", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } }],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5, align: "right" } });

let nObj = 0; const nm = (p) => `${p}_${++nObj}`;
const shadow = () => ({ type: "outer", color: "0F1B2D", opacity: 0.08, blur: 8, offset: 2, angle: 90 });
function card(s, x, y, w, h, fill) { s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill || C.background2 }, line: { color: C.background2, width: 0.5 }, objectName: nm("card") }); }
function stat(s, x, y, w, big, label, col) {
  s.addText(big, { x, y, w, h: 0.75, fontSize: 40, bold: true, color: col || C.accent1, margin: 0, isTextBox: true, objectName: nm("stat") });
  s.addText(label, { x, y: y + 0.78, w, h: 0.75, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: nm("statlbl") }); }
function txt(s, t, o) { s.addText(t, Object.assign({ fontSize: 16, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: nm("txt") }, o)); }
function dot(s, x, y, label, col) { s.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color: col || C.accent1 }, line: { color: col || C.accent1 }, objectName: nm("dot") });
  s.addText(label, { x, y, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: nm("dotlbl") }); }
const chartFont = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mn-lt" };

const NOTES = require("./notes.json");

// 1 ------------------------------------------------------------------ TITLE
pres.addSection({ title: "Кіріспе" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Кіріспе" });
s.addText("DataWorth KZ", { placeholder: "title" });
s.addText("Open Banking үшін деректерді минимизациялауды экономикалық тұрғыдан бағалайтын әдістемелік прототип", { placeholder: "body" });
txt(s, "[Аты-жөні] · «Қаржы», 4-курс · Ғылыми жетекші: [Аты-жөні]\nNarxoz University · Finance Intelligence 2026", { x: 0.8, y: 5.9, w: 11, h: 0.8, fontSize: 14, color: C.accent6 });
s.addNotes(NOTES[0]);

// 2 ------------------------------------------------------------------ PROBLEM
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Кіріспе" });
s.addText("Банкке қанша дерек жеткілікті?", { placeholder: "title" });
txt(s, "Open Banking банктерге клиенттің келісімімен көбірек деректер береді. Бірақ әрбір дерек тобы шығынды, құқықтық жүктемені және құпиялық тәуекелін арттырады.", { x: 0.6, y: 1.35, w: 12.1, h: 0.8, fontSize: 18, color: C.accent5 });
const st2 = [["26,7 трлн ₸", "жеке тұлғаларға кредиттер, оның 17,7 трлн ₸ — тұтынушылық (01.10.2026, ҚНРДА)"], ["≈ 1,6 млн", "адамның қарызы 90 күннен астам мерзімі өткен (ҚНРДА, 2025)"], ["8,95 млн", "қарыз алушы — халықтың ≈ 44%-ы; 39,4 млн кредит (01.01.2026)"]];
st2.forEach(([b, l], i) => { const x = 0.6 + i * 4.1; card(s, x, 2.45, 3.8, 2.2); stat(s, x + 0.3, 2.7, 3.3, b, l); });
card(s, 0.6, 4.95, 12.1, 1.75, "DBEAFE");
txt(s, [{ text: "Зерттеу сұрағы: ", options: { bold: true, color: C.accent1 } }, { text: "банк кредиттік шешімдердің экономикалық тиімділігін сақтай отырып, пайдаланылатын клиенттік деректер көлемін қаншалықты азайта алады?" }],
  { x: 0.95, y: 5.25, w: 11.4, h: 1.2, fontSize: 20, valign: "middle" });
s.addNotes(NOTES[1]);

// 3 ------------------------------------------------------------------ KZ MARKET
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Кіріспе" });
s.addText("Қазақстан нарығы: өсу және проблемалық қарыздар", { placeholder: "title" });
s.addImage({ path: FIG + "kz_market.png", x: 0.6, y: 1.35, w: 8.3, h: 2.92, objectName: "kz_market", altText: "Бөлшек портфель және NPL90+ динамикасы" });
card(s, 9.2, 1.35, 3.5, 1.45, "DBEAFE"); stat(s, 9.45, 1.45, 3.1, "×2,1", "жеке тұлғалардың NPL90+ сомасы: 575 млрд → 1,2 трлн ₸ (01.2024 → 08.2026)");
card(s, 9.2, 2.95, 3.5, 1.35); stat(s, 9.45, 3.05, 3.1, "51 мың+", "банкрот деп танылды, 188 млрд ₸ есептен шығарылды (2025)", C.accent2);
card(s, 0.6, 4.55, 12.1, 2.2);
txt(s, "Реттеуші жауабы", { x: 0.95, y: 4.7, w: 5, h: 0.4, fontSize: 18, bold: true });
txt(s, [{ text: "01.07.2024 — 90+ кешіккенге жаңа тұтынушылық кредит жоқ", options: { bullet: true, breakLine: true } },
        { text: "24.11.2025 — банкте 30+ күн кешіксе кепілсіз кредит жоқ", options: { bullet: true, breakLine: true } },
        { text: "Борыш жүктемесі шегі 0,5 → 0,25 (90+ тарихы барларға)", options: { bullet: true } }], { x: 0.95, y: 5.15, w: 5.7, h: 1.5, fontSize: 14, paraSpaceAfter: 4 });
txt(s, [{ text: "01.04.2026 — бөлшек кредитке 2% контрциклдік буфер", options: { bullet: true, breakLine: true } },
        { text: "Коллекторларға сатуға мораторий 01.05.2027-ге дейін", options: { bullet: true, breakLine: true } },
        { text: "Open Banking: 2023 пилот, 2026 жаңа банк заңы", options: { bullet: true } }], { x: 6.85, y: 5.15, w: 5.6, h: 1.5, fontSize: 14, paraSpaceAfter: 4 });
s.addNotes(NOTES[2]);

// 4 ------------------------------------------------------------------ HYPOTHESIS
pres.addSection({ title: "Әдіснама" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Әдіснама" });
s.addText("Ғылыми гипотеза және авторлық модель", { placeholder: "title" });
card(s, 0.6, 1.5, 12.1, 1.35, "0B1F3A");
txt(s, "V(S) = Π(S) − Π(S₀) − C(S)", { x: 0.95, y: 1.62, w: 6.5, h: 0.7, fontSize: 32, bold: true, color: C.background1, fontFace: "Cambria Math" });
txt(s, "Деректер жиынтығының таза құны = қосымша модельдік пайда − деректер шығыны − құпиялықтың шартты бағасы", { x: 0.95, y: 2.3, w: 11.4, h: 0.45, fontSize: 15, color: C.accent6 });
const H = [["H1", "Non-inferiority: 6 белгілі Model B пайдасы 19 белгілі Model C-дан δ-дан артық төмен емес", C.accent1], ["H2", "Соңғы айлардың төлем мен шот деректері пайданы маңызды арттырады", C.accent2], ["H3", "Деректердің құны алгоритм мен кодтауға тәуелді", C.accent3], ["H4", "Мөлшерлеме, LGD және деректер шығыны өзгергенде тиімді жиынтық пен модель өзгереді", C.accent4]];
H.forEach(([h, t, col], i) => { const x = 0.6 + i * 3.06; card(s, x, 3.15, 2.86, 2.6); dot(s, x + 0.25, 3.4, h, col); txt(s, t, { x: x + 0.25, y: 4.05, w: 2.4, h: 1.6, fontSize: 15 }); });
txt(s, "Зерттеу олқылығы: әдебиет жаңа деректі қосудың пайдасын бағалайды; біз керісінше — қай деректен банк шығынсыз бас тарта алатынын есептейміз.", { x: 0.6, y: 6.0, w: 12.1, h: 0.6, fontSize: 14, color: C.accent5, italic: true });
s.addNotes(NOTES[3]);

// 5 ------------------------------------------------------------------ DATA, METHOD, HYBRID
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Әдіснама" });
s.addText("Деректер және әдіснама", { placeholder: "title" });
const steps = [["Деректер", "UCI, n = 30 000\nдефолт 22,1%\n70 / 15 / 15"], ["Ақпарат топтары", "S₀ + G1…G6\nA (2) · B (6) · C (19)\n64 комбинация"],
  ["PD модельдері", "Logistic Regression\nRandom Forest\nGradient Boosting"], ["Қаржы модулі", "EAD · LGD · маржа\nшешім: PD < t\nΠ(S), C(S)"], ["DVF", "V(S), фронтир\nоңтайлы жиынтық\nKZ сценарийлері"]];
steps.forEach(([h, b], i) => { const x = 0.6 + i * 2.5; card(s, x, 1.4, 2.2, 2.75, i == 4 ? "DBEAFE" : undefined); dot(s, x + 0.25, 1.6, String(i + 1), i == 4 ? C.accent2 : C.accent1);
  txt(s, h, { x: x + 0.25, y: 2.22, w: 1.85, h: 0.45, fontSize: 16, bold: true }); txt(s, b, { x: x + 0.25, y: 2.7, w: 1.85, h: 1.35, fontSize: 13, color: C.accent5, paraSpaceAfter: 2 });
  if (i < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.22, y: 2.6, w: 0.26, h: 0.3, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: nm("arrow") }); });
card(s, 0.6, 4.4, 5.95, 2.4); card(s, 6.75, 4.4, 5.95, 2.4, "DBEAFE");
txt(s, "PD модельдерін оқыту: ашық клиенттік жиын", { x: 0.9, y: 4.55, w: 5.4, h: 0.4, fontSize: 17, bold: true });
txt(s, [{ text: "UCI: 30 000 клиент, 6 айлық төлем тарихы", options: { bullet: true, breakLine: true } }, { text: "A (2), B (6), C (19) белгі; 64 комбинация", options: { bullet: true, breakLine: true } },
        { text: "70/15/15; ROC-AUC, Brier, bootstrap CI", options: { bullet: true } }], { x: 0.9, y: 5.0, w: 5.4, h: 1.6, fontSize: 14, paraSpaceAfter: 4 });
txt(s, "Қаржы параметрлері: ҚНРДА, ҰБ, бюро (2026)", { x: 7.05, y: 4.55, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: C.accent1 });
txt(s, [{ text: "Маржа: 22,5% − 14,7% = 7,8% (жылдық)", options: { bullet: true, breakLine: true } }, { text: "Теңгеге масштаб: Ē ≈ 698 мың ₸", options: { bullet: true, breakLine: true } },
        { text: "NPL90+ — тек контекст, PD емес; LGD — болжам", options: { bullet: true } }], { x: 7.05, y: 5.0, w: 5.4, h: 1.6, fontSize: 14, paraSpaceAfter: 4 });
s.addNotes(NOTES[4]);

// 7 ------------------------------------------------------------------ MODEL RESULTS
pres.addSection({ title: "Нәтижелер" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Нәтижелер" });
s.addText("Model A/B/C: дәлдік қай жерде өседі?", { placeholder: "title" });
const algos = ["Logistic Regression", "Random Forest", "Gradient Boosting"];
s.addChart(pres.charts.BAR, [
  { name: "Model A (2)", labels: algos, values: [0.708, 0.732, 0.732] },
  { name: "Model B (6)", labels: algos, values: [0.711, 0.770, 0.771] },
  { name: "Model C (19)", labels: algos, values: [0.711, 0.781, 0.777] }],
  Object.assign({ x: 0.6, y: 1.4, w: 7.6, h: 5.3, barDir: "col", barGapWidthPct: 60, chartColors: [HEX.a, HEX.b, HEX.c],
    valAxisMinVal: 0.65, valAxisMaxVal: 0.80, valAxisMajorUnit: 0.05, valAxisLabelFormatCode: "0.00", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", dataLabelFontSize: 10,
    dataLabelColor: HEX.ink, catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted, catAxisLabelFontSize: 13, valAxisLabelFontSize: 11, valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 13, showTitle: true, title: "ROC-AUC (test, n = 4 500)", titleFontSize: 14, titleColor: HEX.ink, objectName: "auc_chart" }, chartFont));
card(s, 8.6, 1.4, 4.1, 2.45, "DBEAFE"); stat(s, 8.9, 1.6, 3.6, "+0,040", "ΔAUC: A → B (Gradient Boosting)\n95% CI: 0,028 … 0,051");
card(s, 8.6, 4.15, 4.1, 2.55); stat(s, 8.9, 4.35, 3.6, "+0,006", "ΔAUC: B → C, 95% CI: −0,001 … 0,013\n13 қосымша белгінің үлесі шағын", C.accent5);
s.addNotes(NOTES[5]);

// 7 ------------------------------------------------------------------ KZ ECONOMICS
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Нәтижелер" });
s.addText("Экономикалық нәтиже теңгемен", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Model A (2)", labels: ["1 — базалық", "2 — жоғары тәуекел"], values: [-4300, -4561] },
  { name: "Model B (6)", labels: ["1 — базалық", "2 — жоғары тәуекел"], values: [7718, 2311] },
  { name: "Model C (19)", labels: ["1 — базалық", "2 — жоғары тәуекел"], values: [6262, 2700] }],
  Object.assign({ x: 0.6, y: 1.4, w: 6.9, h: 5.0, barDir: "col", barGapWidthPct: 60, chartColors: [HEX.a, HEX.b, HEX.c], valAxisMinVal: -6000, valAxisMaxVal: 9000, valAxisMajorUnit: 3000,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "#,##0", dataLabelFontSize: 11, dataLabelColor: HEX.ink, valAxisLabelFormatCode: "#,##0", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted,
    catAxisLabelFontSize: 13, valAxisLabelFontSize: 11, valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 12, showTitle: true,
    title: "Π, ₸ / клиент (Gradient Boosting, тест)", titleFontSize: 14, titleColor: HEX.ink, objectName: "kz_chart" }, chartFont));
card(s, 7.8, 1.4, 4.9, 1.55, "DBEAFE"); stat(s, 7.95 + 0.15, 1.5, 4.4, "+12 019 ₸", "B − A, базалық; 95% CI: 7 408 … 16 917 · H2 ✓");
card(s, 7.8, 3.1, 4.9, 1.55); stat(s, 8.1, 3.2, 4.4, "U95 = 7,1%", "C − B (GB), Π(B)-ға шаққанда; RF — 20,7% · H1 ~", C.accent5);
card(s, 7.8, 4.8, 4.9, 1.6); stat(s, 8.1, 4.9, 4.4, "98%", "жоғары тәуекелде U95(C − B)/Π(B); ең жақсы RF + B · H4 ~", C.accent2);
txt(s, "m = 22,5% − 14,7% = 7,8% (ҚНРДА, шілде 2026); LGD — сценарий; Ē ≈ 698 мың ₸ (бюро). Модельдік бағалау, банктің нақты пайдасы емес.", { x: 0.6, y: 6.5, w: 12.1, h: 0.4, fontSize: 12, color: C.accent5, italic: true });
s.addNotes(NOTES[6]);

// 8 ------------------------------------------------------------------ DVF KZ
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Нәтижелер" });
s.addText("Data Value Frontier: 6 өріс жеткілікті", { placeholder: "title" });
const fx = Array.from({ length: 18 }, (_, i) => String(i + 2));
const fv = [0, 3443, 7964, 7964, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877, 10877];
s.addChart(pres.charts.LINE, [{ name: "Фронтир", labels: fx, values: fv }], Object.assign({ x: 0.6, y: 1.4, w: 8.2, h: 5.3, chartColors: [HEX.blue], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 7,
  valAxisMinVal: 0, valAxisMaxVal: 12000, valAxisMajorUnit: 3000, valAxisLabelFormatCode: "#,##0", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" }, showLegend: false, showTitle: true, title: "V(S*), ₸ / клиент (тест) · өрістер бюджеті бойынша · базалық сценарий", titleFontSize: 14, titleColor: HEX.ink,
  showCatAxisTitle: true, catAxisTitle: "Өрістер саны (құпиялық жүктемесі)", catAxisTitleFontSize: 12, catAxisTitleColor: HEX.muted, objectName: "frontier_chart" }, chartFont));
card(s, 9.2, 1.4, 3.5, 1.65, "DBEAFE"); stat(s, 9.45, 1.55, 3.1, "10 877 ₸", "6 өрістің таза құны; 19 белгімен салыстырғанда −68% өріс");
card(s, 9.2, 3.25, 3.5, 1.65); stat(s, 9.45, 3.4, 3.1, "≈ 630 ₸", "бір топтың құны клиент басына осыдан асса, жиынтық кішірейеді", C.accent2);
card(s, 9.2, 5.1, 3.5, 1.6); stat(s, 9.45, 5.25, 3.1, "≈ 650 ₸", "бір өрістің құпиялық бағасының ауысу шегі (λ* ≈ 9,3 б.п.)", C.accent3);
s.addNotes(NOTES[7]);

// 9 ------------------------------------------------------------------ SENSITIVITY
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Нәтижелер" });
s.addText("Мөлшерлеме мен LGD өзгерсе не болады?", { placeholder: "title" });
s.addImage({ path: FIG + "kz_sensitivity.png", x: 0.6, y: 1.4, w: 12.1, h: 3.8, objectName: "kz_sens", altText: "Сезімталдық жылу картасы" });
card(s, 0.6, 5.4, 5.9, 1.35, "DBEAFE"); stat(s, 0.9, 5.45, 5.4, "15 / 15", "комбинацияда B − A оң: 4 390 … 15 010 ₸ / клиент");
card(s, 6.8, 5.4, 5.9, 1.35); stat(s, 7.1, 5.45, 5.4, "3 / 15", "комбинацияда ғана C − B оң, ең көбі +304 ₸", C.accent2);
s.addNotes(NOTES[8]);

// 10 ----------------------------------------------------------------- DEMO
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Нәтижелер" });
s.addText("Web App Live Demo", { placeholder: "title" });
s.addImage({ path: FIG + "shot_kz.png", x: 0.6, y: 1.35, w: 6.4, h: 4.89, objectName: "shot_kz", altText: "Қазақстан сценарийлері бөлімінің скриншоты", shadow: shadow() });
s.addImage({ path: FIG + "shot_dvf_c.png", x: 7.3, y: 1.35, w: 3.0, h: 2.71, objectName: "shot_dvf", altText: "DVF бөлімінің скриншоты", shadow: shadow() });
txt(s, "Демо сценарийі", { x: 10.5, y: 1.35, w: 2.3, h: 0.45, fontSize: 18, bold: true });
txt(s, [{ text: "DVF: деректер құны 0 → 20 б.п.", options: { bullet: { type: "number" }, breakLine: true } }, { text: "Оңтайлы жиынтық 6 → 3 өріс", options: { bullet: { type: "number" }, breakLine: true } },
        { text: "KZ: 1 → 2 → 3 сценарий", options: { bullet: { type: "number" }, breakLine: true } }, { text: "Өз мөлшерлемелерін енгізу", options: { bullet: { type: "number" } } }],
  { x: 10.5, y: 1.9, w: 2.3, h: 2.6, fontSize: 13, paraSpaceAfter: 8 });
card(s, 7.3, 4.5, 5.4, 1.74, "DBEAFE");
txt(s, "7 бөлім · нақты оқытылған модельдер · параметр өзгерсе 64 жиынтық қайта есептеледі · 25 автотест · банк жүйесіне қосылмаған", { x: 7.6, y: 4.65, w: 4.8, h: 1.44, fontSize: 14, valign: "middle" });
txt(s, "Іске қосу: streamlit run app.py", { x: 0.6, y: 6.45, w: 5.6, h: 0.35, fontSize: 12, color: C.accent5 });
s.addNotes(NOTES[9]);

// 11 ----------------------------------------------------------------- NOVELTY & LIMITS
pres.addSection({ title: "Қорытынды" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Қорытынды" });
s.addText("Ғылыми жаңалық және шектеулер", { placeholder: "title" });
card(s, 0.6, 1.5, 6.0, 5.2, "DBEAFE"); card(s, 6.9, 1.5, 5.8, 5.2);
txt(s, "Жаңалық", { x: 0.95, y: 1.7, w: 5.3, h: 0.5, fontSize: 22, bold: true, color: C.accent1 });
txt(s, [{ text: "Негіз: пайдаға негізделген скоринг, құн-сезімтал шешім, Data Shapley", options: { bullet: true, breakLine: true } },
  { text: "Авторлық үлес: оларды деректерді минимизациялауға біріктіру — V(S) = Π(S) − Π(S₀) − C(S)", options: { bullet: true, breakLine: true } },
  { text: "Кіші жиынтықтың «кем еместігін» non-inferiority арқылы тексеру", options: { bullet: true, breakLine: true } },
  { text: "Құпиялық өлшенбегенде — ауысу шегі λ*", options: { bullet: true, breakLine: true } },
  { text: "Барлық экономика Қазақстанның 2026 ж. мөлшерлемелерінде, теңгемен", options: { bullet: true, breakLine: true } },
  { text: "64 комбинация — әдіс, жаңалық емес", options: { bullet: true } }], { x: 0.95, y: 2.35, w: 5.3, h: 4.1, fontSize: 14, paraSpaceAfter: 6 });
txt(s, "Шектеулер", { x: 7.25, y: 1.7, w: 5.1, h: 0.5, fontSize: 22, bold: true, color: C.accent2 });
txt(s, [{ text: "PD модельдері ашық клиенттік жиында оқытылған (UCI)", options: { bullet: true, breakLine: true } },
  { text: "Мақсат — 1 айлық кешігу; айлық маржада нәтиже орнықсыз", options: { bullet: true, breakLine: true } },
  { text: "₸ — модельдік бағалау, банктің нақты пайдасы емес", options: { bullet: true, breakLine: true } },
  { text: "H1 тек GB үшін және δ ≥ 7,1% болғанда", options: { bullet: true, breakLine: true } },
  { text: "LGD, c, λ — болжам; маржа — жалпы айырма", options: { bullet: true, breakLine: true } },
  { text: "Уақыт бойынша тексеру жоқ", options: { bullet: true } }], { x: 7.25, y: 2.35, w: 5.1, h: 4.1, fontSize: 14, paraSpaceAfter: 6 });
s.addNotes(NOTES[10]);

// 12 ----------------------------------------------------------------- CONCLUSION
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Қорытынды" });
s.addText("Қорытынды және ұсыныстар", { placeholder: "title" });
s.addText("Деректердің құны көлемінде емес, шешімге қосатын үлесінде — бірақ бұл қорытынды болжамдарға тәуелді", { placeholder: "body" });
[["H2 ✓", "A → B: +12 019 ₸ / клиент"], ["H1 ~", "GB ✓ (δ ≥ 7,1%), RF ✗"], ["H3 ✓", "құн алгоритмге тәуелді"], ["H4 ~", "тәуекелде B ≈ C; 630 ₸-дан қымбат топ тиімсіз"]].forEach(([b, l], i) => {
  const x = 0.8 + i * 3.0; s.addText(b, { x, y: 4.75, w: 2.8, h: 0.6, fontSize: 28, bold: true, color: C.background1, margin: 0, isTextBox: true, objectName: nm("h") });
  s.addText(l, { x, y: 5.35, w: 2.8, h: 0.7, fontSize: 14, color: C.accent6, margin: 0, isTextBox: true, objectName: nm("hl") }); });
txt(s, "Ұсыныстар: түйіршікті Open Banking келісімі · жаңа деректер тобының шекті құнын есептеу · банктердің өз деректерімен, 12 айлық дефолтпен қайталау", { x: 0.8, y: 6.35, w: 11.8, h: 0.6, fontSize: 13, color: C.accent6 });
s.addNotes(NOTES[11]);

(async () => { await pres.writeFile({ fileName: "DataWorth_KZ_Presentation.pptx" }); await applyTheme("DataWorth_KZ_Presentation.pptx", THEME); console.log("ok"); })();
