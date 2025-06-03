import json
import boto3
import os

def test_s3_connection(event, context):
    """
    Simple test function to check S3 connectivity
    """
    
    try:
        # Initialize S3 client
        s3_endpoint = os.environ.get('S3_ENDPOINT_URL', 'http://localhost:4566')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'prerun-plots-bucket-local')
        
        print(f"Attempting to connect to S3 at: {s3_endpoint}")
        print(f"Using bucket: {bucket_name}")
        
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name='us-east-1'
        )
        
        # Try to list objects in the bucket
        print("Attempting to list bucket contents...")
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        print(f"Success! Bucket contains {response.get('KeyCount', 0)} objects")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'S3 connection successful',
                'bucket': bucket_name,
                'endpoint': s3_endpoint,
                'object_count': response.get('KeyCount', 0)
            })
        }
        
    except Exception as e:
        print(f"Error connecting to S3: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'S3 connection failed: {str(e)}'
            })
        }
