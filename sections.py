from settings import COMPONENTS, HO_COMPONENTS
from datetime import date
import slack_interface
import jira_interface
import followup


class LineItem():
    def __init__(self, **fields):
        self.fields = fields

    # These methods return the line_fmt with any vars expanded from the item itself
    def jira_line_title(self, line_fmt):
        return line_fmt.format(**self.fields)

    def slack_line_title(self, line_fmt):
        return f'<{self.fields["link"]}|{line_fmt.format(**self.fields)}>'


class Section():
    def __init__(self, heading, line_items, line_fmt, message_if_none='', show_count=True):
        self.heading = heading
        self.line_items = line_items
        self.line_fmt = line_fmt
        self.message_if_none = message_if_none
        self.show_count = show_count

        print(f'Populated section for "{self.heading}"')

    def get_section(self, for_slack=False, max_len=85):
        title_count = f' ({len(self.line_items)})' if self.show_count else ''

        section_items = []

        if self.heading:
            section_items.append(f'*{self.heading}{title_count}:*')

        section_items.append('\n\n')

        if not self.line_items and self.message_if_none:
            section_items.append(f'_{self.message_if_none}_')
            section_items.append('\n')

        else:
            for li in self.line_items:
                item_title = li.slack_line_title(self.line_fmt) if for_slack else li.jira_line_title(self.line_fmt)
                section_items.append(item_title)
                section_items.append('\n')
                section_items.append(li.fields["summary"][:max_len])
                section_items.append('\n\n')

        return ''.join(section_items)


class SecFromJira(Section):
    def __init__(self, heading, query, line_fmt, only_followup=False, **kwargs):

        line_items = []

        issues = jira_interface.get_tickets(query)

        # Admittedly an edge case, but doesnt seem to merit a whole new class
        if only_followup:
            issues = followup.filter_followup(issues)

        for issue in issues:
            line_items.append(
                LineItem(  # Dates truncated to display only relevant/desireable date info
                    key=issue.key, priority=issue.fields.priority.name, created=issue.fields.created[:10],
                    updated=issue.fields.updated[:16].replace('T', '_'), summary=issue.fields.summary,
                    link=issue.permalink()))

        super(SecFromJira, self).__init__(
            heading=heading,
            line_items=line_items,
            line_fmt=line_fmt,
            **kwargs)


class SecFromSlack(Section):
    def __init__(self, heading, line_fmt, archived=False, **kwargs):
        _CHN_URL_BASE = 'https://birdrides.slack.com/archives/'  # No need to store this as a setting I think
        line_items = []

        for channel in slack_interface.get_channels(archived):
            line_items.append(
                LineItem(
                    key=channel['name'], created=str(date.fromtimestamp(channel['created'])),
                    summary=channel['topic']['value'], link=f"{_CHN_URL_BASE}{channel['id']}"))

        super(SecFromSlack, self).__init__(
            heading=heading,
            line_items=line_items,
            line_fmt=line_fmt,
            **kwargs)


def _instantiate(sec_comp):
    if sec_comp['from_jira']:
        return SecFromJira(**sec_comp['kwargs'])
    else:
        return SecFromSlack(**sec_comp['kwargs'])


def get_sections(name="full_ho"):
    sections = []
    if name == "full_ho":
        sections.extend(_instantiate(s) for s in HO_COMPONENTS)
    else:
        sections.append(_instantiate(COMPONENTS[name]))
    return sections
