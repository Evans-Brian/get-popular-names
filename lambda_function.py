import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to query DynamoDB for names in a specific bucket for a given state.
    
    Handles both direct invocations and API Gateway events.
    
    Direct invocation format:
    {
        "state": "OH",
        "bucket": "stateBucket1"
    }
    
    API Gateway event format:
    {
        "body": "{"call":{"transcript_with_tool_calls":[{"tool_call_id":"tool_call_id","name":"get_names_bucket","arguments":"{\\"bucket\\":\\"stateBucket1\\",\\"state\\":\\"OH\\"}"}]},"name":"get_names_bucket","args":{"bucket":"stateBucket1","state":"OH"}}",
        ...
    }
    
    Returns:
    A list of names in the specified bucket
    """
    # Parse the event to extract state and bucket
    try:
        # Check if this is an API Gateway event
        if isinstance(event, dict) and 'body' in event:
            # Parse the body
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
            
            # Check if this is the expected format with 'args'
            if 'args' in body and isinstance(body['args'], dict):
                state = body['args'].get('state')
                bucket = body['args'].get('bucket')
            # Alternative format with tool calls
            elif 'call' in body and 'transcript_with_tool_calls' in body['call']:
                # Extract from the first tool call
                for tool_call in body['call']['transcript_with_tool_calls']:
                    if 'arguments' in tool_call:
                        args = json.loads(tool_call['arguments'])
                        state = args.get('state')
                        bucket = args.get('bucket')
                        break
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid request format"})
                }
        else:
            # Direct invocation
            state = event.get('state')
            bucket = event.get('bucket')
        
        # Validate required parameters
        if not state or not bucket:
            return format_response({
                "error": "Missing required parameters: state and bucket"
            }, is_api_gateway=('body' in event))
        
        # Validate bucket format
        valid_bucket_prefixes = ['stateBucket', 'otherNamesBucket']
        if not any(bucket.startswith(prefix) for prefix in valid_bucket_prefixes):
            return format_response({
                "error": "bucket must start with 'stateBucket' or 'otherNamesBucket'"
            }, is_api_gateway=('body' in event))
            
        # Validate bucket number if it's a state bucket
        if bucket.startswith('stateBucket'):
            try:
                bucket_number = int(bucket[len('stateBucket'):])
                if bucket_number < 1 or bucket_number > 4:
                    return format_response({
                        "error": "For state buckets, number must be between 1 and 4"
                    }, is_api_gateway=('body' in event))
            except ValueError:
                return format_response({
                    "error": "Invalid bucket format. Expected 'stateBucket1' through 'stateBucket4'"
                }, is_api_gateway=('body' in event))
                
        # Validate bucket number if it's an other names bucket
        elif bucket.startswith('otherNamesBucket'):
            try:
                bucket_number = int(bucket[len('otherNamesBucket'):])
                if bucket_number < 1 or bucket_number > 2:
                    return format_response({
                        "error": "For other names buckets, number must be between 1 and 2"
                    }, is_api_gateway=('body' in event))
            except ValueError:
                return format_response({
                    "error": "Invalid bucket format. Expected 'otherNamesBucket1' or 'otherNamesBucket2'"
                }, is_api_gateway=('body' in event))
            
    except Exception as e:
        return format_response({
            "error": f"Error parsing request: {str(e)}"
        }, is_api_gateway=('body' in event if isinstance(event, dict) else False))
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('StateNames')
    
    # Query DynamoDB
    try:
        response = table.get_item(
            Key={
                'State': state
            }
        )
        
        # Check if the state exists
        if 'Item' not in response:
            return format_response([], is_api_gateway=('body' in event if isinstance(event, dict) else False))
        
        # Get the bucket names
        if bucket in response['Item']:
            return format_response(response['Item'][bucket], is_api_gateway=('body' in event if isinstance(event, dict) else False))
        else:
            return format_response([], is_api_gateway=('body' in event if isinstance(event, dict) else False))
    
    except ClientError as e:
        return format_response({
            "error": str(e)
        }, is_api_gateway=('body' in event if isinstance(event, dict) else False))

def format_response(data, is_api_gateway=False):
    """
    Format the response based on whether it's an API Gateway event or direct invocation
    """
    if is_api_gateway:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
            },
            "body": json.dumps(data)
        }
    else:
        return data 