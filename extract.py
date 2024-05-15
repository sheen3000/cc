
from pypdf2 import PdfReader
import os
from openai import OpenAI
import numpy as np
import pandas as pd

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)



reader = PdfReader("amex_blue.pdf")
text = ""

for page in reader.pages:
    text += page.extract_text() + "\n"


    print(text)
    
    
    exit()
    
    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a witty assistant, always answering with a Joke."},
            {   "role": "user",
                "content": "Who are you?"},
        ]
    )

    chat_completion

    
    

chunks = text.split('\n')
print(f'1) Text split into {len(chunks)} chunks')


# Functions
def get_embeddings(chunks):
 response = OpenAI().embeddings.create(input=chunks, model="text-embedding-3-large")
 return [np.array(record.embedding) for record in response.data]


# Step 2: compute embeddings for each chunk
embeddings = get_embeddings(chunks)
print(f'2) Computed {len(embeddings)} embeddings of size {len(embeddings[0])}')
