'''
Script that processes credit card disclosure files
<FILL THIS>


TODO:

- Carefully weight costs of GPT4o and GPT3.5t
- Consider trimming at a max. number of pages (line 89 of readers.py currently sets that at 50 pages)
- ...
- ...

'''

from pathlib import Path
import pandas as pd
import click
import sys
from loguru import logger
from tqdm import tqdm
from readers import PDF, Para
from llm import LLM
import time
import itertools
import tiktoken

question = '''
You have been tasked to extract information from a bank a consumer credit card agreement. You will find the entire text of the agreement after the word "CONTEXT:" at the end of this message.

Follow these general instructions:

1. Please only answer the question using the provided context.
2. Provide your response using JSON fields. If a given item is not found, return an empty string.
3. If you fail to find an answer, just return an empty string.

Your objective is to extract information about the credit card agreement. Provide the solution as follows, where the list of purchased assets listed in the text will be contained in the field "assets":

{
    "bank_name": "...", # Name of the bank or financial institution
    "product_name": "...", # Name of the credit card product
    "card_network": "...", # Type of card (Visa, Mastercard, Amex, etc.)
    "gambling_prohibited": "...", # Does the agreement prohibit gambling or betting transactions? Respond "yes", "no", or "depends"
    "gambling_snippet": "..." # Please quote the specific section (if any) discussing gambling or betting transactions

}

Further, follow these instructions:

1. Please only answer the question using the provided context.
2. Note that the text is based on an OCRed scan, so it might contain typos typical of OCRed documents.
3. Exclude from the list of assets the stated purpose of the firm, often prefixed by the "Zweck:" label (or a similar label).
4. Hint: the list of assets is usually prefixed by a label such as Gegenwärtiger Besitz, Besitz, Besitzum, Besitzstand (and variations).
5. Provide your response using JSON items. If a given item is not found, return an empty string.

CONTEXT:

'''

   # "overdraft_fee": "..." # What is the overdraft fee?
    #"interest_rate": "...", # What is the APR for purchases?
   # "annual_fee": "...", # What (if any) is the annual fee?
# Import restricted bank sample 

df=pd.read_csv('../output/big_sample.tsv', sep='\t')

# Extract the 'name' column and convert it to a set
bank_sample = set(df['name'])

# Print the set
print(bank_sample)
print(len(bank_sample)) 

def process_period(period: str):

    # Parameters
    base_path = Path('C:/users/shawn/credit-cards-shawn/data/') # "Credit card Agreement database"

    pdf_path = base_path / period
    assert pdf_path.is_dir()

    questions_path = base_path /  f'questions' / period
    questions_path.mkdir(exist_ok=True, parents=True)

    cache_path = base_path /  f'llm-cache'
    cache_path.mkdir(exist_ok=True)
    cache_filename = cache_path / f'{period}.sqlite'
    llm = LLM(cache_filename=cache_filename)

    #output_fn = base_path / f'{period}-data.tsv'
    output_fn = Path('../output') / f'{period}-data.tsv'

    # Ignore already processed files
    if output_fn.exists():
        df = pd.read_csv(output_fn, sep='\t')
        done = df.to_dict(orient='records')
        done = {(d['bank_name'], d['filename']):d for d in done}
        #done = df[['bank_name', 'filename']].values.tolist()
        #done = set( (bank_name, filename) for bank_name, filename in done) # set of tuples
    else:
        done = None

    # Process all PDFs
    answers = []
    pdf_fns = pdf_path.glob('**/*.pdf')
    pdf_fns = list(pdf_fns)

    for pdf_fn in pdf_fns:
        bank_name = pdf_fn.parent.name
        filename = pdf_fn.stem
        # bank_sample is a set that I will create previously 
        if bank_name not in bank_sample:
            continue

        print(filename)
        time.sleep(6)



        # Avoid reading pdfs (slow) for already processed files
        if done and (bank_name, filename) in done:
            answers.append(done[bank_name, filename])
            continue

        if 

        pdf = PDF(pdf_fn)
        paras = [para for para in pdf.yield_paragraphs(detect_tables=True)]


        if not paras:
            # Scanned PDF???
            ans = {}
            num_pages = 0
            num_paras = 0
            ok = False
        else:
            num_pages = paras[-1].page
            num_paras = len(paras)
            logger.info(f' - Firm="{bank_name}". filename="{filename}"; {num_pages} pages; {num_paras} paragraphs')
            context = '\n\n'.join(para.text for para in paras)
            path = questions_path / bank_name
            path.mkdir(exist_ok=True)
            question_fn = path / '{filename}.txt'
            ans = llm.find_answer(question, context, question_fn=question_fn, verbose=False)
            ok = True


        #check_text_under_limit('paras')

        ans['ok'] = ok
        ans['bank_name'] = bank_name
        ans['filename'] = filename
        ans['num_pages'] = num_pages
        ans['num_paras'] = num_pages
        print(ans)

        answers.append(ans)

    # Save table
    df = pd.DataFrame(answers)
    df.to_csv(output_fn, sep='\t', index=False)




def main():

    # Just to have pretty debugging messages...
    log_format = '<green>{time:HH:mm:ss.S}</green> | <level>{level: <8}</level> | <blue><level>{message}</level></blue>'
    logger.remove()
    logger.add(sys.stderr, format=log_format, colorize=True, level="DEBUG") # TRACE DEBUG INFO SUCCESS WARNING ERROR CRITICAL
    
    base_path = Path('C:/users/shawn/credit-cards-shawn/data/')
    # TODO: iterate over periods
    subfolder_names = [f.name for f in base_path.iterdir() if f.is_dir() and f.name.startswith('2')]

    for period in subfolder_names:
        process_period(period)



if __name__ == '__main__':
    main()



