from settings import TZ, JiraSettings
from datetime import datetime
from jira.client import JIRA


_SEP = '—' * 35 + '\n\n'

session = JIRA(JiraSettings.URL, basic_auth=(JiraSettings.USER, JiraSettings.TOKEN))


def get_tickets(query):
    return session.search_issues(query)


def create_ticket(pfx, sections):
    date_local = datetime.now(TZ).date()

    descr = ''.join([_SEP + s.get_section() for s in sections])

    issue_fields = {
        'project': JiraSettings.PROJECT,
        'summary': f'{pfx} NOC Handover {date_local}',
        'description': descr,
        'issuetype': {'name': 'Story'},
    }

    ticket = session.create_issue(fields=issue_fields)
    return ticket


def update_ticket(ticket, sections):
    descr = ''.join([_SEP + s.get_section() for s in sections])
    ticket.update(description=descr)
