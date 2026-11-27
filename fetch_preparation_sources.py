"""Download publicly linked official syllabi; keep PDFs, page text and provenance."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'sources/preparation-v5'
CODES=['MA1300','MA1301','MA2503','MA2508','MA2509','MA2510','MA3511','MA3512','MA3514','MA3515','MA3517','MA3518','MA3525','MA3526','MA3521','MA3523','MA4523','MA4524','MA4525','MA4542','MA4545','MA4546','MA4535','MA4550','GE2134']
def main():
    OUT.mkdir(parents=True,exist_ok=True);manifest=[];session=requests.Session()
    for code in CODES:
        page=f'https://www.cityu.edu.hk/catalogue/ug/current/course/{code}.htm'
        record={'code':code,'catalogue_page':page,'fetched_at':datetime.now(timezone.utc).isoformat()}
        path=OUT/(code+'.pdf')
        try:
            if not path.exists():
                r=session.get(page,timeout=35)
                record['catalogue_status']=r.status_code
                links=[]
                if r.ok:
                    soup=BeautifulSoup(r.text,'html.parser')
                    links=[urljoin(r.url,a['href']) for a in soup.select('a[href]') if a['href'].lower().split('?')[0].endswith('/'+code.lower()+'.pdf')]
                # Official public PDF endpoint used by the catalogue downloader.
                url=links[-1] if links else f'https://www.cityu.edu.hk/ug/202627/course/{code}.pdf'
                record['pdf_link_method']='catalogue_link' if links else 'official_public_pdf_endpoint_catalogue_unavailable'
                time.sleep(1)
                r=session.get(url,timeout=40);r.raise_for_status()
                if not r.content.lstrip().startswith(b'%PDF'):raise ValueError('Not a PDF; access challenge is not course evidence')
                path.write_bytes(r.content);record['pdf_url']=r.url
            else:
                old=next((x for x in json.loads((OUT/'manifest.json').read_text()) if x['code']==code),{}) if (OUT/'manifest.json').exists() else {}
                record.update(old)
            pages=[p.extract_text() or '' for p in PdfReader(path).pages]
            if code not in '\n'.join(pages):raise ValueError('Course code mismatch')
            (OUT/(code+'.pages.json')).write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
            (OUT/(code+'.txt')).write_text('\n'.join(pages),encoding='utf-8')
            record.update(status='downloaded',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pages=len(pages),local_pdf=str(path))
        except Exception as e:record.update(status='unavailable',error=str(e))
        manifest.append(record);(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(code,record['status'],record.get('pdf_url',record.get('error')),flush=True)
        if record.get('status')=='unavailable' and 'access challenge' in record.get('error',''):
            print('Stopping: provide public PDFs locally rather than retrying the challenged site.',flush=True)
            break
if __name__=='__main__':main()
