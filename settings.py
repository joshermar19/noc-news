from pytz import timezone
import os


# "True" uses NP jira project and DEV slack whook 
DEBUG = True 

TZ = timezone('America/Los_Angeles')


class JiraSettings:
    USER = os.environ.get('JIRA_USER')
    TOKEN = os.environ.get('JIRA_TOKEN')

    URL = 'https://birdco.atlassian.net/'
    PROJECT = 'NP' if DEBUG else 'NOC'


class SlackSettings:
    WHOOK = os.environ.get('DEV_WHOOK') if DEBUG else os.environ.get('HANDOVER_WHOOK')

    if WHOOK is None:  # Meaning the environment variable is not set!
        raise Exception('Missing webhook for Slack!')

    TOKEN = os.environ['SLACK_DEV_TOKEN'] if DEBUG else os.environ.get('SLACK_TOKEN')


class Intervals:
    P2 = 28800     # 4 HRS
    P3 = 86400     # 24 HRS
    P4 = 604800    # 1 Week


class NOCStatSettings:
    SIGN_SECRET = os.environ['SLACK_SIGN_SECRET'].encode()  # MUST BE ASCII ¯\_(ツ)_/¯
    AUTHORIZED_USERS = [
        'josh.martinez', 'barry.mayo', 'chris.bosman', 'chris.andrews',
        'derek.gaska', 'rosalba.vergara', 'anthony.vaccaro', 'zachary.thacker']
    SELECTIONS = [
        {
            "text": "Pending Issue Tasks",
            "value": "incident_subtasks"
        },
        {
            "text": "Followup Issues",
            "value": "followup_issues"
        },
        {
            "text": "All Open Issues",
            "value": "outstanding_incidents"
        },
        {
            "text": "Full Handover",
            "value": "full_ho"
        },
        {
            "text": "Open NOC Channels",
            "value": "open_channs"
        },
        {
            "text": "Archived NOC Channels",
            "value": "archived_channs"
        },
    ]


# Macros for queries bellow
_DEF_SORT = 'ORDER BY key DESC'
_TYPES = '(type = Incident or type = "Platform Partner Outage")'

# JQL queries used to populate issue sections
_HO = f'project = NOC AND type = Story AND summary ~ "NOC Handover" AND status != Done {_DEF_SORT}'
_CR = f'project = NOC AND type = "Change Record" AND created > "-24h" {_DEF_SORT}'
_P1 = f'project = NOC AND {_TYPES} AND priority = 1 AND created > "-36h" {_DEF_SORT}'
_OPEN_ISSUES = f'project = NOC AND {_TYPES} AND status != Closed ORDER by priority DESC, key DESC'
_SUBTASKS = 'project = NOC AND issuetype = sub-task AND status != Done ORDER by due ASC'


# Formats used by line titles
_SHORT_FMT = '*{key} — Created: {created}*'
_LONG_FMT = '*{key} — P{priority} — Last update: {updated}*'
_SUBT_FMT = '*{key} — Parent: {parent_key} — Due: {due}*'


COMPONENTS = {
    "open_ho_issues": {
        "from_jira": True,
        "kwargs": {
            "heading": "Open Handover Issues",
            "query": _HO,
            "message_if_none": "No open handover issues.",
            "line_fmt": _SHORT_FMT,
        }
    },
    "recent_cr_issues": {
        "from_jira": True,
        "kwargs": {
            "heading": "Recent Change Records (-24hrs, any status)",
            "query": _CR,
            "message_if_none": "No recent CR issues.",
            "line_fmt": _SHORT_FMT,
        }
    },
    "recent_outages": {
        "from_jira": True,
        "kwargs": {
            "heading": "Recent Outages (-36hrs, any status)",
            "query": _P1,
            "message_if_none": "No recent outages (knock on wood).",
            "line_fmt": _LONG_FMT,
        }
    },
    "outstanding_incidents": {
        "from_jira": True,
        "kwargs": {
            "heading": "Outstanding Incidents",
            "query": _OPEN_ISSUES,
            "message_if_none": "No outstanding incidents. Woohoo!",
            "line_fmt": _LONG_FMT,
            "show_count": True,
        }
    },
    "incident_subtasks": {
        "from_jira": True,
        "kwargs": {
            "heading": "Pending Sub-tasks",
            "query": _SUBTASKS,
            "message_if_none": "No pending sub-tasks.",
            "line_fmt": _SUBT_FMT,
        }
    },
    "open_channs": {
        "from_jira": False,
        "kwargs": {
            "heading": "Open NOC Channels",
            "line_fmt": _SHORT_FMT,
            "show_count": True,
        }
    },
    "followup_issues": {
        "from_jira": True,
        "kwargs": {
            "heading": "Issues that need to be followed up on",
            "query": _OPEN_ISSUES,
            "message_if_none": "No issues need to be followed up on right now.",
            "line_fmt": _LONG_FMT,
            "show_count": True,
            "only_followup": True,
        }
    },
    "archived_channs": {
        "from_jira": False,
        "kwargs": {
            "heading": "Archived NOC Channels",
            "line_fmt": _SHORT_FMT,
            "archived": True,
        }
    }
}

# This defines the entirety of components and their order for the full handover message
HO_COMPONENTS = [
    COMPONENTS["open_ho_issues"],
    COMPONENTS["recent_cr_issues"],
    COMPONENTS["recent_outages"],
    COMPONENTS["outstanding_incidents"],
    COMPONENTS["incident_subtasks"],
    COMPONENTS["open_channs"]
]
