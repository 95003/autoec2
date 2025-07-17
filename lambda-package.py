import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    regions = ['ap-south-1', 'us-east-1', 'ap-northeast-1', 'us-west-1']
    sender = "dhaarun25052004@gmail.com"
    recipient = "mikeyram35@gmail.com"
    subject = "EC2 Daily Automation Summary (Test Version)"

    # Get AWS Account ID
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']

    # IST time calculation
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = datetime.now(timezone.utc) + ist_offset
    current_time = ist_time.strftime('%Y-%m-%d %H:%M:%S IST')

    # Test summary rows (only 2 rows for now)
    summary_rows = [
        ["i-0a123456789abcdef", "TestInstance-1", "ap-south-1", "on-demand", "Stopped"],
        ["i-0b123456789abcdef", "TestInstance-2", "us-east-1", "spot", "Terminated"],
    ]

    # Compose Email Body
    body = f"EC2 Daily Automation Summary (Test)\n"
    body += f"AWS Account ID   : {account_id}\n"
    body += f"Execution Time   : {current_time}\n\n"

    if summary_rows:
        body += "The following EC2 instances were stopped or terminated:\n\n"
        headers = ["Instance ID", "Instance Name", "Region", "Instance Type", "Action"]
        col_widths = [20, 25, 15, 15, 12]

        # Header row
        header_row = "".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
        separator = "-" * sum(col_widths)

        body += header_row + "\n"
        body += separator + "\n"

        for row in summary_rows:
            formatted_row = "".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row)))
            body += formatted_row + "\n"
    else:
        body += "No EC2 instances were in the running state across the mentioned regions. All instances are already stopped."

    # Print debug info
    print("EMAIL BODY:\n", body)
    print(f"Body Length: {len(body)} characters")

    # Send Email using SES
    ses = boto3.client('ses', region_name='ap-south-1')
    try:
        response = ses.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        print("SES response:", response)
    except ClientError as e:
        print("SES ERROR:", e.response['Error']['Message'])
        return {"status": "Email Failed"}

    return {"status": "Email Sent Successfully"}
