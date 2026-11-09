import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from guide_data import ENTRIES
D='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('S',D+'DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('SB',D+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('SI',D+'DejaVuSans-Oblique.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('S',normal='S',bold='SB',italic='SI',boldItalic='SB')
ACC=colors.HexColor('#2F6DB5');SOFT=colors.HexColor('#EEF4FB');GR=colors.HexColor('#555555')
b=ParagraphStyle('b',fontName='S',fontSize=9.6,leading=13.6,spaceAfter=3)
h1=ParagraphStyle('h1',fontName='SB',fontSize=17,leading=22,textColor=ACC,spaceAfter=8)
h2=ParagraphStyle('h2',fontName='SB',fontSize=11.5,leading=15,textColor=ACC,spaceBefore=4,spaceAfter=3)
lab=ParagraphStyle('lab',fontName='SB',fontSize=9.2,leading=12.5,textColor=GR,spaceBefore=4)
ref=ParagraphStyle('ref',fontName='SI',fontSize=9,leading=12.5,textColor=colors.HexColor('#333333'))
sm=ParagraphStyle('sm',fontName='S',fontSize=8.6,leading=11.5)
def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
refs=[l[5:] for l in open('paper.txt').read().split('\n') if l.startswith('REF:')]
used={}
for l in open('paper.txt').read().split('\n'):
    pass
st=[]
st.append(Paragraph('DataWorth KZ: пайдаланылған әдебиеттер бойынша оқу нұсқаулығы',h1))
st.append(Paragraph('Бұл нұсқаулық ғылыми жұмыстағы 34 дереккөздің әрқайсысы туралы мыналарды береді: дереккөз не туралы, оның қай бөлігі пайдаланылды, біздің жұмыстың қай жерінде қолданылды және қорғауда қандай сұрақ қойылуы мүмкін.',b))
st.append(Paragraph('<b>Қалай пайдалану керек.</b> Алдымен «Міндетті» деп белгіленген дереккөздерді оқыңыз (аннотация, кіріспе және қорытынды бөлімдері жеткілікті). Әр жазбадағы «Қай бөлігі қолданылды» бөлімінде көрсетілген идеяны өз сөзіңізбен түсіндіре алатындай болыңыз. Ашық нұсқасы бар мақалалар сілтемеде белгіленген.',b))
st.append(Paragraph('<b>Маңызды ескерту.</b> Мақалалардың толық мәтіндері авторлық құқықпен қорғалған, сондықтан бұл жерде олардың мазмұны тек қысқаша өз сөзімізбен берілген. Сипаттамалар мақалалардың аннотацияларына, ресми беттеріне және ғылыми әдебиеттегі белгілі мазмұнына негізделген. Ақылы мақалалардың барлық беттерін біз бұл жұмыс барысында оқыған жоқпыз. Сондықтан қорғауға дейін ең болмағанда «Міндетті» дереккөздердің аннотациясы мен қорытындысын түпнұсқадан өзіңіз оқыңыз. Сандарды (49 ел, 41 алгоритм, 128 клиент, NPL90+ 4,7%, мөлшерлемелер 22,5% және 14,7% т.б.) біз дереккөздерден тексердік.',b))
st.append(Spacer(1,6))
cnt={}
for e in ENTRIES: cnt[e[1]]=cnt.get(e[1],0)+1
rows=[[Paragraph('<b>№</b>',sm),Paragraph('<b>Дереккөз</b>',sm),Paragraph('<b>Басымдық</b>',sm),Paragraph('<b>Жұмыста</b>',sm)]]
for e in ENTRIES:
    r=refs[e[0]-1]; short=esc(r.split('//')[0].split(' – ')[0])
    rows.append([Paragraph(str(e[0]),sm),Paragraph(short,sm),Paragraph(e[1],sm),Paragraph(esc(e[5].split('. ')[0].rstrip('.')),sm)])
t=Table(rows,colWidths=[1.0*cm,8.6*cm,2.6*cm,4.8*cm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),SOFT),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#C9D6E8')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
st.append(Paragraph('Жалпы шолу',h2)); st.append(t)
st.append(Paragraph(f"Барлығы 34 дереккөз: міндетті — {cnt.get('Міндетті',0)}, жақсы білу керек — {cnt.get('Жақсы білу керек',0)}, таныс болу жеткілікті — {cnt.get('Таныс болу жеткілікті',0)}.",b))
st.append(PageBreak())
for (n,pr,acc,about,part,ours,q,a) in ENTRIES:
    blk=[Paragraph(f'[{n}] <font size="9" color="#555555">· {pr}</font>',h2),
         Paragraph(esc(refs[n-1]),ref),
         Paragraph('Қайдан табуға болады',lab),Paragraph(esc(acc),b),
         Paragraph('Дереккөз не туралы',lab),Paragraph(esc(about),b),
         Paragraph('Қай бөлігі қолданылды',lab),Paragraph(esc(part),b),
         Paragraph('Біздің жұмыста',lab),Paragraph(esc(ours),b)]
    qa=Table([[Paragraph('<b>Мүмкін сұрақ:</b> '+esc(q),b)],[Paragraph('<b>Жауап:</b> '+esc(a),b)]],colWidths=[17*cm])
    qa.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),SOFT),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    blk+= [Spacer(1,3),qa,Spacer(1,10)]
    st.append(KeepTogether(blk))
def foot(c,d):
    c.saveState();c.setFont('S',8);c.setFillColor(GR);c.drawRightString(A4[0]-2*cm,1.2*cm,f'DataWorth KZ · Әдебиеттер нұсқаулығы · {d.page}');c.restoreState()
doc=SimpleDocTemplate('../out/v2/DataWorth_KZ_Adebietter_Nusqaulyq.pdf',pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.8*cm,title='DataWorth KZ — әдебиеттер бойынша оқу нұсқаулығы')
doc.build(st,onFirstPage=foot,onLaterPages=foot)
