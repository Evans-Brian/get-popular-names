import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to query DynamoDB for names in a specific bucket for a given state.
    
    Expected input:
    {
        "state": "OH",
        "bucketNumber": 1
    }
    
    Returns:
    A list of names in the specified bucket
    """
    # Get parameters from the event
    try:
        state = event['state']
        bucket_number = event['bucketNumber']
        
        # Validate bucket number
        if not isinstance(bucket_number, int) or bucket_number < 1 or bucket_number > 5:
            return {
                "error": "bucketNumber must be an integer between 1 and 5"
            }
    except KeyError as e:
        return {
            "error": f"Missing required parameter: {str(e)}"
        }
    
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
            return []
        
        # Get the bucket names
        bucket_key = f'nameBucket{bucket_number}'
        if bucket_key in response['Item']:
            return response['Item'][bucket_key]
        else:
            return []
    
    except ClientError as e:
        return {
            "error": str(e)
        } 