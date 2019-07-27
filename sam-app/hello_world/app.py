import json
import requests
import psycopg2


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    conn = psycopg2.connect(host="rain-alert-database.cabbzmps4bpf.us-east-2.rds.amazonaws.com",database="RainAlert", user="postgres", password="fp6r2?$a;k+A7zMd")
    cur = conn.cursor()
    cur.execute('SELECT version()')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": cur.fetchone(),
            # "location": ip.text.replace("\n", "")
        }),
    }
