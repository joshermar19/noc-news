import slack_interface
import jira_interface
import sections

current_ticket = None


def _send_handover_msg(ho_ticket, sections, preface=''):
    msg_segments = [f'@here\n{preface}<{ho_ticket.permalink()}|*{ho_ticket.fields.summary}*>']
    msg_segments.extend([s.get_section(for_slack=True) for s in sections])
    slack_interface.send_msg(*msg_segments)


def new_handover(pfx):
    print(f'Commencing "{pfx}" handover job...')

    global current_ticket
    secs = sections.get_sections()
    current_ticket = jira_interface.create_ticket(pfx, secs)
    _send_handover_msg(current_ticket, secs)

    print('Job completed')


def update_handover(preface=''):
    if not current_ticket:  # In case there is no current_ticket yet
        return

    print('Commencing update of last ticket')

    secs = sections.get_sections()
    jira_interface.update_ticket(current_ticket, secs)
    _send_handover_msg(current_ticket, secs, preface=preface)

    print('Job completed')


def mid_handover():
    PFX = "Mid-Shift"
    new_handover(PFX)


def on_handover():
    PFX = "Overnight"
    new_handover(PFX)


def am_update():
    PREFACE = (
        '*Good morning team!*\n'
        '_Overnight handover ticket has been updated to include any new issues._\n\n')
    update_handover(PREFACE)


# Fires shortly after mid_handover
def standup_reminder():
    print('Sending "standup" reminder')
    msg = (
        '@here\n'
        '\n'
        '*Please commence mid-shift standup.*\n'
        '_Remember to assign and close the handover ticket._\n')

    slack_interface.send_msg(msg)

    print('Reminder sent')


def followup_reminder():
    HEADING = f'@here\nHeads up team!\n\n'
    section = sections.get_sections(name='followup_issues')[0]

    if not section.line_items:  # If there's nothing to follow up on, do nothing
        return

    msg = HEADING + section.get_section(for_slack=True)
    slack_interface.send_msg(msg)
