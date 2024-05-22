import json
import process_sql
import os
import re
import spider_eval
import pandas as pd
folder_Path = ""
prompt_type = ""
Scores = []
C = 0
for label in ['easy', 'medium', 'hard', 'extra']:
    filepath = f"NL2SQL/{folder_Path}{label}_{prompt_type}"

    with open(filepath, 'r') as file:
        response = json.load(file)
    evaluator = spider_eval.Evaluator()

    scores = {}
    etype = "exec"

    cnt = 0
    idx = 0
    incorrect = 0
    logs = []
    for line in response:
        # print(line)
        gpt_query = line['gpt_response_updated']
        # query = line['gpt_response_updated_AS']
        db = line['db_id']
        question = line['question']
        if db not in scores:
            scores[db] = {'cnt': 0, 'error': 0}
        scores[db]['cnt'] += 1
        db_path = f'dataset/spider/database/{db}/{db}.sqlite'
        schema = process_sql.Schema(process_sql.get_schema(db_path))
        # print(line['question'])
        g_str = line['query']
        query_ = gpt_query
            
        p_str = query_

        
        if etype in ["all", "exec"]:
            exec_score = spider_eval.eval_exec_match(db_path, p_str, g_str, '', '', question, db, label, idx)
            # print(exec_score)
            if exec_score:
                cnt += 1.0
            else:
                incorrect += 1
                scores[db]['error'] += 1

        # print('-------------------------')
        idx += 1

    C += cnt
    print(label, len(response), incorrect, cnt / len(response))   


