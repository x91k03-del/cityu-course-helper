"""Read explicit course grades from student messages outside the model."""
import re

def explicit_grades(text):
    """Guard explicit grade statements independently of the neural extraction."""
    upper=text.upper();found={}
    grade=r'(A\+|A-|A|B\+|B-|B|C\+|C-|C|D|P|F|IP|W)(?![A-Z+\-])'
    for code in set(re.findall(r'\b[A-Z]{2,6}\d{4}[A-Z]?\b',upper)):
        match=re.search(r'\b'+code+r'\s*(?::|\(|WITH\s+(?:GRADE\s+)?|GRADE\s+(?:OF\s+)?)\s*'+grade,upper)
        if match:found[code]=match.group(1);continue
        for pattern,value in [(r'(?:FAILED|FAIL)\s+'+code,'F'),
                              (r'(?:WITHDREW FROM|WITHDRAWN FROM)\s+'+code,'W'),
                              (code+r'\s+(?:IS\s+)?(?:STILL\s+)?IN PROGRESS','IP'),
                              (code+r'\s*[:(]\s*GRADE\s+(?:NOT PROVIDED|UNKNOWN)','UNKNOWN')]:
            if re.search(pattern,upper):found[code]=value;break
    return found
