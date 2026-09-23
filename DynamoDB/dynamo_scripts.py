""" run this once to fix permissions error on intial run of the dynamodb container:
    
    # 1. Create the local data directory if it doesn't exist
    mkdir -p ./docker/dynamodb

    # 2. Grant read/write permissions so the container can access it
    sudo chmod -R 777 ./docker/dynamodb


 """


import json
import boto3
import os
import sys
from datetime import datetime

from boto3.dynamodb.types import TypeDeserializer

dyno_endpoint_url= os.getenv("DYNAMODB", "http://127.0.0.1:8000")

# Connect to local DynamoDB container running on port 8001
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=dyno_endpoint_url,
    region_name="us-east-1",  # Local requires a dummy region
    aws_access_key_id="dummy",  # Local requires dummy credentials
    aws_secret_access_key="dummy",
)


def scanRecursive(tableName, **kwargs):
        """
        NOTE: Anytime you are filtering by a specific equivalency attribute such as id, name 
        or date equal to ... etc., you should consider using a query not scan

        kwargs are any parameters you want to pass to the scan operation
        """
        dbTable = dynamodb.Table(tableName)
        response = dbTable.scan(**kwargs)
        if kwargs.get('Select')=="COUNT":
            return response.get('Count')
        data = response.get('Items')
        while 'LastEvaluatedKey' in response:
            response = kwargs.get('table').scan(ExclusiveStartKey=response['LastEvaluatedKey'], **kwargs)
            data.extend(response['Items'])
        return data


def truncateTable(tableName):
    table = dynamodb.Table(tableName)
    
    #get the table keys
    tableKeyNames = [key.get("AttributeName") for key in table.key_schema]

    #Only retrieve the keys for each item in the table (minimize data transfer)
    projectionExpression = ", ".join('#' + key for key in tableKeyNames)
    expressionAttrNames = {'#'+key: key for key in tableKeyNames}
    
    counter = 0
    page = table.scan(ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames)
    with table.batch_writer() as batch:
        while page["Count"] > 0:
            counter += page["Count"]
            # Delete items in batches
            for itemKeys in page["Items"]:
                batch.delete_item(Key=itemKeys)
            # Fetch the next page
            if 'LastEvaluatedKey' in page:
                page = table.scan(
                    ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames,
                    ExclusiveStartKey=page['LastEvaluatedKey'])
            else:
                break
    print(f"Deleted {counter}")
            

def create_llm_traces_table():
    try:
                       
        table = dynamodb.create_table(
            TableName="LLMTraces",
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},  # Partition Key
                {"AttributeName": "trace_id", "KeyType": "RANGE"},  # Sort Key
            ],
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "trace_id", "AttributeType": "S"},
            ],
            # Local environment ignores billing mode but requires this structure
            BillingMode="PAY_PER_REQUEST",
        )

        # Wait until the table exists (usually instant on local)
        table.meta.client.get_waiter("table_exists").wait(TableName="LLMTraces")
        print("Table 'LLMTraces' created successfully!")

    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("Table 'LLMTraces' already exists.")
        else:
            print(f"Error creating table: {e}")




#def insert_llm_record(session_id, trace_id, record_type, raw_json_string):
def insert_llm_record(session_id, trace_id, record_type, data_dict):
    
    try:
        # Parse the string into a native Python dictionary rather than a json string
        model_name = data_dict.get("model", "unknown-model")
        # print(f"Model Name:{model_name}")

        # Construct the Composite Sort Key: TYPE#MODEL#TRACE_ID
        # e.g., REQUEST#qwen2.5:latest#trace_12345
        composite_sort_key = f"{record_type}#{model_name}#{trace_id}"
    
        item = {
            "session_id": session_id,  # Partition Key
            "trace_id": composite_sort_key,  # Sort Key (Holds type, model, and MLFlow's trace ID)
            "model_name": model_name,  # Kept as a separate attribute for easy reading
            "record_type": record_type,  # "REQUEST" or "RESPONSE"
            "created_date": str(datetime.now()),
            "payload": data_dict  # the full JSON structure
        }

        table = dynamodb.Table("LLMTraces")
        table.put_item(Item=item)
        print(
            f"Successfully inserted {record_type} for {model_name} under Sort Key: {composite_sort_key}"
        )
    except Exception as e:
        print(f"\n[ERROR in dynamo_scripts.insert_llm_record: {e}", file=sys.stderr)


if __name__ == "__main__":
    
    # sample MLflow request string
    
    # request_payload = {
    #     "model": "qwen2.5:latest", 
    #     "messages": [{"role": "system", "content": "\"You are a helpful medical data assistant. Your job is to summarize the provided context documents into a single, comprehensive, cohesive answer. Only use facts directly mentioned in the context. Do not make up information.\""}, 
    #                  {"role": "user", "content": "Based on the following retrieved reference contexts, please write a single consolidated summary answering this question: 'Please tell me something important about how to treat the elderly as patients?'\n\n---\nRETRIEVED CONTEXT DOCUMENTS:\nvisual impairment; hearing impairment; malnutrition/weight loss; dementia; and caregiver burden). These protocols are included here as important aspects of care for older people with long-term conditions, which might also be relevant to social care.\n\n---\n\nthe process of care is as important as the outcomes. Older people want continuity of care in order to develop relationships with paid carers, a named key person to coordinate care, co-production of care with users and carers, and good links with the wider system of health and social care, allowing effective response at times of crisis.\n\n---\n\nthe process of care is as important as the outcomes. Older people want continuity of care in order to develop relationships with paid carers, a named key person to coordinate care, co-production of care with users and carers, and good links with the wider system of health and social care, allowing effective response at times of crisis.\n\n---\n\nthe process of care is as important as the outcomes. Older people want continuity of care in order to develop relationships with paid carers, a named key person to coordinate care, co-production of care with users and carers, and good links with the wider system of health and social care, allowing effective response at times of crisis.\n\n---\n\nthe process of care is as important as the outcomes. Older people want continuity of care in order to develop relationships with paid carers, a named key person to coordinate care, co-production of care with users and carers, and good links with the wider system of health and social care, allowing effective response at times of crisis.\n---\n\nConsolidated Summary:"}
    #                 ], 
    #     "stream": True, 
    #     "stream_options": {"include_usage": True}}
    
    request_payload = {"model": "qwen2.5:latest", "messages": [{"role": "system", "content": "\"You are a helpful medical data assistant. Your job is to summarize the provided context documents into a single, comprehensive, cohesive answer. Only use facts directly mentioned in the context. Do not make up information.\""}, {"role": "user", "content": "Based on the following retrieved reference contexts, please write a single consolidated summary answering this question: 'Please tell me something important about caring for the elderly?'\n\n---\nRETRIEVED CONTEXT DOCUMENTS:\nmattered to people, and how these related to personalised care. Older people in both settings identified the importance of living a ‘normal’ life, maintaining social contact with people of all Older people with social care needs and multiple long-term conditions 39 of 166 generations, having money and knowing their rights, and the ability to choose meaningful activities.\n\n---\n\nand social care, allowing effective response at times of crisis. ES6 What older people want from care and support There is good evidence from 1 qualitative study (Granville et al, 2010,+) that older people value the importance of living a ‘normal’ life, maintaining social contact with people of all generations, having money and knowing their rights, and the ability to choose meaningful activities.\n\n---\n\nand social care, allowing effective response at times of crisis. (REC 1.2.1) ES6 What older people want from care and support There is good evidence from 1 qualitative study (Granville et al 2010 +) that older people value the importance of living a ‘normal’ life, maintaining social contact with people of all generations, having money and knowing their rights, and the ability to choose meaningful activities.\n\n---\n\nthat the system can respond effectively at times of crisis. Importance of support that extends beyondpersonal care Challis (2010b, +/-), a UK mixed methods study, found that older people emphasised the importance of practical help with housework, shopping and banking: ‘There are all sorts of basic needs that aren’t being met for people who live by themselves’ (interviewee 1, p180).\n\n---\n\nthis as a priority area to make research recommendations on. Review questions 3.2 Carer support: how shouldservices work with and support carers of older people with multiple long-term conditions (who may have long-term conditions themselves)?\n---\n\nConsolidated Summary:"}], "stream": True, "stream_options": {"include_usage": True}}

    
    response_payload = {
        "id": "chatcmpl-726", "choices": [{"finish_reason": "stop", "index": 0, "logprobs": None, 
        "message": {"content": "An important aspect of treating elderly patients is ensuring that the process of care is as valued as the outcomes. Older individuals prefer continuity of care to build relationships with paid carers and having a named key person to coordinate care. Collaborative care involving the users and carers (co-production) is also significant. Additionally, establishing good links with the broader health and social care system is crucial for an effective response during crises.", 
        "refusal": None, "role": "assistant", "annotations": None, "audio": None, "function_call": None, 
        "tool_calls": None}}], "created": 1789722735, 
        "model": "qwen2.5:latest", "object": "chat.completion", 
        "metadata": None, "moderation": None, "service_tier": None, 
        "system_fingerprint": "fp_ollama", 
        "usage": {"completion_tokens": 84, "prompt_tokens": 415, "total_tokens": 499, "completion_tokens_details": None, "prompt_tokens_details": None}
    }

    
    create_llm_traces_table() # this will only create the table if it doesn't already exist
        
    # insert_llm_record(
    #     session_id="session_98765123",
    #     trace_id="trace_1234512",
    #     record_type="REQUEST",
    #     data_dict=request_payload
    # )

    # insert_llm_record(
    #     session_id="session_98765123",
    #     trace_id="trace_1234512",
    #     record_type="RESPONSE",
    #     data_dict=response_payload
    # )
    
    # allData = scanRecursive("LLMTraces")
    # for line in allData:
    #     print(f"{line}\n")
    
    # clear out the table if we need to
    #truncateTable("LLMTraces")

