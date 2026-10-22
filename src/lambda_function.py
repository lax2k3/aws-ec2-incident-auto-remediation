import json
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client('ec2')


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        sns_record = event['Records'][0]['Sns']
        sns_message = json.loads(sns_record['Message'])
    except (KeyError, json.JSONDecodeError) as err:
        logger.error("Failed to parse SNS event payload: %s", str(err))
        return {"statusCode": 400, "body": "Invalid payload"}

    alarm_name = sns_message.get('AlarmName', 'Unknown')
    new_state = sns_message.get('NewStateValue', 'Unknown')
    dimensions = sns_message.get('Trigger', {}).get('Dimensions', [])

    instance_id = None
    for dim in dimensions:
        if dim.get('name') == 'InstanceId':
            instance_id = dim.get('value')
            break

    if not instance_id:
        logger.error("No InstanceId found in alarm dimensions.")
        return {"statusCode": 400, "body": "Instance ID not present"}

    logger.info("Alarm '%s' triggered state '%s' for instance: %s", alarm_name, new_state, instance_id)

    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        logger.info("Current state of instance %s is %s", instance_id, state)

        if state not in ['running', 'stopping']:
            logger.warning("Instance %s is in state '%s'. Skipping reboot action.", instance_id, state)
            return {"statusCode": 200, "body": "No action needed"}

        logger.info("Initiating automated reboot for instance: %s", instance_id)
        ec2_client.reboot_instances(InstanceIds=[instance_id])
        logger.info("Reboot signal successfully dispatched to instance %s", instance_id)

        return {
            "statusCode": 200,
            "body": f"Successfully initiated remediation for {instance_id}"
        }

    except Exception as exc:
        logger.error("Error executing remediation on instance %s: %s", instance_id, str(exc))
        raise exc
