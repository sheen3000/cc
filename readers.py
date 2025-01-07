'''
Code that ingests/reads data from different sources
(but mostly PDFs)

Tools:

- PDF: pdfplumber (although pymupdf is faster)
'''

import re
from typing import Optional # Any, 
from collections.abc import Generator
from collections import defaultdict
from functools import partial
from dataclasses import dataclass
from pathlib import Path

from tqdm import tqdm
from loguru import logger
import pdfplumber
from sqlitedict import SqliteDict

# Table extraction
import pandas as pd
from py_markdown_table.markdown_table import markdown_table

from utils import normalize_text_for_embedding




@dataclass
class Para:
    page: int
    is_table: bool
    text: str
    position: Optional[int] = None # Order in which each para appears in the document
    vector: Optional[list[float]] = None
    raw_text: Optional[str] = None


class PDF:
    '''Extract text from PDF using pdfplumber'''

    def __init__(self, filename: Path, ):
        logger.info(f'Processing document "{filename}"')
        assert filename.is_file(), filename
        assert filename.suffix.lower() == '.pdf'
        self.filename = filename
        self.name = self.filename.stem # without folder or extension
        self.table_positions = defaultdict(list)


    def yield_paragraphs(self, detect_tables=False, inspect=False) -> Generator[Para, None, None]:
        # A PDF can have 1000+ pages
        # For performance, we will parse each page at a time and then yield the paragraphs
        # Note: if we pass "laparams= {}" we can retrieve more objects

        # If detect_tables=True, we will yield the corresponding text as tables instead of paras

        # Note that we can access tables as lists with either:
        # a) page.extract_tables(table_settings={})
        # b) tables = page.find_tables(table_settings={})
        #    tables[0].extract()
        # The second is slower if we only want the text but useful if we also want the bbox
        
        with pdfplumber.open(self.filename) as pdf:
            logger.info(f' - Reading text from PDF ({len(pdf.pages)} pages)')
            
            self.metadata = pdf.metadata.copy()
            self.num_pages = len(pdf.pages)
            self.num_paragraphs = 0
            self.num_tables = 0

            #for page in tqdm(pdf.pages):
            for page in pdf.pages:

                page_num = page.page_number

                # Steps:
                # 1) Identify tables so we can exclude text contained in them (that would otherwise be duplicated)
                # 2) Transform tables to text; store them
                # 4) Determine if we want to abort a page
                # 5) Yield all paras (unless we abort a para)
                # 6) Yield all tables

                # Experimental - Only read first 100? 50? pages
                if page_num > 50:
                    return

                converted_tables = []
                if detect_tables:
                    tables = page.find_tables(table_settings={})
                    if tables:
                        # Get the bounding boxes of the tables on the page.
                        # See: https://github.com/jsvine/pdfplumber/issues/242#issuecomment-1686505282
                        bboxes = [table.bbox for table in tables]
                        bbox_not_within_bboxes = partial(not_within_bboxes, bboxes=bboxes)

                        # Filter-out tables from page (so .extract_text() below won't include them)
                        page = page.filter(bbox_not_within_bboxes)

                        #logger.info(f'    - Identified {len(tables)} table on page {page_num})')
                        for table in tables:
                            table = table.extract() # x_tolerance=3, y_tolerance=3 -> defaults
                            # Convert table to markdown
                            table = [['' if c is None else c.replace('\n', ' ').strip() for c in row] for row in table]
                            df = pd.DataFrame(table)
                            empty_cols = [df[col].name for col in df if not df[col].any()]
                            df.drop(empty_cols, axis=1, inplace=True)
                            df.rename(columns = {x: "C"+str(x+1) for x in range(0,240)}, inplace = True)
                            data = df.to_dict(orient='records')

                            # markdown_table fails if data is empty (and there's no point in parsing it anyways)
                            if not data:
                                continue

                            try:
                                # Try to make markdown tables as close as possible to what OpenAI expects
                                md_table = markdown_table(data).set_params(row_sep='markdown', quote=False)
                                md = md_table.get_markdown()
                                md = md.split('\n')
                                md = [md[2], md[1]] + md[3:]
                                md = '\n'.join(md)
                            except:
                                # What if some assumptions (e.g. number of rows) are not met? Easy hack/fix
                                #md = markdown_table(data).get_body()
                                md = markdown_table(data).get_markdown()
                            
                            para = Para(page=page_num, is_table=True, text=md)
                            converted_tables.append(para)

                #print(page.objects.keys())
                # Default y_density is 13; but that sometimes splits paragraphs
                # Not fully sure how this algorithm works though...
                # https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/utils/text.py
                text = page.extract_text(layout=True, y_density=13.8)
                text = clean_text(text)
                raw_text = text if inspect else None
                paras = text2paragraphs(text)

                for para in paras:
                    if abort_para(para):
                        continue
                    self.num_paragraphs += 1
                    yield Para(page=page_num, is_table=False, text=para, raw_text=raw_text)

                for table in converted_tables:
                    self.num_tables += 1
                    yield table


def clean_text(text: str) -> str:
    text = text.replace(u'\u201f', '"')  # double high-reversed-9 quotation mark
    text = text.replace(u'\u201c', '"')  # left double quotation mark
    text = text.replace(u'\u201d', '"')  # right double quotation mark
    text = text.replace(u'’', "'")
    
    # PDF garbled text that we need to delete (else GPT stops due to repeated patterns)
    # 1) This is usually bar plots or other charts represented as text in older PDFs
    text = re.sub(r'(\(cid:\d+\)){2,}', "", text)  # Bullet symbol
    # 2) Bullet symbols
    text = re.sub(r'\s\(cid:\d+\) ', "- ", text)  # The number could be 1, 2, 130, 190, 216, etc.
    # 3) Sanity check
    #assert '(cid:' not in text, text

    return text


def text2paragraphs(text: str) -> list[str]:
    new_para: str
    paras: list[str] = []
    # add empty str at the end to finalize last paragraph
    lines = [fix_line(line) for line in text.split('\n')] + ['']
    parts: list[str] = []
    for line in lines:
        if not line and parts:
            new_para = ' '.join(parts)
            if '\uf0b7' in new_para:
                new_para = fix_bullet_list(new_para)
            paras.append(new_para)
            parts = []
        elif line:
            parts.append(line)

    # Remove page number at the end of the page
    if paras and paras[-1].isdigit():
        paras = paras[:-1]
    
    return paras


def fix_line(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.replace('”', '"').replace('“', '"')
    return text


def fix_bullet_list(text: str) -> str:
    items = text.split('\uf0b7')
    items = [item.strip() for item in items]
    items = ['- ' + item for item in items if item]
    return '\n'.join(items)


def abort_para(para: str) -> bool:

    # If somehow preprocessing turned the para into an empty string
    if not para:
        return True
    
    # Abort if the string represents numbers (commonly because its a row in a table)
    words = para.split()
    num_words = len(words)
    numerator = sum(word.replace('.', '').replace('%', '').isdigit() for word in words)
    fraction = numerator / len(words)
    #if fraction>0.5:
    #    print('?? PARA', para)
    #    print('?? fraction', fraction)
    #    print()
    if fraction > 0.6:
        return True

    # Abort table headers
    if para.upper().startswith('TABLE ') and len(para) < 80:
        return True

    # Abort very short paras
    if len(para) < 15:
        return True

    # Abort if normalized text is empty
    if not normalize_text_for_embedding(para):
        return True

    return False


def not_within_bboxes(obj, bboxes):
    """Check if the object is in any of the table's bbox."""
    # SOURCE: https://github.com/jsvine/pdfplumber/issues/242#issuecomment-1686505282

    def obj_in_bbox(_bbox):
        """Define objects in box.

        See https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/table.py#L404
        """
        v_mid = (obj["top"] + obj["bottom"]) / 2
        h_mid = (obj["x0"] + obj["x1"]) / 2
        x0, top, x1, bottom = _bbox
        return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)

    return not any(obj_in_bbox(__bbox) for __bbox in bboxes)


if __name__ == '__main__':
    pdf_path = Path('E:/WH/CCADB/2023Q4/WELLS FARGO & COMPANY')
    pdf_fn = pdf_path / 'Wells Fargo Active Cash Card-357807_10688200000089XBAAY.pdf'
    
    pdf = PDF(pdf_fn)
    prev_page = 0

    for para in pdf.yield_paragraphs(detect_tables=True):
        
        if para.page != prev_page:
            print(f' Page {para.page} '.center(100, '='))
            prev_page = para.page
            #print(para.raw_text)
            #print('X' * 100)
            #print()

            # View image (for debugging)
            if False:
                with pdfplumber.open(pdf.filename) as _pdf:
                    p = _pdf.pages[para.page-1]
                    im = p.to_image(resolution=150)
                    im.draw_rects(p.extract_words())
                    im.show()

        print(para.text)
        print()
