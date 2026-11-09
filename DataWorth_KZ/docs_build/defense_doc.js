const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak, Footer, PageNumber, Table, TableRow, TableCell, WidthType, ShadingType, LevelFormat } = require('docx');
const D = JSON.parse(fs.readFileSync('defense.json')); const F = "Times New Roman", SZ = 28;
const P = (runs, o = {}) => new Paragraph({ alignment: o.align || AlignmentType.JUSTIFIED, indent: o.indent === false ? undefined : { firstLine: 709 }, spacing: { after: o.after ?? 80 }, keepNext: o.keepNext, children: runs });
const R = (t, o = {}) => new TextRun(Object.assign({ text: t, font: F, size: SZ }, o));
const H = (t, lvl = 1) => new Paragraph({ heading: lvl == 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, alignment: lvl == 1 ? AlignmentType.CENTER : AlignmentType.LEFT, children: [R(t, { bold: true })] });
const ch = [];
ch.push(H("DataWorth KZ: қорғауға арналған материалдар"));
ch.push(P([R("Материалдар ғылыми жұмыстың соңғы нұсқасына сәйкес келеді.", { italics: true })], { indent: false }));
D.texts.forEach(([t, ps], i) => { ch.push(H(`${i + 1}. ${t}`, 2)); ps.forEach(p => ch.push(P([R(p)]))); });
ch.push(new Paragraph({ children: [new PageBreak()] }));
ch.push(H("6. Комиссия қоюы мүмкін 15 күрделі сұрақ және жауаптар", 2));
D.qa.forEach(([q, a], i) => { ch.push(P([R(`${i + 1}. ${q}`, { bold: true })], { indent: false, keepNext: true, after: 40 })); ch.push(P([R(a)], { after: 140 })); });
ch.push(new Paragraph({ children: [new PageBreak()] }));
ch.push(H("7. Қорғау сөзі (5–7 минут)", 2));
const total = D.script.reduce((a, [, , s]) => a + s.split(/\s+/).length, 0);
ch.push(P([R(`Әр бөлім презентацияның бір слайдына сәйкес келеді. Мәтін көлемі: ${total} сөз — қалыпты қарқынмен (минутына 110–120 сөз) және демонстрациямен шамамен 6–7 минут.`, { italics: true })], { indent: false }));
for (const [t, tm, s] of D.script) { ch.push(P([R(`Слайд ${t}`, { bold: true }), R(`   [${tm}]`, { color: "5B6577" })], { indent: false, keepNext: true, after: 40 })); ch.push(P([R(s)])); }
ch.push(H("Қосымша: есте сақтайтын негізгі сандар", 2));
const w = [3000, 6638];
ch.push(new Table({ width: { size: 9638, type: WidthType.DXA }, columnWidths: w, rows: D.nums.map(([a, b]) => new TableRow({ cantSplit: true, children: [
  new TableCell({ width: { size: w[0], type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: "DCE6F5", color: "auto" }, margins: { top: 40, bottom: 40, left: 80, right: 80 }, children: [new Paragraph({ children: [R(a, { bold: true, size: 24 })] })] }),
  new TableCell({ width: { size: w[1], type: WidthType.DXA }, margins: { top: 40, bottom: 40, left: 80, right: 80 }, children: [new Paragraph({ children: [R(b, { size: 24 })] })] })] })) }));
ch.push(H("Қосымша: демонстрацияға кеңестер", 2));
D.demo.forEach(t => ch.push(new Paragraph({ numbering: { reference: "b", level: 0 }, alignment: AlignmentType.JUSTIFIED, children: [R(t)] })));
const doc = new Document({ styles: { default: { document: { run: { font: F, size: SZ } } }, paragraphStyles: [
  { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F, size: 30, bold: true }, paragraph: { spacing: { before: 0, after: 200 }, keepNext: true, outlineLevel: 0 } },
  { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F, size: SZ, bold: true }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 993, hanging: 284 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { left: 1701, top: 1134, right: 567, bottom: 1417 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: F, size: 24 })] })] }) }, children: ch }] });
Packer.toBuffer(doc).then(b => { fs.writeFileSync('DataWorth_KZ_Defense_Script.docx', b); console.log('ok'); });
