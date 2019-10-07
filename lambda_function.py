import boto3
import pytz
import requests

SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']


def get_cost():
    """boto3を使って直近の1日の最大の予想請求額を取得する

    :return: response
    """

    now = datetime.datetime.now()

    cloudwatch = boto3.resource('cloudwatch', region_name='us-east-1')
    metric = cloudwatch.Metric('AWS/Billing', 'EstimatedCharges')
    response = metric.get_statistics(
        Dimensions=[
            {
                'Name': 'Currency',
                'Value': 'USD'
            },
        ],
        StartTime=now - datetime.timedelta(days=1),
        EndTime=now,
        Period=86400,
        Statistics=['Maximum']
    )

    return response


def build_message(response):
    """SlackにPOSTするメッセージボディを作成する

    :param response:
    :return: message
    """

    cost = response['Datapoints'][0]['Maximum']
    timestamp = (response['Datapoints'][0]['Timestamp'] + datetime.timedelta(days=1)).astimezone(
        pytz.timezone('Asia/Tokyo')).strftime(
        '%Y年%m月')

    text = '{}のAWS料金'.format(timestamp)
    attachment_text = '${}'.format(cost)

    if float(cost) >= 300.0:
        color = 'danger'   # red
    elif float(cost) >= 150.0:
        color = 'warning'  # yellow
    else:
        color = 'good'     # green

    atachements = {'text': attachment_text, 'color': color}

    message = {
        'text': text,
        'channel': SLACK_CHANNEL,
        'attachments': [atachements],
    }

    return message


def post_message(message):
    """SlackにPOSTする

    :param message:
    :return:
    """

    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(message))
    response.raise_for_status()


def lambda_handler(event, context):

    response = get_cost()

    message = build_message(response)

    post_message(message)