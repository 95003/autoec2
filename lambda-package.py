import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    regions = ['ap-south-1', 'us-east-1', 'ap-northeast-1','us-west-1']
    sender = "dhaarun25052004@gmail.com" //Add the Sender mail here
    recipient = "mikeyram35@gmail.com" //Add the receiver mail here
    subject = "EC2 Daily Automation Summary"

    # Get AWS Account ID
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']

    # Manually define IST timezone (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = datetime.now(timezone.utc) + ist_offset
    current_time = ist_time.strftime('%Y-%m-%d %H:%M:%S IST')

    summary_rows = []

    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance.get('InstanceLifecycle', 'on-demand')
                name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')

                if instance_type == 'spot':
                    ec2.terminate_instances(InstanceIds=[instance_id])
                    action = "Terminated"
                else:
                    ec2.stop_instances(InstanceIds=[instance_id])
                    action = "Stopped"

                summary_rows.append([instance_id, name_tag, region, instance_type, action])

    # Compose Email Body
    body = f"EC2 Automation Summary\nAWS Account ID: {account_id}\nTime of Execution: {current_time}\n\n"

    if summary_rows:
        body += "The following EC2 instances were stopped or terminated:\n\n"
        body += "{:<20} {:<20} {:<15} {:<15} {}\n".format("Instance ID", "Instance Name", "Region", "Instance Type", "Action")
        body += "-" * 85 + "\n"
        for row in summary_rows:
            body += "{:<20} {:<20} {:<15} {:<15} {}\n".format(*row)
    else:
        body += "No EC2 instances were in the running state across the mentioned regions. All instances are already stopped."

    # Send Email using SES
    ses = boto3.client('ses', region_name='ap-south-1')
    try:
        ses.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        raise e

    return {"status": "Completed"}
