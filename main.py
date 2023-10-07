import boto3
import botocore
import urllib
import json



def lambda_handler(event, context):
    prehook(event, context)
    bedrock_runtime = boto3.client('bedrock-runtime')
    s3 = boto3.client('s3')

    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    

    # S3からオブジェクトを取得
    obj = s3.get_object(Bucket=bucket, Key=key)
    
    # オブジェクトのボディ(中身)を文字列として取得
    text = obj['Body'].read().decode('utf-8') 
    
    print(text)


    modelId = 'anthropic.claude-v2'
    # modelId = 'anthropic.claude-instant-v1'
    accept = 'application/json'
    contentType = 'application/json'

    def prompt(text):
        return '\n\nHuman:以下のプログラムのコードを、[変数名の適切さ]、[リファクタリングの余地]、[バグの有無]の観点で、レビューしてください。\n' + text + '\n\nAssistant:'
    
    body = json.dumps({
        "prompt": prompt(text),
        "max_tokens_to_sample": 8191,
        "temperature": 0.1,
        "top_p": 0.9,
    })

    # APIレスポンスからBODYを取り出す
    response = bedrock_runtime.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    # text
    print(response_body)
    completion = response_body.get("completion")
    return completion

def prehook(event, context):
    print('botocore vertion: {0}'.format(botocore.__version__))
    print('boto3 vertion: {0}'.format(boto3.__version__))
    print("Received event: " + json.dumps(event, indent=2))
