import re
p='paper.txt'; s=open(p,encoding='utf-8').read()
def ren(kind, word):
    global s
    caps=[l for l in s.split('\n') if l.startswith(kind)]
    old=[re.search(r'\| *(K?F?\d+)-'+word, l).group(1) for l in caps]
    mp={o:str(i+1) for i,o in enumerate(old)}
    s=re.sub(r'\b(K?F?\d+)-'+word, lambda m: (mp.get(m.group(1),m.group(1)))+'-'+word, s)
    return mp
print(ren('TAB:','кесте')); print(ren('FIG:','сурет'))
open(p,'w',encoding='utf-8').write(s)
