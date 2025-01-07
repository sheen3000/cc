import os
import json
from pathlib import Path
import hashlib
from typing import Optional

import tiktoken
from loguru import logger
from openai import OpenAI
from sqlitedict import SqliteDict


# To an alternative OpenAI's API KEY
if False:
    api_key = '<PASTE HERE>'
    os.environ["OPENAI_API_KEY"] = api_key


# Make sure env var exists
if "OPENAI_API_KEY" in os.environ:
    print('Ok: API key present in env')
else:
    exit('Error: API key not present')


class LLM:
    '''
    Oracle that calls an LLM to answer questions
    '''

    def __init__(
        self,
        model: Optional[str] = None,
        cache_filename: Optional[Path] = None
    ):
        self.client = OpenAI()

        # Current list of models:
        # https://platform.openai.com/docs/models

        # GPT-4o is much cheaper than GPT4 ... (note that we mostly care about cost per INPUT token)
        # See: https://openai.com/pricing
        # Cost per 1m tok is $30-60 for GPT4; $10 for GPT4T and $5 for GPT4o (and $0.5 for GPT3.5T)

        #default_model = 'gpt-4-turbo-2024-04-09'
        #default_model = 'gpt-4-0613'
        default_model = 'gpt-4o-2024-05-13' # $5 per 1m tokens; at 8k tokens per file this is only ~100 files
        #default_model = 'gpt-3.5-turbo-0125' # $0.5 per 1m tokens! Much cheaper; not as good

        self.model = default_model if model is None else model
        self.use_cache = cache_filename is not None
        self.usage = 0

        if self.use_cache:
            self.cache_filename = cache_filename
            logger.info(f'Connecting to LLM cache "{self.cache_filename}"')
            self.cache_db = SqliteDict(str(self.cache_filename))


    def find_answer(
            self,
            question: str,
            context: str,
            question_fn: Optional[Path] = None,
            temperature: float = 0.2,
            verbose: bool = False
        ):

        # Parameter reference :
        # https://platform.openai.com/docs/api-reference/chat/create?lang=python

        # Important: when using JSON mode, you must also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if finish_reason="length", which indicates the generation exceeded max_tokens or the conversation exceeded the max context length.

        # Other parameters
        # seed
        # temperature
        
        # VALIDATE TOKEN LENGTH OF QUESTION
        # "This model's maximum context length is 16385 tokens."
        enc = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(enc.encode(context))
        if num_tokens >= 10000: # Leave some space for question and token-string mismatch
            ratio = 10000 / num_tokens
            new_len = int(ratio * len(context)) + 1
            logger.info(f' - Warning: had to reduce the size of the context to fit max context length (was: {num_tokens})')
            context = context[:new_len]
        
        print(len(context))
        print(len(question))
        
        full_question = question + context

        if question_fn is not None:
            question_fn.write_text(full_question, encoding='utf-8')

        # Load data from cache if available
        if self.use_cache:
            augmented_question = full_question + '\n' + f'INFO: llm={self.model}'
            h = hashlib.sha256(augmented_question.encode('utf-8')).hexdigest()
            ans = self.cache_db.get(h)
            if ans is not None:
                logger.info('     Loading LLM response from cache')
                if verbose:
                    print('=' * 24, f'LLM Prompt', '=' * 24)
                    print(full_question)
                ans['source'] = 'cache'
                ans['usage'] = 0
                return ans

     

        logger.info(f'     Querying LLM (model="{self.model}")')

        response = self.client.chat.completions.create(
          model = self.model,
          response_format = { "type": "json_object" },
          max_tokens = 2000,
          # seed=1234,
          #user = 'sergio-salings',
          temperature=temperature,
          messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": full_question}
          ]
        )

        if verbose:
            print('=' * 24, f'LLM Prompt', '=' * 24)
            print(full_question)
            print('=' * 24, f'LLM Response', '=' * 24)
            print(response)
            print()

        # Response API:
        # https://platform.openai.com/docs/api-reference/chat/object
        finish_reason = response.choices[0].finish_reason
        if finish_reason != 'stop':
            print(f'WARNING!!! Finish reason was "{finish_reason}"')
            print('==== QUESTION:')
            print(full_question)
            print('==== RESPONSE:')
            print(response)
            print('==== REASON:')
            print(response.choices[0].finish_reason)
            print()
            assert False # FIX
            ans = {'success': False, 'start': None, 'end': None, 'source': 'error'}
        else:
            ans = response.choices[0].message.content
            assert ans is not None
            ans = json.loads(ans)
            assert response.usage is not None
            usage = response.usage.total_tokens
            ans['usage'] = usage
            
            if self.use_cache:
                self.cache_db[h] = ans
                self.cache_db.commit()
            
            ans['source'] = 'llm'

        ans['llm'] = self.model
        ans['temperature'] = temperature
        return ans

