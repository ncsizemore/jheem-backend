import json
import boto3
import os
from botocore.exceptions import ClientError

def get_plot(event, context):
    """
    Lambda handler to retrieve prerun plot JSON from S3
    
    Expected query parameters:
    - plotKey: The key/path to the plot file in S3
    """
    
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        plot_key = query_params.get('plotKey')
        
        if not plot_key:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Missing plotKey parameter'
                })
            }
        
        # Initialize S3 client
        s3_endpoint = os.environ.get('S3_ENDPOINT_URL', 'http://localhost:4566')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'prerun-plots-bucket-local')
        
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name='us-east-1'
        )
        
        # Retrieve the plot JSON from S3
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=plot_key)
            plot_data = response['Body'].read().decode('utf-8')
            
            # Try to parse as JSON to validate
            json.loads(plot_data)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': plot_data
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, OPTIONS'
                    },
                    'body': json.dumps({
                        'error': f'Plot not found: {plot_key}'
                    })
                }
            else:
                raise e
                
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }
