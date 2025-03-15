# Get Popular Names - Lambda Function

This tool helps you deploy and update the `get-popular-names-by-state` Lambda function on AWS. The function retrieves popular names from a DynamoDB table based on state and bucket parameters.

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
- `populate_ddb_with_names.py` - Script to populate DynamoDB with names data
- `requirements.txt` - Python dependencies

## Data Sources

This project uses the following data sources:

- **State-level name data**: The U.S. Social Security Administration provides state-specific baby name data, which can be downloaded from [SSA.gov](https://www.ssa.gov/oact/babynames/limits.html). This data includes names given to babies born in each state from 1910 onwards.

- **International names**: Global name data was sourced from [Forebears.io](https://forebears.io/earth/forenames), which provides a comprehensive database of forenames from around the world.

## Data Structure

The project uses a DynamoDB table named "StateNames" with the following structure:

- **Partition Key**: `State` (2-letter state code)
- **Attributes**:
  - `stateBucket1` through `stateBucket4`: Lists of names for each state
  - `otherNamesBucket1` and `otherNamesBucket2`: Lists of international names
  - Various count attributes for statistics

Each state has 4 buckets of names, with each bucket containing up to 3950 characters worth of names.

## Usage

### Modifying the Lambda Function

To modify the Lambda function, edit the `lambda_function.py` file directly. This file contains the actual code that will be deployed to AWS Lambda.

### Populating DynamoDB

To populate the DynamoDB table with names data:

```
python populate_ddb_with_names.py
```

This script will:
1. Process state name data files from the `data/states` directory
2. Create 4 state buckets for each state, with a maximum size of 3950 characters each
3. Create 2 international name buckets for each state
4. Write the data to the DynamoDB table

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
5. Test the function with sample events
6. Save the responses to output files

### Manual Deployment

If you prefer to update the Lambda function manually, you can use the Python script:

```
python create_deployment.py
```

This script will:
1. Verify that `lambda_function.py` exists
2. Create a ZIP deployment package
3. Update the Lambda function on AWS
4. Create test event files for different scenarios
5. Test the function and save the responses

### Testing the Lambda Function Separately

After updating the function, you can test it using the AWS CLI:

#### State Bucket Test
```
aws lambda invoke --function-name get-popular-names-by-state --payload file://test-event-state.json --region us-east-2 output-state.json
```

#### Other Names Bucket Test
```
aws lambda invoke --function-name get-popular-names-by-state --payload file://test-event-other.json --region us-east-2 output-other.json
```

#### API Gateway Test
```
aws lambda invoke --function-name get-popular-names-by-state --payload file://test-event-api.json --region us-east-2 output-api.json
```

## Lambda Function Details

- **Function Name**: `get-popular-names-by-state`
- **Region**: `us-east-2`
- **Runtime**: Python 3.9
- **Handler**: `lambda_function.lambda_handler`

The function queries a DynamoDB table named "StateNames" based on a state code and bucket name, returning a list of names.

### Input Formats

#### Direct Invocation
```json
{
  "state": "OH",
  "bucket": "stateBucket1"
}
```

Valid bucket values:
- `stateBucket1` through `stateBucket4` - State-specific name buckets
- `otherNamesBucket1` and `otherNamesBucket2` - International name buckets

#### API Gateway Event
```json
{
  "body": "{\"call\":{\"transcript_with_tool_calls\":[{\"tool_call_id\":\"tool_call_id\",\"name\":\"get_names_bucket\",\"arguments\":\"{\\\"bucket\\\":\\\"stateBucket1\\\",\\\"state\\\":\\\"OH\\\"}\"}]},\"name\":\"get_names_bucket\",\"args\":{\"bucket\":\"stateBucket1\",\"state\":\"OH\"}}"
}
```

### Output Formats

#### Direct Invocation
A list of names in the specified bucket:

```json
[
  "Michael",
  "David",
  "James",
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
  "body": "[\"Michael\",\"David\",\"James\",...]"
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
        "name": "get_names_bucket",
        "arguments": "{\"bucket\":\"stateBucket1\",\"state\":\"OH\"}"
      }
    ]
  },
  "name": "get_names_bucket",
  "args": {
    "bucket": "stateBucket1",
    "state": "OH"
  }
}
```

## Error Handling

The Lambda function includes comprehensive error handling for:
- Missing or invalid parameters
- Invalid bucket formats
- Invalid bucket numbers (must be 1-4 for state buckets, 1-2 for other names buckets)
- DynamoDB access errors

## Troubleshooting

If you encounter issues:

1. Ensure your AWS credentials are correctly configured
2. Verify that the Lambda function exists in the specified region
3. Check that the IAM role attached to the Lambda function has permissions to access DynamoDB
4. Review CloudWatch logs for any runtime errors
5. For API Gateway issues, check the API Gateway configuration and test the endpoint using Postman or curl 