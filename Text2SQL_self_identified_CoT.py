import json
from spider_eval import evaluate
import gptTest
import copy
from process_sql import get_schema
import Text2SQLCallAPI
import os
import re
import random


filename = "NL2Query/dataset/spider/train_others.json"
with open(filename, 'r') as file:
    CoTOriData = json.load(file)

def ChainOfThoughtReadIn(filename):
    with open(filename, 'r') as file:
        cot = json.load(file)
    return cot

def ChainOfThoughtSetting(jsonfile, exList):
    return {_: jsonfile[_] for _ in jsonfile if _ in exList}


def BasicPromptConstruction(schema_dict):
    prompts = []
    for key in schema_dict:
        tablename = key
        columns = ", ".join(schema_dict[key])
        p = f"Table {tablename}, columns = [{columns}]"
        prompts.append(p)
    return "\n".join(prompts)


def OpenAIDemonstrationPromptConstruction(schema_dict):
    prompts = []
    P = f"### Complete sqlite SQL query only with no explanation \n### SQLite SQL tables, with their properties: \n"

    for key in schema_dict:
        tablename = key
        columns = ", ".join(schema_dict[key])
        p = f"# {tablename}({columns})"
        prompts.append(p)
    return P+"\n".join(prompts)

def CodeRepresentationPromptConstruction(schema, question):
    return f"\\*Given the following database schema: *\\ \n {schema}\n\\*Answer the following: {question}*\\ \n \\*Your solution:*\\ \n ```sql\n Select```"


def CodeRepresentationCoTConstruction(schema, explanation, question, obj, tables, cols, query):
    P = f"\\*Given the following database schema: *\\ \n {schema}\n\\*Schema Explanation:*\\\n {explanation}\n  \\*Answer the following: {question}*\\ \n  \\*Your solution:*\\\n```sql\n{query}\n```\n\\*The objective of question:*\\\n{obj}\n\\*Relevant Tables:*\\\n{tables}\n\\*Relevant Columns (col_name, table_name):*\\\n{cols}\n\\*Final Query:*\\\n{query}"
    return P


def CodeRepresentationCoTDecomposition(schema, question, explanation, cot):
    P = f"\\*Given the following database schema: *\\ \n {schema}\n \\*Schema Explanation:\n*\\ {explanation}\n \\*Answer the following: {question}*\\ \n {cot}."
    return P



def CodeRepresentationPromptExampleSelection(schema, question):
    P = f"\\*Given the following database schema: *\\ \n {schema}\n \\*Answer the following: {question}*\\ \n The most relevant example set:\n Example Set"
    return P

def CodeRepresentation(idx, schema, question):
    P = f"\\*Ex {idx}: Given the following database schema: *\\ \n {schema}\n \\*Answer the following: {question}*\\ \n"
    return P

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

def reorganizeCoT(CoTList):
    COT = []
    for _ in CoTList:
        db = _['db_id']
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))
        exm_schema_exp = get_schema_explanation(db)
        question = _['question']
        query = _['query']
        tables = _['tables']
        columns = _['correctedCols']
        obj = _['objective']
        COT.append(CodeRepresentationCoTConstruction(schema, exm_schema_exp, question, obj, tables, columns, query))
    return COT

def reorganizeCoTDecompose(CoTList):
    COT = []
    for _ in CoTList:
        db = _['db_id']
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))

        question = _['question']
        query = _['query']
        # tables = _['tables']
        # columns = _['correctedCols']
        # obj = _['objective']
        exm_schema_exp = get_schema_explanation(db)
        cot = _['query_decomposition']

        COT.append(CodeRepresentationCoTDecomposition(schema, question, exm_schema_exp, cot))
    return COT


def CoTCodePrepresentationPrompting(ChainOfThought, dev_dict, flag):
    Hardness = {'easy': [], 'medium':[], 'hard':[], 'extra':[]}
    # print(ChainOfThought)
    # CoT = ChainOfThoughtCodeRepresent(ChainOfThought)
    tokens = []
    for _ in dev_dict:
        db = _['db_id']
        question = _['question']
        schema = "".join(Text2SQLCallAPI.get_schema_code(db))
        exm_schema_exp = get_schema_explanation(db)
        p = CodeRepresentationPromptConstruction(schema, question)   
        l = _['label']

        CoT = ChainOfThought[_['Hardness_of_CoT_example']] # autoselection
        CoT = [CoT[0]]

        datapoints = _['datapoints']

        cotidx = str(_['cluster_idx'])
        CoT = ChainOfThought[cotidx] # embeddingselection
        if flag == 'Steps':
            COT = "\n".join(reorganizeCoT(CoT))  # 没加schema explanation
        else:
            COT = "\n".join(reorganizeCoTDecompose(CoT))

        # res = Text2SQLCallAPI.gpt_response_with_tips(f"{COT}\n{p}")
        res = Text2SQLCallAPI.gpt_solution_with_datapoints(f"{COT}\n{p}", datapoints)

        # print(question)
        print(res)
        # break
        _['gpt_response'] = res
        Hardness[l].append(_)

    for h in Hardness:
        json_object = json.dumps(Hardness[h], indent=4)
        with open(f'response/Generate_with_datapoints/AutoSelected-CoT-One-Shot/{h}_gpt_response.json', 'w') as file:
            file.write(json_object)

def find_example_set_phrases(input_string):

    pattern = re.compile(r'example set (\d+)', re.IGNORECASE)
    matches = pattern.findall(input_string)
    formatted_matches = [match for match in matches]
    return formatted_matches

def selfIdentifiedExamples(flag):
    if flag == "Steps":
        ChainOfThoughtExplain = ChainOfThoughtReadIn('NL2SQL/CoTExamples/Chain-of-Thought-Steps-AutoGen-Randomized(3).json')
    else:
        ChainOfThoughtExplain = ChainOfThoughtReadIn('NL2SQL/CoTExamples/Chain-of-Thought-Decomposition-AutoGen-Randomized(3).json')

    
    filepath = "NL2SQL/dev_with_datapoints.json"
    with open(filepath, 'r') as file:
        jsonfile = json.load(file)
    
    CoTCodePrepresentationPrompting(ChainOfThoughtExplain, jsonfile, flag)


def embeddingIdentifiedExample(flag):
    if flag == "Steps":
        cotPath = "NL2SQL/CoTExamples/OneShotSchemaQuestionQUeyClusterCoT.json"
    else:
        cotPath = None
    ChainOfThoughtExplain = ChainOfThoughtReadIn(cotPath)
    # print(ChainOfThoughtExplain)
    testSamplePath = "NL2SQL/Clustering/dev_schema_question_query_cluster.json"
    with open(testSamplePath, 'r') as file:
        jsonfile = json.load(file)
    
    # print(jsonfile[0])
    CoTCodePrepresentationPrompting(ChainOfThoughtExplain, jsonfile)


if __name__ == "__main__":
    flag = "Steps" # or Steps
    selfIdentifiedExamples(flag)

    # embeddingIdentifiedExample()


