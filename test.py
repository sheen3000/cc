# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 21:25:48 2024

@author: shawn
"""

import PyPDF2
import os
from openai import OpenAI
import openai
import numpy as np
import pandas as pd
import backoff 
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)



pdf_file = open('../data/amex_blue.pdf','rb')
read_pdf = PyPDF2.PdfFileReader(pdf_file)
number_of_pages = read_pdf.getNumPages()

page_content=""                # define variable for using in loop.
for page_number in range(number_of_pages):
    page = read_pdf.getPage(page_number)
    page_content += page.extractText()   
    
    
print(page_content)  
   

# @backoff.on_exception(backoff.expo, openai.RateLimitError)
# def completions_with_backoff(**kwargs):
#     return client.chat.completions.create(**kwargs)


# completions_with_backoff(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Once upon a time,"}])

# # Functions
def get_embeddings(chunks):
      
    response = OpenAI().embeddings.create(input=chunks, model="text-embedding-3-large")
    return [np.array(record.embedding) for record in response.data]

def cosine_similarity(a, b):
 return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def distance(a, b):
 return 1 - cosine_similarity(a, b)


def get_response(prompt):
 response = OpenAI().chat.completions.create(
 model = 'gpt-4-0125-preview',
 messages=[
{"role": "user", "content": prompt}
 ]
 )
 return response.choices[0].message.content

# Step 1: split text into chunks
chunks = page_content.split('\n')
print(f'1) Text split into {len(chunks)} chunks')


# # Step 2: compute embeddings for each chunk
embeddings = get_embeddings(chunks)
print(f'2) Computed {len(embeddings)} embeddings of size {len(embeddings[0])}')


# Step 3: select relevant embeddings
query = 'First, what is the date of the credit card agreement? Then, what is the credit card name? Who is the credit card issuer? Can you summarise the general terms (interest rates and fees) of the credit card agreement? Thank you. '

query_embedding = get_embeddings(query)[0]
for i, chunk in enumerate(chunks):
 d = distance(query_embedding, embeddings[i])
 print(f' - Distance of chunk {i} to query: {d:4.2f}')
distances = [distance(query_embedding, e) for e in embeddings]
best_i = np.argmin(distances)
context = chunks[best_i]
print(f'3) Best chunk is number {best_i} ("{context[:30]}..."")')


# Step 4: query the LLM
prompt = f'''
You have been tasked to extract information from a report.
Text excerpts for this examination have been attached at the end of this text, after the word "CONTEXT:".
Please answer the following question: {query}
CONTEXT:
{chunks}
'''
print(f'4) LLM answer:')
answer = get_response(prompt)
print(answer)


# # Step 5: query the LLM to retrieve Stata-ready numeric output
# def get_json_response(prompt):
# response = OpenAI().chat.completions.create(
#  model = 'gpt-4-0125-preview',
#  response_format = { "type": "json_object" },
#  messages=[
#  {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
#  {"role": "user", "content": prompt}
#  ]
# )

# return response.choices[0].message.content
# prompt = f'''
# You have been tasked to extract information from a report. Text excerpts for this examination have been attached at the 
# end of this text, after the word "CONTEXT:".
# Please answer the following question: {query}
# Please provide your response using two JSON fields, the first one named 'success' with values True or
# False, the second named 'answer', with values 1 to 5, with 1 meaning "great" and 5 meaning "terrible".
# CONTEXT:
# {context}
# '''
# print(f'4) LLM answer:')
# answer = get_response(prompt)
# print(answer)



