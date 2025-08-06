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
        dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT_URL')
        
        # Build client args conditionally
        client_args = {'region_name': 'us-east-1'}
        
        # Only set endpoint_url if it's a valid URL (not empty string)
        if dynamodb_endpoint and dynamodb_endpoint.strip():
            client_args['endpoint_url'] = dynamodb_endpoint
            
        dynamodb = boto3.resource('dynamodb', **client_args)
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'jheem-plot-metadata')
        table = dynamodb.Table(table_name)
        
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
        dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT_URL')
        
        # Build client args conditionally
        client_args = {'region_name': 'us-east-1'}
        
        # Only set endpoint_url if it's a valid URL (not empty string)
        if dynamodb_endpoint and dynamodb_endpoint.strip():
            client_args['endpoint_url'] = dynamodb_endpoint
            
        dynamodb = boto3.resource('dynamodb', **client_args)
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'jheem-plot-metadata')
        table = dynamodb.Table(table_name)
        
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


def get_all_available_cities(event, context):
    """
    Lambda handler to get all cities that have plot data available
    Returns cities with their available scenarios in a single API call
    
    Response format:
    {
        "cities": {
            "C.12580": ["cessation", "brief_interruption"],
            "C.12940": ["cessation"]
        },
        "total_cities": 2
    }
    """
    
    try:
        # Initialize DynamoDB client
        dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT_URL')
        
        # Build client args conditionally
        client_args = {'region_name': 'us-east-1'}
        
        # Only set endpoint_url if it's a valid URL (not empty string)
        if dynamodb_endpoint and dynamodb_endpoint.strip():
            client_args['endpoint_url'] = dynamodb_endpoint
            
        dynamodb = boto3.resource('dynamodb', **client_args)
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'jheem-plot-metadata')
        table = dynamodb.Table(table_name)
        
        # Single scan to get all city_scenario combinations
        response = table.scan(
            ProjectionExpression='city_scenario'
        )
        
        # Process data to group by city
        city_data = {}
        for item in response['Items']:
            city_scenario = item['city_scenario']
            if '#' in city_scenario:
                city, scenario = city_scenario.split('#', 1)
                
                if city not in city_data:
                    city_data[city] = []
                
                if scenario not in city_data[city]:
                    city_data[city].append(scenario)
        
        # Sort scenarios for consistency
        for city in city_data:
            city_data[city].sort()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'cities': city_data,
                'total_cities': len(city_data)
            }, default=decimal_default)
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
                'error': f'Failed to get available cities: {str(e)}'
            })
        }
