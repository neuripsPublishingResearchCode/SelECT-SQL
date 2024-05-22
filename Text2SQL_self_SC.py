import json
from spider_eval import evaluate
import gptTest
import copy
from process_sql import get_schema
import Text2SQLCallAPI
import os
import re
import random
from Schema2TableSampleExamination import check_query
import time
def updateTips(messages, tip, res):
    if res:
        messages.append({"role": "assistant", "content": f"{res}"})
    if tip:
        messages.append({"role": "user", "content": f"{tip}"})
    res = Text2SQLCallAPI.gpt_tips(messages)
    return messages, res

def CodeRepresentationPromptConstruction(schema, question, solution):
    return f"\\*Given the following database schema: *\\ \n {schema}\n \\*Answer the following: {question}*\\ \n\\*Student solution: {solution}*\\ \n \\*Your solution:*\\ \n ```sql\n Select```"

def CodeRepresentationwithDataPointsConstruction(schema, question):
    return f"\\*Given the following database schema:*\\ \n {schema}\n\\*Answer the following: {question}*\\ \n\\*Your solution:*\\ \n ```sql\n Select```"


def get_schema_explanation(db):
    schemaFile = f"NL2SQL/Schama/{db}_schema_explanation.json"
    if os.path.exists(schemaFile):
        with open(schemaFile, 'r') as file:
            schema_exp = json.load(file)
        
    else:
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))
        schema_exp = Text2SQLCallAPI.gpt_schema_explanation(schema)
        print("------------------GPT is generating schema explanation!-------------------")
    return schema_exp 


def CodePrepresentationPrompting(dev_dict):
    Response = []
    for _ in dev_dict:
        db = _['db_id']
        question = _['question']
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))
        exm_schema_exp = get_schema_explanation(db)
        gptSol = _['gpt_response_updated']
        chkQ = check_query(_)
        p = CodeRepresentationPromptConstruction(schema, question, gptSol)   
        l = _['label']
        if not chkQ:
            res = Text2SQLCallAPI.gpt_solution_correction_incorrect(p, exm_schema_exp)
            print(res)
            _['gpt_response_corrected'] = res
        else:
            res = Text2SQLCallAPI.gpt_solution_correction_correct(p, exm_schema_exp)
            print(res)
            _['gpt_response_corrected'] = res
        Response.append(_)
    json_object = json.dumps(Response, indent=4)
    with open(f'NL2SQL/response/AutoSelected-CoT/One-shot/{hardness}_gpt_response_correction.json', 'w') as file:
        file.write(json_object)


def ProvideDataPoints(query_dict, dataPoint_dict):
    Response = []
    for qd, dp in zip(query_dict, dataPoint_dict):
        db = qd['db_id']
        question = qd['question']
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))
        exm_schema_exp = get_schema_explanation(db)
        gptSol = qd['gpt_response_updated']
        datapoints = '```'.join(dp['generated_datapoints'].split('```')[:-1])
        p = CodeRepresentationwithDataPointsConstruction(schema, question)
        # print(p)
        res = Text2SQLCallAPI.gpt_solution_with_datapoints(p, datapoints)
        print(res)
   

        qd['gpt_response_corrected'] = res
        Response.append(qd)
    json_object = json.dumps(Response, indent=4)
    with open(f'response/Generate_with_datapoints/AutoSelected-CoT-One-Shot/{hardness}_gpt_response_.json', 'w') as file:
        file.write(json_object)

def CodeRepresentation(dev_dict):
    Response = []
    for _ in dev_dict:
        db = _['db_id']
        question = _['question']
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))
        exm_schema_exp = get_schema_explanation(db)
        gptSol = _['gpt_response_updated']
        # chkQ = check_query(_)
        p = CodeRepresentationPromptConstruction(schema, question, gptSol)   
        """with tips"""
        messages = [
        {"role": "system", "content": "You are an expert in SQL and capable of delivering correct SQL queries for database analysis. I'll first give you some tips and please keep these tips in mind as you proceed. Eventually, you will receive a schema, a specific question, and a student's solution. Based on the tips, please adjust the provided query to enhance its accuracy in answering the question."}
        ]
        tip = "# Tip: When using the \'GROUP BY\' clause, consider prioritizing the primary key if it aligns logically with the requirements of question. Often, you may need to group by other columns to achieve meaningful data summaries and analyses."
        messages, res = updateTips(messages, tip, res=None)
        tip = "# Tip: Use clauses 'LEFT JOIN', 'CAST', 'REPLACE', 'DATEDIFF', 'IN', and 'OR' judiciously. Replace <> with !=."
        messages, res = updateTips(messages, tip, res)
        tip = "# Tip: Ensure that join operations are executed correctly by avoiding redundant joins, unnecessary nested queries, or missing essential joins between tables. "
        messages, res = updateTips(messages, tip, res)
        tip = "# Tip: Whenever possible, opt for join clauses instead of nested queries in your SQL statements."
        messages, res = updateTips(messages, tip, res)
        tip = "# Tip: If applicable, prefer using \'COUNT(*)\' over \'COUNT(column_name)\' when you need to count rows regardless of column values."
        messages, res = updateTips(messages, tip, res)
        tip = "# Tip: For questions aimed at identifying extremes such as the youngest, oldest, or top minimum or maximum values, opt for employing LIMIT in conjunction with ORDER BY, or utilize the MIN or MAX functions directly. This avoids the complexity and performance issues associated with nested queries and is especially effective for managing large datasets efficiently."
        messages, res = updateTips(messages, tip, res)
        tip = "# Tip: Please provide a case-insensitive SQL query by possibly incorporating the LOWER() or UPPER() functions within the SQL query."
        messages, res = updateTips(messages, tip, res)
        messages.append({"role": "assistant", "content": f"{res}"})
        # print(messages)
        # Prompt = prompting2(question, schema, gpt_queries)

        messages.append({"role": "user", "content": f"{p}"})
        # print(messages)
        res = Text2SQLCallAPI.gpt_solution_with_tips_response(messages)
        print(res)
        _['gpt_response'] = res
        Response.append(_)
    json_object = json.dumps(Response, indent=4)
    with open(f'response/Tips-corrected/autoselect-cot-steps-fewshot/{hardness}_gpt_response.json', 'w') as file:
        file.write(json_object)
    time2 = time.time()
    print(time2-time1)

if __name__ == "__main__":
    time1 = time.time()
    for hardness in ['easy', 'medium', 'hard', 'extra']:
        filepath = f"response/AutoSelected-CoT/Few-shot/{hardness}_openAI_cot_steps_gpt_response_updated.json"
        with open(filepath, 'r') as file:
            queryFile = json.load(file)
        CodeRepresentation(queryFile)

    
# pricing $2.03, timing 7176s
