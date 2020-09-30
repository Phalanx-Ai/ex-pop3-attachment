import poplib
import datetime
from datetime import timedelta
from email.parser import Parser
from email.header import decode_header
from email.utils import parsedate_tz, mktime_tz
import sys
import os
import json

def main():
    CONFIG_FILE = 'config.json'
    configuration = {}

    with open(CONFIG_FILE) as json_file:
        configuration = json.load(json_file)

    print (configuration)

    assert "server" in configuration['parameters']
    assert "username" in configuration['parameters']
    assert "#password" in configuration['parameters']
    assert "accept_from" in configuration['parameters']
    assert 'accept_filename' in configuration['parameters']

    # set default values for the rest of the options
    configuration["parameters"]["accept_timedelta_hours"] = configuration["parameters"].get("accept_timedelta_hours", 24)
    OUTPUT_FILENAME = os.getenv('KBC_DATADIR', '.') + '/out/files/' + configuration['parameters']['accept_filename']

    mailbox = poplib.POP3(configuration['parameters']['server'])
    mailbox.user(configuration['parameters']['username'])
    mailbox.pass_(configuration['parameters']['#password'])

    for i in reversed(range(len(mailbox.list()[1]))):
        print ("Reading an email from the mailbox")
        lines = mailbox.retr(i+1)[1]
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        email = Parser().parsestr(msg_content)
        email_datetime = datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(email.get_all('Date')[0])))
        now_datetime = datetime.datetime.now()

        if now_datetime - timedelta(hours=configuration['parameters']['accept_timedelta_hours']) > email_datetime:
            print ("Email is older than 'accept_timedelta_hours'. Email is ignored and extracting is done")
            break

        if not (configuration['parameters']['accept_from'] in email.get_all('From')[0]):
            print ("Email is not from the 'accept_from' address but <%s>. Email is ignored" % (configuration['parameters']['accept_from']))
            continue

        print ("Parsing the content of the email")

        for part in email.get_payload():
            if (part.get_filename() != configuration['parameters']['accept_filename']):
                print ("Email attachment is not the name that is accepted but '%s'. Attachment is ignored" % (part.get_filename()))
                continue

            fp = open(OUTPUT_FILENAME, 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()


    mailbox.quit()


main()