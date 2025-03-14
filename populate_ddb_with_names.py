#!/usr/bin/env python3

import csv
from collections import defaultdict
import boto3
import json
import os
import time

def analyze_names(file_path):
    """
    Analyze name frequency data from the specified file.
    
    The function reads data in the format: State, gender, year of birth, name, name frequency
    It compiles all names from 1955 to 2010 (inclusive), gets the total counts for each name,
    and orders the results by total count.
    
    Args:
        file_path (str): Path to the data file
    
    Returns:
        list: List of tuples (name, total_count) ordered by total count in descending order
    """
    # Dictionary to store name counts
    name_counts = defaultdict(int)
    total_name_count = 0
    
    # Read the data file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse the line
            parts = line.strip().split(',')
            if len(parts) != 5:
                continue  # Skip malformed lines
            
            state, gender, year, name, count = parts
            
            try:
                year = int(year)
                count = int(count)
            except ValueError:
                continue  # Skip lines with non-integer year or count
            
            # Only include data from 1955 to 2010
            if 1955 <= year <= 2010:
                name_counts[name] += count
                total_name_count += count
    
    # Convert to list of tuples and sort by count (descending)
    result = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)
    
    return result, total_name_count

def read_international_names(file_path):
    """
    Read international and other names from a text file.
    
    Args:
        file_path (str): Path to the file containing international names
    
    Returns:
        list: List of names
    """
    names = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                name = line.strip()
                if name:  # Skip empty lines
                    names.append(name)
        print(f"Read {len(names)} names from {file_path}")
    except Exception as e:
        print(f"Error reading international names file: {str(e)}")
    
    return names

def print_results(results, limit=None):
    """
    Print the results in a formatted way.
    
    Args:
        results (list): List of tuples (name, count)
        limit (int, optional): Limit the number of results to display
    """
    print(f"{'Rank':<6}{'Name':<20}{'Total Count':<12}")
    print("-" * 38)
    
    for i, (name, count) in enumerate(results[:limit] if limit else results, 1):
        print(f"{i:<6}{name:<20}{count:<12}")

def create_name_buckets(results, max_bucket_size=3950, num_buckets=4):
    """
    Create multiple buckets of names, each not exceeding the max_bucket_size.
    
    Args:
        results (list): List of tuples (name, count)
        max_bucket_size (int): Maximum size of each bucket in characters
        num_buckets (int): Number of buckets to create
    
    Returns:
        list: List of name buckets
    """
    buckets = [[] for _ in range(num_buckets)]
    
    current_bucket_idx = 0
    current_size = 2  # Start with 2 for the brackets []
    
    for name, _ in results:
        # Calculate size with name, quotes, and comma
        name_size = len(name) + 4  # "name", (quotes, comma, and space)
        
        # If adding this name would exceed the bucket size, move to next bucket
        if current_size + name_size > max_bucket_size:
            current_bucket_idx += 1
            current_size = 2
            
            # If we've filled all buckets, stop
            if current_bucket_idx >= num_buckets:
                break
        
        buckets[current_bucket_idx].append(name)
        current_size += name_size
    
    return buckets

def create_international_name_buckets(names, existing_names, max_bucket_size=3950, num_buckets=2):
    """
    Create buckets for international names, excluding any that already exist in state data.
    
    Args:
        names (list): List of international names
        existing_names (set): Set of names that already exist in state data
        max_bucket_size (int): Maximum size of each bucket in characters
        num_buckets (int): Number of buckets to create
    
    Returns:
        list: List of name buckets
    """
    buckets = [[] for _ in range(num_buckets)]
    
    current_bucket_idx = 0
    current_size = 2  # Start with 2 for the brackets []
    
    for name in names:
        # Skip if name already exists in state data
        if name in existing_names:
            continue
            
        # Calculate size with name, quotes, and comma
        name_size = len(name) + 4  # "name", (quotes, comma, and space)
        
        # If adding this name would exceed the bucket size, move to next bucket
        if current_size + name_size > max_bucket_size:
            current_bucket_idx += 1
            current_size = 2
            
            # If we've filled all buckets, stop
            if current_bucket_idx >= num_buckets:
                break
        
        buckets[current_bucket_idx].append(name)
        current_size += name_size
    
    return buckets

def get_all_existing_names(dynamodb, table_name):
    """
    Get all names that already exist in the DynamoDB table.
    
    Args:
        dynamodb: DynamoDB resource
        table_name (str): Name of the DynamoDB table
    
    Returns:
        set: Set of all names in the table
    """
    existing_names = set()
    
    try:
        table = dynamodb.Table(table_name)
        
        # Scan the table to get all items
        response = table.scan()
        items = response.get('Items', [])
        
        # Process all items
        for item in items:
            # Add names from all state buckets
            for i in range(1, 5):  # Changed from 6 to 5 (to get buckets 1-4)
                bucket_key = f'stateBucket{i}'
                if bucket_key in item:
                    existing_names.update(item[bucket_key])
        
        print(f"Found {len(existing_names)} existing names in the database")
        
    except Exception as e:
        print(f"Error getting existing names: {str(e)}")
    
    return existing_names

def write_to_dynamodb(state, name_buckets, unique_names_count, total_name_count, other_name_buckets=None):
    """
    Write the name buckets to DynamoDB.
    
    Args:
        state (str): State code (PK)
        name_buckets (list): List of name buckets
        unique_names_count (int): Total number of unique names
        total_name_count (int): Total count of all names
        other_name_buckets (list, optional): List of international name buckets
    """
    # Initialize DynamoDB client with specific region
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    
    # Table name
    table_name = 'StateNames'
    
    # Check if table exists, if not create it
    try:
        table = dynamodb.Table(table_name)
        table.table_status  # This will raise an exception if the table doesn't exist
    except:
        print(f"Creating {table_name} table...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'State',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'State',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait for table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print("Table created successfully!")
    
    # Prepare the item to be written
    item = {
        'State': state,
        'stateBucket1': name_buckets[0],
        'stateBucket2': name_buckets[1],
        'stateBucket3': name_buckets[2],
        'stateBucket4': name_buckets[3],
        'stateBucket1Count': len(name_buckets[0]),
        'stateBucket2Count': len(name_buckets[1]),
        'stateBucket3Count': len(name_buckets[2]),
        'stateBucket4Count': len(name_buckets[3]),
        'uniqueNamesCount': unique_names_count,
        'totalNameCount': total_name_count
    }
    
    # Add international name buckets if provided
    if other_name_buckets:
        item['otherNamesBucket1'] = other_name_buckets[0]
        item['otherNamesBucket2'] = other_name_buckets[1]
        item['otherNamesBucket1Count'] = len(other_name_buckets[0])
        item['otherNamesBucket2Count'] = len(other_name_buckets[1])
    
    # Write to DynamoDB
    response = table.put_item(Item=item)
    
    print(f"Data written to DynamoDB table {table_name} for state {state}")
    for i, bucket in enumerate(name_buckets, 1):
        print(f"State Bucket {i} size: {len(json.dumps(bucket))} characters, {len(bucket)} names")
    
    if other_name_buckets:
        for i, bucket in enumerate(other_name_buckets, 1):
            print(f"Other Names Bucket {i} size: {len(json.dumps(bucket))} characters, {len(bucket)} names")
    
    print(f"Total unique names: {unique_names_count}")
    print(f"Total name count (sum of all frequencies): {total_name_count}")
    
    return response

def process_state_file(file_path, international_names=None, existing_names=None):
    """
    Process a single state file and write the results to DynamoDB.
    
    Args:
        file_path (str): Path to the state file
        international_names (list, optional): List of international names
        existing_names (set, optional): Set of existing names
    """
    # Extract state code from file name
    state = os.path.basename(file_path).split('.')[0]
    
    print(f"\nProcessing {state}...")
    results, total_name_count = analyze_names(file_path)
    
    # Print top 10 results
    print(f"\nTop 10 names by frequency from 1955 to 2010 for {state}:\n")
    print_results(results, 10)
    
    # Create name buckets
    name_buckets = create_name_buckets(results, max_bucket_size=3950, num_buckets=4)
    
    # Create international name buckets if provided
    other_name_buckets = None
    if international_names:  # Add international names to all states
        if existing_names is None:
            # Initialize DynamoDB client
            dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
            existing_names = get_all_existing_names(dynamodb, 'StateNames')
        
        # Add names from current state buckets
        state_names = set()
        for bucket in name_buckets:
            state_names.update(bucket)
        
        # Create international name buckets
        other_name_buckets = create_international_name_buckets(
            international_names, 
            state_names,  # Only exclude names from this state's buckets
            max_bucket_size=3950, 
            num_buckets=2
        )
        
        print(f"Created {len(other_name_buckets)} international name buckets")
        print(f"International bucket 1: {len(other_name_buckets[0])} names")
        print(f"International bucket 2: {len(other_name_buckets[1])} names")
    
    # Write to DynamoDB
    write_to_dynamodb(state, name_buckets, len(results), total_name_count, other_name_buckets)
    
    print(f"Completed processing for {state}")

def main():
    # Updated data directory for state files
    states_data_dir = "data/states"
    
    # Path to international names file
    international_names_file = "data/other/international_and_other_additional_names.txt"
    
    # Read international names
    international_names = read_international_names(international_names_file)
    
    # Get all state files
    state_files = [os.path.join(states_data_dir, f) for f in os.listdir(states_data_dir) if f.endswith('.TXT')]
    
    print(f"Found {len(state_files)} state files to process")
    
    # Process each state file
    for i, file_path in enumerate(state_files, 1):
        print(f"Processing file {i} of {len(state_files)}: {file_path}")
        process_state_file(file_path, international_names)
        
        # Add a small delay between files to avoid throttling
        if i < len(state_files):
            time.sleep(1)
    
    print("\nAll states processed successfully!")

if __name__ == "__main__":
    main() 