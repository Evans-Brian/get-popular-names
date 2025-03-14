#!/usr/bin/env python3

import boto3
import os
import zipfile
import io
import tempfile
import shutil
import json
import time
import sys

def create_deployment():
    """
    Create a deployment package, update the Lambda function code, and test it.
    """
    # Lambda function details
    function_name = "get-popular-names-by-state"
    region = "us-east-2"
    
    print("Starting deployment process...")
    
    # Step 1: Verify Lambda function file exists
    print("\nStep 1: Verifying Lambda function file...")
    lambda_file_path = "lambda_function.py"
    
    if not os.path.exists(lambda_file_path):
        print(f"Error: Lambda function file '{lambda_file_path}' not found.")
        print("Please make sure the file exists in the current directory.")
        sys.exit(1)
    
    print(f"Lambda function file found: {lambda_file_path}")
    
    # Step 2: Create a deployment package
    print("\nStep 2: Creating deployment package...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    zip_file_path = os.path.join(os.getcwd(), "lambda_function.zip")
    
    try:
        # Copy the Lambda function file to the temporary directory
        temp_lambda_path = os.path.join(temp_dir, "lambda_function.py")
        shutil.copy2(lambda_file_path, temp_lambda_path)
        
        # Create a ZIP file
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(lambda_file_path, "lambda_function.py")
        
        print(f"Deployment package created at: {zip_file_path}")
        
        # Step 3: Update the Lambda function code
        print("\nStep 3: Updating Lambda function code...")
        
        try:
            # Initialize Lambda client
            lambda_client = boto3.client("lambda", region_name=region)
            
            # Read the ZIP file
            with open(zip_file_path, "rb") as zip_file:
                zip_bytes = zip_file.read()
            
            # Update the Lambda function code
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes,
                Publish=True
            )
            
            print(f"Lambda function updated successfully. Version: {response['Version']}")
            
            # Step 4: Create test events
            print("\nStep 4: Creating test events...")
            
            # Direct invocation test events
            
            # Test state bucket
            state_test_event = {
                "state": "OH",
                "bucket": "stateBucket1"
            }
            
            state_test_path = os.path.join(os.getcwd(), "test-event-state.json")
            with open(state_test_path, "w") as f:
                json.dump(state_test_event, f, indent=2)
            
            print(f"State bucket test event created at: {state_test_path}")
            
            # Test state bucket 4 (highest valid bucket)
            state_test_event4 = {
                "state": "OH",
                "bucket": "stateBucket4"
            }
            
            state_test_path4 = os.path.join(os.getcwd(), "test-event-state4.json")
            with open(state_test_path4, "w") as f:
                json.dump(state_test_event4, f, indent=2)
            
            print(f"State bucket 4 test event created at: {state_test_path4}")
            
            # Test other names bucket
            other_test_event = {
                "state": "OH",
                "bucket": "otherNamesBucket1"
            }
            
            other_test_path = os.path.join(os.getcwd(), "test-event-other.json")
            with open(other_test_path, "w") as f:
                json.dump(other_test_event, f, indent=2)
            
            print(f"Other names bucket test event created at: {other_test_path}")
            
            # API Gateway test event
            api_test_event = {
                "version": "2.0",
                "routeKey": "ANY /get-popular-names-by-state",
                "rawPath": "/default/get-popular-names-by-state",
                "headers": {
                    "content-type": "application/json"
                },
                "body": json.dumps({
                    "call": {
                        "transcript_with_tool_calls": [
                            {
                                "tool_call_id": "tool_call_id",
                                "name": "get_names_bucket",
                                "arguments": json.dumps({
                                    "bucket": "stateBucket1",
                                    "state": "OH"
                                })
                            }
                        ]
                    },
                    "name": "get_names_bucket",
                    "args": {
                        "bucket": "stateBucket1",
                        "state": "OH"
                    }
                }),
                "isBase64Encoded": False
            }
            
            api_test_path = os.path.join(os.getcwd(), "test-event-api.json")
            with open(api_test_path, "w") as f:
                json.dump(api_test_event, f, indent=2)
            
            print(f"API Gateway test event created at: {api_test_path}")
            
            # Step 5: Test the Lambda function with state bucket
            print("\nStep 5: Testing Lambda function with state bucket...")
            
            # Wait a moment for the Lambda update to propagate
            print("Waiting for Lambda update to propagate...")
            time.sleep(5)
            
            # Invoke the Lambda function with state bucket
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(state_test_event)
            )
            
            # Read the response
            payload = response["Payload"].read().decode("utf-8")
            
            # Save the response to a file
            state_output_path = os.path.join(os.getcwd(), "output-state.json")
            with open(state_output_path, "w") as f:
                f.write(payload)
            
            # Pretty print the response
            try:
                result = json.loads(payload)
                print("\nLambda function response (state bucket):")
                print(json.dumps(result[:10] if isinstance(result, list) and len(result) > 10 else result, indent=2))
                print(f"\nResponse saved to: {state_output_path}")
            except json.JSONDecodeError:
                print(f"Raw response: {payload}")
            
            # Step 6: Test the Lambda function with state bucket 4
            print("\nStep 6: Testing Lambda function with state bucket 4...")
            
            # Invoke the Lambda function with state bucket 4
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(state_test_event4)
            )
            
            # Read the response
            payload = response["Payload"].read().decode("utf-8")
            
            # Save the response to a file
            state4_output_path = os.path.join(os.getcwd(), "output-state4.json")
            with open(state4_output_path, "w") as f:
                f.write(payload)
            
            # Pretty print the response
            try:
                result = json.loads(payload)
                print("\nLambda function response (state bucket 4):")
                print(json.dumps(result[:10] if isinstance(result, list) and len(result) > 10 else result, indent=2))
                print(f"\nResponse saved to: {state4_output_path}")
            except json.JSONDecodeError:
                print(f"Raw response: {payload}")
            
            # Step 7: Test the Lambda function with other names bucket
            print("\nStep 7: Testing Lambda function with other names bucket...")
            
            # Invoke the Lambda function with other names bucket
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(other_test_event)
            )
            
            # Read the response
            payload = response["Payload"].read().decode("utf-8")
            
            # Save the response to a file
            other_output_path = os.path.join(os.getcwd(), "output-other.json")
            with open(other_output_path, "w") as f:
                f.write(payload)
            
            # Pretty print the response
            try:
                result = json.loads(payload)
                print("\nLambda function response (other names bucket):")
                print(json.dumps(result[:10] if isinstance(result, list) and len(result) > 10 else result, indent=2))
                print(f"\nResponse saved to: {other_output_path}")
            except json.JSONDecodeError:
                print(f"Raw response: {payload}")
            
            # Step 8: Test the Lambda function with API Gateway event
            print("\nStep 8: Testing Lambda function with API Gateway event...")
            
            # Invoke the Lambda function with API Gateway event
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(api_test_event)
            )
            
            # Read the response
            payload = response["Payload"].read().decode("utf-8")
            
            # Save the response to a file
            api_output_path = os.path.join(os.getcwd(), "output-api.json")
            with open(api_output_path, "w") as f:
                f.write(payload)
            
            # Pretty print the response
            try:
                result = json.loads(payload)
                print("\nLambda function response (API Gateway event):")
                print(json.dumps(result, indent=2))
                print(f"\nResponse saved to: {api_output_path}")
            except json.JSONDecodeError:
                print(f"Raw response: {payload}")
            
            print("\nDeployment and testing completed successfully!")
            
        except Exception as e:
            print(f"Error updating or testing Lambda function: {str(e)}")
            sys.exit(1)
            
    finally:
        # Clean up
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_dir)
        print("Temporary directory removed.")
        print("Note: The deployment package (lambda_function.zip) and test files have been kept for reference.")

if __name__ == "__main__":
    create_deployment() 