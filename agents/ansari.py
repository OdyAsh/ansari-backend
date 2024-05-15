import time
from pydantic import BaseModel
from util.prompt_mgr import PromptMgr
from tools.search_quran import SearchQuran
from tools.search_hadith import SearchHadith
import json
from openai import OpenAI
import litellm
from langfuse import Langfuse
from datetime import datetime, date
from langfuse.model import InitialGeneration, CreateGeneration, CreateTrace
import hashlib

lf = Langfuse()
lf.auth_check()

MODEL = 'gpt-4o' 

MAX_FUNCTION_TRIES = 3 
class Ansari: 
    def __init__(self, json_format = False):
        sq = SearchQuran()
        sh = SearchHadith()
        self.tools = { sq.get_fn_name(): sq, sh.get_fn_name(): sh}
        self.model = MODEL
        self.pm = PromptMgr()
        self.sys_msg = self.pm.bind('system_msg_fn').render()
        self.functions = [x.get_function_description() for x in self.tools.values()]
        self.message_history = [{
            'role': 'system',
            'content': self.sys_msg
        }]
        self.json_format = json_format
        
    # The trace id is a hash of the first user input and the time. 
    def compute_trace_id(self):
        today = date.today()
        hashstring = str(today) + self.message_history[1]['content']
        result = hashlib.md5(hashstring.encode())
        return 'chash_' + result.hexdigest()

    def greet(self):
        self.greeting = self.pm.bind('greeting')
        return self.greeting.render()
    
    def process_input(self, user_input):
        self.message_history.append({
            'role': 'user',
            'content': user_input
        })
        return self.process_message_history()

    def log(self):
        trace_id = self.compute_trace_id()
        print('trace id is ', trace_id)
        trace = lf.trace(CreateTrace(
            id=trace_id,
            name='ansari-trace'
        ))

        generation = trace.generation(CreateGeneration(
            name='ansari-gen',
            startTime=self.start_time,
            endTime=datetime.now(),
            model=MODEL,
            prompt=self.message_history[:-1],
            completion=self.message_history[-1]['content'],
        )) 

    
    def replace_message_history(self, message_history):
        self.message_history = [{
            'role': 'system',
            'content': self.sys_msg
        }] + message_history
        for m in self.process_message_history():
            if m:
                yield m

    def process_message_history(self):
        # Keep processing the user input until we get something from the assistant
        self.start_time = datetime.now()
        count = 0
        while self.message_history[-1]['role'] != 'assistant':
            try: 
                print(f'Processing one round {self.message_history}')
                # This is pretty complicated so leaving a comment. 
                # We want to yield from so that we can send the sequence through the input
                # Also use functions only if we haven't tried too many times
                use_function = True
                if count >= MAX_FUNCTION_TRIES:
                    use_function = False
                    print('Not using functions -- tries exceeded')
                yield from self.process_one_round(use_function)
                count += 1
            except Exception as e:
                print('Exception occurred: ', e)
                print('Retrying in 5 seconds...')
                time.sleep(5)
        self.log()
        
        
    def process_one_round(self, use_function = True):
        response = None
        while not response:
            try: 
                if use_function: 
                    if self.json_format:
                        response = litellm.completion(
                            model = self.model,
                            messages = self.message_history,
                            stream = True,
                            functions = self.functions, 
                            timeout = 30.0,
                            temperature = 0.0, 
                            metadata = {'generation-name': 'ansari'},
                            response_format = { "type": "json_object" }, 
                            num_retries = 5
                        )
                    else:
                        response = litellm.completion(
                            model = self.model,
                            messages = self.message_history,
                            stream = True,
                            functions = self.functions, 
                            timeout = 30.0,
                            temperature = 0.0, 
                            metadata = {'generation-name': 'ansari'},
                            num_retries = 5
                        )
                else:
                    if  self.json_format:
                        response = litellm.completion(
                            model = self.model,
                            messages = self.message_history,
                            stream = True,
                            timeout = 30.0,
                            temperature = 0.0,  
                            response_format = { "type": "json_object" }, 
                            metadata = {'generation-name': 'ansari'},   
                            num_retries = 5                  
                        )
                    else: 
                        response = litellm.completion(
                            model = self.model,
                            messages = self.message_history,
                            stream = True,
                            timeout = 30.0,
                            temperature = 0.0,  
                            metadata = {'generation-name': 'ansari'},   
                            num_retries = 5                  
                        )

            except Exception as e:
                print('Exception occurred: ', e)
                print('Retrying in 5 seconds...')
                time.sleep(5)
            
    
        words = ''
        function_name = ''
        function_arguments = ''
        response_mode = '' # words or fn
        for tok in response: 
            #print(f'Tok is {tok}')
            delta = tok.choices[0].delta
            if not response_mode: 
                # This code should only trigger the first 
                # time through the loop.
                if 'function_call' in delta and delta.function_call:
                    # We are in function mode
                    response_mode = 'fn'
                    print(f'Tok is {tok}')
                    function_name = delta.function_call.name
                else: 
                    response_mode = 'words'
                print('Response mode: ' + response_mode)

            # We process things differently depending on whether it is a function or a 
            # text
            if response_mode == 'words':
                if delta.content == None: # End token
                    self.message_history.append({
                            'role': 'assistant',
                            'content': words
                        })

                    break
                elif delta.content != None: 
                    words += delta.content
                    yield delta.content 
                else: 
                    continue
            elif response_mode == 'fn':
                if not 'function_call' in delta: # End token
                    function_call = function_name + '(' + function_arguments + ')'
                    # The function call below appends the function call to the message history
                    yield self.process_fn_call(input, function_name, function_arguments)
                    # 
                    break
                elif 'function_call' in delta:
                    function_arguments += delta.function_call.arguments
                    #print(f'Function arguments are {function_arguments}')
                    yield '' # delta['function_call']['arguments'] # we shouldn't yield anything if it's a fn
                else: 
                    continue
            else:
                raise Exception("Invalid response mode: " + response_mode)


    
    def process_fn_call(self, orig_question, function_name, function_arguments):
        if function_name in self.tools.keys():
            args = json.loads(function_arguments)
            query = args['query']
            results = self.tools[function_name].run_as_list(query)
            # print(f'Results are {results}')
            # Now we have to pass the results back in
            if len(results) > 0: 
                for result in results:   
                    self.message_history.append({
                        'role': 'function',
                        'name': function_name, 
                        'content': result
                    })
            else: 
                self.message_history.append({
                    'role': 'function',
                    'name': function_name, 
                    'content': 'No results found'
                })
        else:
            print('Unknown function name: ', function_name) 
