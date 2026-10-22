# Automated EC2 Incident Remediation & Monitoring Pipeline

An event-driven cloud monitoring and automated remediation pipeline on AWS. This system detects anomalous CPU degradation on Amazon EC2 instances and initiates zero-touch serverless recovery via Amazon CloudWatch, SNS, and AWS Lambda using Python and Boto3.

---

## Architecture Overview

```text
[ Amazon EC2 Instance ]
      │
      │  (High CPU load / runaway process)
      ▼
[ CloudWatch Metric Alarm ]  (CPUUtilization > 40%)
      │
      │  (Alarm state: OK -> ALARM)
      ▼
[ Amazon SNS Topic ]  (ec2-incident-alerts)
      │
      │  (Asynchronous event delivery)
      ▼
[ AWS Lambda Function ]  (ec2_auto_remediator)
      │
      │  (Validates instance state and calls ec2:RebootInstances)
      ▼
[ Zero-Touch Reboot Initiated ]
      │
      ▼
[ CPU Returns to Baseline ] -> [ Alarm Returns to OK ]
```

---

## Key Features & Highlights

- Proactive anomaly detection using CloudWatch metric alarms
- Decoupled event delivery through Amazon SNS
- Serverless recovery engine implemented with AWS Lambda
- Least-privilege security model using scoped IAM permissions
- Zero-touch remediation for EC2 instances experiencing sustained CPU pressure

---

## Tech Stack & Services

- Cloud Platform: Amazon Web Services (AWS)
- Compute: Amazon EC2
- Monitoring & Alerts: Amazon CloudWatch Alarms, Amazon SNS
- Serverless: AWS Lambda with Python 3.12 and Boto3
- Identity & Security: AWS IAM
- OS / Tools: Linux, Bash, top, sha1sum

---

## Project Structure

```text
aws-ec2-incident-auto-remediation/
├── src/
│   └── lambda_function.py       # Core remediation logic and SNS event parsing
├── iam/
│   └── lambda-policy.json       # Least-privilege IAM policy document
├── README.md                    # Deployment guide and project documentation
└── architecture/
    └── (optional diagram assets)
```

---

## Step-by-Step Implementation

### 1. IAM Execution Role

Create an IAM role named `EC2AutoRemediationLambdaRole` with the trust policy for Lambda:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Attach the least-privilege policy defined in `iam/lambda-policy.json`.

### 2. Lambda Remediation Function

Create a Lambda function named `ec2_auto_remediator` with the following configuration:

- Runtime: Python 3.12
- Memory: 128 MB
- Timeout: 30 seconds
- Execution role: `EC2AutoRemediationLambdaRole`

Use the implementation stored in `src/lambda_function.py`.

### 3. SNS Topic and Lambda Trigger

Create a standard SNS topic named `ec2-incident-alerts` and configure it as the trigger for the Lambda function.

The Lambda function expects the alarm payload to arrive as an SNS event and extracts the target `InstanceId` from the alarm trigger dimensions.

### 4. CloudWatch Alarm Rule

Create a CloudWatch alarm on the `AWS/EC2` metric `CPUUtilization` with these settings:

- Period: 300 seconds
- Statistic: Average
- Condition: Greater than 40%
- Evaluation: 1 datapoint
- Alarm action: Publish to the SNS topic `ec2-incident-alerts`

This ensures that sustained CPU anomalies trigger the automated remediation workflow.

---

## Runtime Logic

The Lambda function performs the following actions:

1. Reads the SNS message from the event payload
2. Parses the JSON alarm message
3. Extracts `InstanceId` from `Trigger.Dimensions`
4. Calls `DescribeInstances` to confirm the operating state
5. Only reboots when the instance is in a valid state (`running` or `stopping`)
6. Returns a success or no-op result for each alarm event

---

## Fault-Injection Testing & Verification

Generate CPU load on the instance to simulate the incident:

```bash
nohup bash -c 'sha1sum /dev/zero & sha1sum /dev/zero &' > /dev/null 2>&1 &
```

Once the alarm triggers, the Lambda execution logs should look similar to this:

```text
[INFO] Alarm 'HighCPU-AutoRemediate-TargetInstance' triggered state 'ALARM' for instance: i-00683c92abf9c8ccd
[INFO] Current state of instance i-00683c92abf9c8ccd is running
[INFO] Initiating automated reboot for instance: i-00683c92abf9c8ccd
[INFO] Reboot signal successfully dispatched to instance i-00683c92abf9c8ccd
REPORT RequestId: ... Duration: 572.27 ms Billed Duration: 1136 ms Memory Size: 128 MB Max Memory Used: 104 MB
```

To confirm recovery, inspect the instance uptime:

```bash
uptime
```

When the CPU load drops and the alarm condition clears, CloudWatch should transition the alarm back to `OK`.

---

## Security Notes

This design follows least-privilege practices by limiting the Lambda role to:

- EC2 instance read and reboot permissions
- CloudWatch Logs write permissions
- No broad administrative or destructive actions

---

## Cleanup

When finished testing, delete the following resources to avoid additional charges:

- CloudWatch alarm
- SNS topic
- Lambda function
- IAM role and policy
- EC2 test instance, if created only for the lab

---

## Summary

This repository provides a simple, practical AWS incident remediation pattern that combines monitoring, messaging, and serverless automation to recover EC2 instances automatically when CPU anomalies occur.

It is ideal for learning AWS event-driven automation, least-privilege IAM design, and operational resilience patterns.

---

## Production Considerations

For a production deployment, consider adding:

- Alarm suppression or cooldown logic
- Multi-instance support
- Dead-letter queue handling for SNS/Lambda failures
- CloudTrail and AWS Config integration
- Automated rollback or recovery validation steps
