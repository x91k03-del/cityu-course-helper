import os,subprocess,json,re
from pathlib import Path
import project_runtime
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'GE_SEMA/Phase2_Report09'
for key,folder in [('TEXMFVAR','texlive-var'),('TEXMFCONFIG','texlive-config')]:
    p=ROOT/'.cache'/folder;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
for i in (1,2):
    result=subprocess.run([r'D:\texlive\2025\bin\windows\pdflatex.exe','-halt-on-error','-interaction=nonstopmode','Phase2_Report09.tex'],cwd=OUT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/f'compile-pass{i}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:print(result.stdout[-4500:]);raise SystemExit(result.returncode)
from pypdf import PdfReader
reader=PdfReader(OUT/'Phase2_Report09.pdf')
log=(OUT/'Phase2_Report09.log').read_text(encoding='utf-8',errors='replace')
warnings=[x for x in log.splitlines() if 'Overfull' in x or 'undefined' in x or 'Warning' in x]
print(json.dumps({'pages':len(reader.pages),'text_lengths':[len(p.extract_text() or '') for p in reader.pages],'warnings':warnings},indent=2))
preview=OUT/'previews';preview.mkdir(exist_ok=True)
subprocess.run(['pdftoppm','-scale-to','1300','-png',str(OUT/'Phase2_Report09.pdf'),str(preview/'page')],check=True,capture_output=True)
