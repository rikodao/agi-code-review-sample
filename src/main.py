import boto3
import botocore
import urllib
import json
ClientError = botocore.exceptions.ClientError
import logging

s3 = boto3.client('s3')

def lambda_handler(event, context):
    prehookForDebug(event, context)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    text = getCode(bucket, key)

    completion = codeReviewWithBedrock(text)
    sendSNSTopicMessage(completion)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('OK!')
    }

def prehookForDebug(event, context):
    print('botocore vertion: {0}'.format(botocore.__version__))
    print('boto3 vertion: {0}'.format(boto3.__version__))
    print('Received event: ' + json.dumps(event, indent=2))

# オブジェクトのボディ(中身)を文字列として取得
def getCode(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    
    text = obj['Body'].read().decode('utf-8') 
    return text 

# コードレビューのための外部API呼び出し
def codeReviewWithBedrock(code):
    bedrock_runtime = boto3.client('bedrock-runtime')
    modelId = 'anthropic.claude-v2'
    accept = 'application/json'
    contentType = 'application/json'

    def prompt(text):
        return '\n\nHuman:以下のLambda上で動くPythonで書かれたプログラムのコードを、[変数名の適切さ]、[リファクタリングの余地]、[バグの有無]、[エラーハンドリングの正しさ]の観点で、10年来の友達として関西弁で正直にレビューしてな。\n' + text + '\n\nAssistant:'
    
    body = json.dumps({
        'prompt': prompt(code),
        'max_tokens_to_sample': 8191,
        'temperature': 0.1,
        'top_p': 0.9,
    })

    # APIレスポンスからBODYを取り出す
    response = bedrock_runtime.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    # text
    print(response_body)
    
    completion = response_body.get('completion')
    return completion

def sendSNSTopicMessage(message):
    message= message
    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:751437213623:test' 
    Message = {'version': '1.0','source': 'custom','content': {'description': message}}
    
    response = sns.publish(
      TopicArn=topic_arn,    
      Message=json.dumps(Message)
     )
