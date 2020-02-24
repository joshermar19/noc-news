from flask import Flask, jsonify, request
from slack_interface import client, msg_builder
from settings import NOCStatSettings
from threading import Thread
import sections
import hashlib
import json
import hmac


def _verify_signature(request):
    body = request.get_data().decode('utf-8')
    timestamp = request.headers['X-Slack-Request-Timestamp']
    base = f'v0:{timestamp}:{body}'.encode('utf-8')  # Apparently this needs to be ASCII
    computed_sig = f'v0={hmac.new(NOCStatSettings.SIGN_SECRET, base, digestmod=hashlib.sha256).hexdigest()}'
    return computed_sig == request.headers['X-Slack-Signature']


class TextSection(dict):
    def __init__(self, text):
        dict.__init__(self)
        self.update({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })


class ButtonSection(dict):
    def __init__(self, text, value):
        dict.__init__(self)
        self.update({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View",
                    "emoji": True
                },
                "value": value
            }
        })


class OnDemandView(dict):
    def __init__(self, blocks):
        dict.__init__(self)
        self.update({
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "NOC Status On-Demand",
            },
            "close": {
                "type": "plain_text",
                "text": "Close",
                "emoji": True
            },
            "blocks": blocks
        })


def initial_view():
    blocks = [
        TextSection('What would you like to view?'),
        {"type": "divider"}
    ]
    blocks.extend([
        ButtonSection(**s) for s in NOCStatSettings.SELECTIONS])
    view = OnDemandView(blocks)

    client.views_open(trigger_id=request.form['trigger_id'], view=view)


def interm_view(vid):
    blocks = [
        TextSection("One moment while I cook that up for you...")
    ]
    view = OnDemandView(blocks)
    client.views_update(view=view, view_id=vid)


def final_view(vid, selection):
    _secs = sections.get_sections(selection)
    segments = [s.get_section(for_slack=True, max_len=200) for s in _secs]

    blocks = msg_builder(*segments)
    view = OnDemandView(blocks)
    client.views_update(view=view, view_id=vid)


app = Flask(__name__)


# This presents the initial view
@app.route('/noc-status', methods=['POST'])
def noc_status():
    # Check for correct signing secret
    if not _verify_signature(request):
        return 'Invalid secret!'

    # Check for user authorization
    user_name = request.form['user_name']
    if user_name not in NOCStatSettings.AUTHORIZED_USERS:
        return jsonify({'text': f'User {user_name} is not authorized to do that ;('})

    # Getting this far means you are authorized and the sign secret is correct
    initial_view()

    return ('', 200)


# Listens for any button clicks
@app.route('/interaction', methods=['POST'])
def interaction():

    payload = json.loads(request.form['payload'])
    vid = payload['view']['id']
    selection = payload['actions'][0]['value']

    # First we call the intermediate view (because shit takes time [also 3 sec timeout])
    interm_view(vid)

    # This takes some time. It will be threaded so that we can return this route immediately.
    final_view_thread = Thread(target=lambda: final_view(vid, selection))
    final_view_thread.start()

    return ('', 200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
