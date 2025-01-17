#!/usr/bin/env python
# encoding: utf-8

import json
import datetime
import requests
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Slack の設定
SLACK_POST_URL = os.environ['slackPostURL']
SLACK_CHANNEL = os.environ['slackChannel']

response = boto3.client('cloudwatch', region_name='us-east-1')

get_metric_statistics = response.get_metric_statistics(
    Namespace='AWS/Billing',
    MetricName='EstimatedCharges',
    Dimensions=[
        {
            'Name': 'Currency',
            'Value': 'USD'
        }
    ],
    StartTime=datetime.datetime.today() - datetime.timedelta(days=1),
    EndTime=datetime.datetime.today(),
    Period=86400,
    Statistics=['Maximum'])

cost = get_metric_statistics['Datapoints'][0]['Maximum']
date = get_metric_statistics['Datapoints'][0]['Timestamp'].strftime('%Y年%m月%d日')

def build_message(cost):
    if float(cost) >= 300.0:
        color = "#ff0000" #red
    else:
        color = "good"    #green

    text = "%sまでのAWSの料金は、$%sです。" % (date, cost)

    atachements = {"text":text,"color":color}
    return atachements

def lambda_handler(event, context):
    content = build_message(cost)

    # SlackにPOSTする内容をセット
    slack_message = {
        'channel': SLACK_CHANNEL,
        "attachments": [content],
    }

    # SlackにPOST
    try:
        req = requests.post(SLACK_POST_URL, data=json.dumps(slack_message))
        logger.info("Message posted to %s", slack_message['channel'])
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)