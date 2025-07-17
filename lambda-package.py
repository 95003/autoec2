import boto3
from datetime import datetime

def lambda_handler(event, context):
    sender = "dhaarun25052004@gmail.com"
    recipient = "mikeyram35@gmail.com"
    aws_regions = ['ap-south-1', 'us-east-1', 'ap-northeast-1']

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"EC2 Instance Action Summary - {current_time}"

    all_instances = []

    for region in aws_regions:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_instances()

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                instance_type = instance.get('InstanceType', 'N/A')
                launch_time = instance.get('LaunchTime', 'N/A')
                name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')

                if state in ['running', 'stopped']:
                    action_taken = None
                    if state == 'running':
                        ec2.stop_instances(InstanceIds=[instance_id])
                        action_taken = 'Stopped'
                    elif state == 'stopped':
                        ec2.terminate_instances(InstanceIds=[instance_id])
                        action_taken = 'Terminated'

                    all_instances.append({
                        'Region': region,
                        'Instance ID': instance_id,
                        'Name': name_tag,
                        'Type': instance_type,
                        'State': state,
                        'Action': action_taken,
                        'Launch Time': str(launch_time)
                    })

    if all_instances:
        # Construct a plain text table
        header = f"{'Region':<15} {'Instance ID':<20} {'Name':<20} {'Type':<10} {'State':<10} {'Action':<10} {'Launch Time'}\n"
        header += "-" * 110 + "\n"
        rows = ""
        for inst in all_instances:
            rows += f"{inst['Region']:<15} {inst['Instance ID']:<20} {inst['Name']:<20} {inst['Type']:<10} {inst['State']:<10} {inst['Action']:<10} {inst['Launch Time']}\n"

        body = (
            f"Hello,\n\n"
            f"The following EC2 instances were processed on {current_time}:\n\n"
            f"{header}{rows}\n"
            "Regards,\nYour AWS Automation"
        )
    else:
        body = f"No running or stopped EC2 instances found across specified regions as of {current_time}."

    # Send the email
    ses = boto3.client('ses', region_name='us-east-1')  # Change if using SES in a different region
    response = ses.send_email(
        Source=sender,
        Destination={'ToAddresses': [recipient]},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': body}
            }
        }
    )

    print("SES response:", response)
    return {
        'statusCode': 200,
        'body': 'Email sent successfully' if response['ResponseMetadata']['HTTPStatusCode'] == 200 else 'Failed to send email'
    }
