
from rouge import Rouge
import openai
import numpy as np
import os
import matplotlib.pyplot as plt
import process_sql
import os
import re
import spider_eval
import statsmodels.api as sm
from rouge import Rouge
import numpy as np
import os
import matplotlib.pyplot as plt
import statsmodels.api as sm
import sqlparse
import json
import sqlite3
from nltk import word_tokenize



openai.api_key = ""
rouge = Rouge()
model_name = 'gpt-3.5-turbo' 

def extract_schema_from_sql_file(file_path):
    with open(file_path, 'r') as file:
        sql_content = file.read()

    parsed = sqlparse.parse(sql_content)

    create_table_statements = [statement for statement in parsed if statement.get_type() == 'CREATE']

    statement = []
    for _ in create_table_statements:
        statement.append(str(_))
    return '\n'.join(statement)

def get_schema_demonstration(db_name):

    db_path = f'/Users/keshen/Documents/ISI/NL2Query/dataset/spider/database/{db_name}/{db_name}.sqlite'
    schema = process_sql.Schema(process_sql.get_schema(db_path))
    # print(schema.idMap)
    return schema.idMap

def get_schema_code(db_name):
    db_path = f'spider/database/{db_name}/{db_name}.sqlite'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    create_table_statements = cursor.fetchall()
    return [statement[0] for statement in create_table_statements if statement[0] is not None]

def gpt_response(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL queries and capable of delivering the SQL queries necessary for conducting analyses on a database in response to a given input question. "},
        {"role": "user", "content": f"{question}"},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer

def get_related_example(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL and capable of finding the most relevant example set for a target question and its related schema. Keep your answer short by directly point out the index of the most relevant Example Set."},
        {"role": "user", "content": f"{question}"},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer

def gpt_correctness(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL queries and capable of examining the SQL queries for given schema and input question."},
        {"role": "user", "content": f"{question}"},
        {"role": "assistant", "content": "The answer is incorrect."},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer


def gpt_objective_checking(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL queries and capable of examining the SQL queries for given schema and input question."},
        {"role": "user", "content": f"{question}"},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer

def gpt_solution_checking(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL queries and capable of examining the SQL queries for given schema and input question."},
        {"role": "user", "content": f"{question}"},
        {"role": "assistant", "content": "The First Solution is incorrect."},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer



def gpt_solution_response(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL queries and capable of delivering the SQL queries necessary for conducting analyses on a database in response to a given input question. Review the provided solutions and determine the correct one, or propose a new solution if none are correct. Please provide an SQL query that is case-insensitive. Incorporate LOWER() or UPPER() to ensure the query is not affected by text case."},
        {"role": "user", "content": f"{question}"},
        # {"role": "assistant", "content": "The First Solution is incorrect."},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer


def gpt_schema_explanation(schema):
    
    messages = [
        {"role": "system", "content": "You are an expert in SQL queries. Please understand the provided database schema thoroughly and provide a brief explanation as comment for each column in the tables."},
        {"role": "user", "content": f"\\* Shema:\n \\*{schema}\n\\* Explanation:\n\\*"},
        # {"role": "assistant", "content": "The First Solution is incorrect."},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer


def gpt_solution_decomposition(question):

    messages = [
        {"role": "system", "content": "You are an expert in SQL queries and capable of breaking down the SQL queries into parts, testing each part for correctness and delivering an integrated, correct query based on the provided schema and question. "},
        {"role": "user", "content": f"{question}"},
        # {"role": "assistant", "content": "The First Solution is incorrect."},
    ]
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    except:
        print('error! try again!')
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)

    answer = response.choices[0].message['content']
    return answer