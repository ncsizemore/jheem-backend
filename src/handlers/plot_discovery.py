import json
import boto3
import os
from decimal import Decimal
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Helper function to convert DynamoDB Decimal objects to regular numbers
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def search_plots(event, context):
    """
    Lambda handler to search for available plots in DynamoDB
    
    Expected query parameters:
    - city: The city code (e.g., "C.12580")
    - scenario: The scenario name (e.g., "cessation")
    - outcomes: Optional comma-separated list of outcomes to filter by
    """
    
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        city = query_params.get('city')
        scenario = query_params.get('scenario')
        outcomes_filter = query_params.get('outcomes')
        
        if not city or not scenario:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters: city and scenario'
                })
            }
        
        # Initialize DynamoDB client
        dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT_URL', 'http://localhost:4566')
        
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name='us-east-1'
        )
        
        table = dynamodb.Table('jheem-plot-metadata')
        
        # Query DynamoDB by partition key
        partition_key = f"{city}#{scenario}"
        
        try:
            response = table.query(
                KeyConditionExpression=Key('city_scenario').eq(partition_key)
            )
            
            items = response['Items']
            
            # Filter by outcomes if specified
            if outcomes_filter:
                requested_outcomes = [outcome.strip() for outcome in outcomes_filter.split(',')]
                items = [item for item in items if item.get('outcome') in requested_outcomes]
            
            # Format response
            plots = []
            for item in items:
                plots.append({
                    'outcome': item.get('outcome'),
                    'statistic_type': item.get('statistic_type'),
                    'facet_choice': item.get('facet_choice'),
                    's3_key': item.get('s3_key'),
                    'file_size': item.get('file_size'),
                    'created_at': item.get('created_at')
                })
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'city': city,
                    'scenario': scenario,
                    'total_plots': len(plots),
                    'plots': plots
                }, default=decimal_default)
            }
            
        except ClientError as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'error': f'DynamoDB error: {str(e)}'
                })
            }
            
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


def register_plot(event, context):
    """
    Lambda handler to register a new plot in DynamoDB
    
    Expected JSON body:
    {
        "city": "C.12580",
        "scenario": "cessation",
        "outcome": "incidence",
        "statistic_type": "mean.and.interval",
        "facet_choice": "sex",
        "s3_key": "plots/jheem_real_plot.json",
        "file_size": 32768
    }
    """
    
    try:
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Invalid JSON in request body'
                })
            }
        
        # Validate required fields
        required_fields = ['city', 'scenario', 'outcome', 'statistic_type', 'facet_choice', 's3_key']
        missing_fields = [field for field in required_fields if not body.get(field)]
        
        if missing_fields:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                })
            }
        
        # Initialize DynamoDB client
        dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT_URL', 'http://localhost:4566')
        
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name='us-east-1'
        )
        
        table = dynamodb.Table('jheem-plot-metadata')
        
        # Prepare item for insertion
        city_scenario = f"{body['city']}#{body['scenario']}"
        outcome_stat_facet = f"{body['outcome']}#{body['statistic_type']}#{body['facet_choice']}"
        
        item = {
            'city_scenario': city_scenario,
            'outcome_stat_facet': outcome_stat_facet,
            'outcome': body['outcome'],
            'statistic_type': body['statistic_type'],
            'facet_choice': body['facet_choice'],
            's3_key': body['s3_key'],
            'file_size': body.get('file_size', 0),
            'created_at': body.get('created_at', '2025-06-10T20:00:00Z')
        }
        
        try:
            # Insert item into DynamoDB
            table.put_item(Item=item)
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'message': 'Plot registered successfully',
                    'city_scenario': city_scenario,
                    'outcome_stat_facet': outcome_stat_facet,
                    's3_key': body['s3_key']
                })
            }
            
        except ClientError as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': f'DynamoDB error: {str(e)}'
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }
