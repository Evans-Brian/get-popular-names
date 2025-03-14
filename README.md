# Lambda Function Deployment Tool

This tool helps you deploy and update the `get-popular-names-by-state` Lambda function on AWS.

## Prerequisites

1. Python 3.6 or higher
2. AWS CLI configured with appropriate credentials
3. Required Python packages (install using `pip install -r requirements.txt`)

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure your AWS CLI is configured with the appropriate credentials:
   ```
   aws configure
   ```

## Project Structure

- `lambda_function.py` - The main Lambda function code
- `create_deployment.py` - Script to package and deploy the Lambda function
- `deploy_lambda.ps1` - PowerShell script to automate the deployment process
- `requirements.txt` - Python dependencies

## Usage

### Modifying the Lambda Function

To modify the Lambda function, edit the `lambda_function.py` file directly. This file contains the actual code that will be deployed to AWS Lambda.

### Automated Deployment (Recommended)

Run the PowerShell script to deploy and test the Lambda function in one step:

```powershell
.\deploy_lambda.ps1
```

This script will:
1. Check AWS CLI configuration
2. Install required Python packages
3. Create a deployment package from `lambda_function.py`
4. Update the Lambda function code
5. Test the function with sample events (both direct invocation and API Gateway)
6. Save the responses to `output-direct.json` and `output-api.json`

### Manual Deployment

If you prefer to update the Lambda function manually, you can use the Python script:

```
python create_deployment.py
```

This script will:
1. Verify that `lambda_function.py` exists
2. Create a ZIP deployment package
3. Update the Lambda function on AWS
4. Create test event files for both direct invocation and API Gateway
5. Test the function and save the responses

### Testing the Lambda Function Separately

After updating the function, you can test it using the AWS CLI:

#### Direct Invocation
```
aws lambda invoke --function-name get-popular-names-by-state --payload file://test-event-direct.json --region us-east-2 output-direct.json
```

#### API Gateway Event
```
aws lambda invoke --function-name get-popular-names-by-state --payload file://test-event-api.json --region us-east-2 output-api.json
```

## Lambda Function Details

- **Function Name**: `get-popular-names-by-state`
- **Region**: `us-east-2`
- **Runtime**: Python 3.9
- **Handler**: `lambda_function.lambda_handler`

The function queries a DynamoDB table named "StateNames" based on a state code and bucket number, returning a list of names.

### Input Formats

#### Direct Invocation
```json
{
  "state": "OH",
  "bucketNumber": 1
}
```

#### API Gateway Event
```json
{
  "body": "{\"call\":{\"transcript_with_tool_calls\":[{\"tool_call_id\":\"tool_call_id\",\"name\":\"get_names_bucket_1\",\"arguments\":\"{\\\"bucketNumber\\\":1,\\\"state\\\":\\\"OH\\\"}\"}]},\"name\":\"get_names_bucket_1\",\"args\":{\"bucketNumber\":1,\"state\":\"OH\"}}"
}
```

### Output Formats

#### Direct Invocation
A list of names in the specified bucket:

```json
[
  "Emma",
  "Olivia",
  "Ava",
  ...
]
```

Or an error message if something goes wrong:

```json
{
  "error": "Error message here"
}
```

#### API Gateway Response
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
  },
  "body": "[\"Emma\",\"Olivia\",\"Ava\",...]"
}
```

## API Gateway Integration

The Lambda function is designed to work with API Gateway, supporting the following integration:

1. **HTTP Method**: POST
2. **Endpoint**: /get-popular-names-by-state
3. **Content Type**: application/json

The function can parse requests from API Gateway in the following format:
```json
{
  "call": {
    "transcript_with_tool_calls": [
      {
        "tool_call_id": "tool_call_id",
        "name": "get_names_bucket_1",
        "arguments": "{\"bucketNumber\":1,\"state\":\"OH\"}"
      }
    ]
  },
  "name": "get_names_bucket_1",
  "args": {
    "bucketNumber": 1,
    "state": "OH"
  }
}
```

## Troubleshooting

If you encounter issues:

1. Ensure your AWS credentials are correctly configured
2. Verify that the Lambda function exists in the specified region
3. Check that the IAM role attached to the Lambda function has permissions to access DynamoDB
4. Review CloudWatch logs for any runtime errors
5. For API Gateway issues, check the API Gateway configuration and test the endpoint using Postman or curl 