from settings import SlackSettings
import requests
import slack
import json

client = slack.WebClient(token=SlackSettings.TOKEN)


def _chan_is_relevant(c, archived):
    keywords = ('issue', 'noc')
    kw_test = all(kw in c['name'] for kw in keywords)
    arch_test = c['is_archived'] if archived else not c['is_archived']
    return all((kw_test, arch_test))


def get_channels(archived):
    relevant_channels = []

    cursor = ''  # Think I tried using None/null and it didn't like that
    while True:  # This has to run with a empty cursor the first time
        response = client.channels_list(cursor=cursor)

        filtered_page = (c for c in response['channels'] if _chan_is_relevant(c, archived))
        relevant_channels.extend(filtered_page)

        cursor = response['response_metadata']['next_cursor']
        if not cursor:
            break

    relevant_channels.sort(key=lambda chan: chan['created'], reverse=True)

    return relevant_channels


# Unused. Will prob remove eventually.
def get_user_name(usr):
    response = client.users_info(user=usr)
    return response['user']['name']


def _txt_block(text):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text
        }
    }


def block_builder(section):
    blocks = []
    block_lines = []

    for line in section.splitlines():
        # If the total char length will not exceed 3k, keep appending lines
        if len('\n'.join(block_lines)) + len(line) < 3000:
            block_lines.append(line)
        # Else reset block_lines list and append to blocks immediately
        else:
            blocks.append(_txt_block('\n'.join(block_lines)))
            block_lines = [line]

    # Append any left over lines
    if block_lines:
        blocks.append(_txt_block('\n'.join(block_lines)))

    return blocks


def msg_builder(*segments):
    blocks = []

    for segment in segments:
        blocks.extend(block_builder(segment))

        if segment != segments[-1]:  # Don't add line for last (or only) segment
            blocks.append({"type": "divider"})
    return blocks


def send_msg(*segments):
    """Accepts any number of message segments"""

    msg = {"blocks": msg_builder(*segments)}

    response = requests.post(SlackSettings.WHOOK, data=json.dumps(msg))
    print(response.status_code)
