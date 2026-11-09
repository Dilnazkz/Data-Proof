import re, json
s=open('paper_kz.txt',encoding='utf-8').read()
body,refs=s.split('#REF ',1)
refdefs=dict(re.findall(r'^REF@(\w+): (.*)$',refs,flags=re.M))
order=[]
for m in re.finditer(r'\[(@[\w,@]+)\]',body):
    for k in m.group(1).replace('@','').split(','):
        if k not in refdefs: raise SystemExit('missing '+k)
        if k not in order: order.append(k)
unused=[k for k in refdefs if k not in order]
num={k:i+1 for i,k in enumerate(order)}
body=re.sub(r'\[(@[\w,@]+)\]',lambda m:'['+','.join(map(str,sorted(num[k] for k in m.group(1).replace('@','').split(','))))+']',body)
head=refs.split('\n',1)[0]
out=body+'#REF '+head+'\n\n'+'\n'.join('REF: '+refdefs[k] for k in order)+'\n'
open('paper.txt','w',encoding='utf-8').write(out)
json.dump(num,open('refmap.json','w'))
print(len(order),'refs; unused:',unused)
