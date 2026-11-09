import subprocess, json, re
s=open('paper.txt').read().split('\n'); heads=[]
for l in s:
    if l.startswith('## '): heads.append((2,l[3:]))
    elif l.startswith('#'): heads.append((1,re.sub(r'^#(!|REF|ANN)?\s*','',l)))
n=int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo','DataWorth_KZ_Research.pdf'],capture_output=True,text=True).stdout).group(1))
pages=[subprocess.run(['pdftotext','-f',str(i),'-l',str(i),'DataWorth_KZ_Research.pdf','-'],capture_output=True,text=True).stdout for i in range(1,n+1)]
norm=lambda x: re.sub(r'\s+',' ',x).strip()
out=[]; start=2
for lvl,h in heads:
    key=norm(h)[:34]; pg=None
    for i in range(start,n):
        if key in norm(pages[i]): pg=i+1; start=i; break
    out.append({"lvl":lvl,"text":h,"page":pg})
old=json.load(open('toc.json')) if __import__('os').path.exists('toc.json') else None
json.dump(out,open('toc.json','w'),ensure_ascii=False)
print(n, [ (o['text'][:12],o['page']) for o in out]); print('same as before:', old==out)
