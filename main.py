import csv

import boto3
from botocore.exceptions import ClientError


def get_rds_instances(session, region):
    rds_client = session.client('rds', region_name=region)
    instances = []
    paginator = rds_client.get_paginator('describe_db_instances')

    for page in paginator.paginate():
        for instance in page['DBInstances']:
            if instance['DBInstanceStatus'] == 'available':
                instances.append({
                    'AccountId': session.client('sts').get_caller_identity()['Account'],
                    'Region': region,
                    'InstanceName': instance['DBInstanceIdentifier'],
                    'InstanceType': instance['DBInstanceClass'],
                    'EngineType': instance['Engine'],
                })
    return instances


def read_profiles(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


def main():
    profile_file = 'profiles.txt'  # プロファイル名が記載されたファイル
    regions = [
        'us-east-1',
        'ap-northeast-1',
        'ap-northeast-2',
        'ap-northeast-3',
    ]  # 必要なリージョンを追加または削除してください

    try:
        profiles = read_profiles(profile_file)
    except FileNotFoundError:
        print(f"Profile file '{profile_file}' not found.")
        return
    except IOError as e:
        print(f"Error reading profile file: {e}")
        return

    all_instances = []

    for profile in profiles:
        try:
            session = boto3.Session(profile_name=profile)
            print(f"Describe DB instances: {profile}")

            for region in regions:
                try:
                    instances = get_rds_instances(session, region)
                    all_instances.extend(instances)
                except ClientError as e:
                    print(f"Error accessing region {region} with profile {profile}: {e}")
        except ClientError as e:
            print(f"Error accessing profile {profile}: {e}")

    # 結果をCSVファイルに出力
    with open('rds_instances.csv', 'w', newline='') as csvfile:
        fieldnames = ['AccountId', 'Region', 'InstanceName', 'InstanceType', 'EngineType']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for instance in all_instances:
            writer.writerow(instance)

    print(f"Total RDS instances found: {len(all_instances)}")
    print("Results have been written to rds_instances.csv")


if __name__ == "__main__":
    main()
