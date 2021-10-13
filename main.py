import poplib
import socket
import datetime
from datetime import timedelta
from email.parser import Parser
from email.utils import parsedate_tz, mktime_tz
import sys
import os
import re

from kbc.env_handler import KBCEnvHandler
import logging
from pathlib import Path

APP_VERSION = "0.4.1"


class Component(KBCEnvHandler):
    DEFAULT_TIMEDELTA = 24
    MANDATORY_PARS = [
        'server',
        'username',
        '#password',
        'accept_from',
        ['accept_filename', 'accept_re_filename']
    ]

    def __init__(self):
        # for easier local project setup
        default_data_dir = Path(__file__).resolve().parent.joinpath('data').as_posix() \
            if not os.environ.get('KBC_DATADIR') else None

        KBCEnvHandler.__init__(
            self,
            self.MANDATORY_PARS,
            log_level=logging.INFO,
            data_path=default_data_dir
        )

        logging.info('Running version %s', APP_VERSION)
        logging.info('Loading configuration...')

        try:
            self.validate_config(self.MANDATORY_PARS)
            self.cfg_params['accept_timedelta_hours'] = \
                self.cfg_params.get('accept_timedelta_hours', self.DEFAULT_TIMEDELTA)
        except ValueError as e:
            logging.exception(e)
            exit(1)

    def run(self):
        params = self.cfg_params
        now_datetime = datetime.datetime.now()

        mailbox = None
        try:
            logging.info('Logging into the mailbox...')
            mailbox = poplib.POP3(params['server'])
            mailbox.user(params['username'])
            mailbox.pass_(params['#password'])
        except poplib.error_proto as error:
            raise RuntimeError('Unable to connect to the server. Please check: server, username and password')
        except socket.gaierror as error:
            raise RuntimeError('Unable to resolve the server name')

        for i in reversed(range(len(mailbox.list()[1]))):
            logging.info("Reading an email from the mailbox...")
            lines = mailbox.retr(i+1)[1]
            msg_content = b'\r\n'.join(lines).decode('utf-8')
            email = Parser().parsestr(msg_content)
            email_datetime = datetime.datetime.fromtimestamp(
                mktime_tz(parsedate_tz(email.get_all('Date')[0]))
            )

            if now_datetime - timedelta(hours=params['accept_timedelta_hours']) > email_datetime:
                logging.info(
                    "Email is older than 'accept_timedelta_hours'. "
                    "The email is ignored and extracting is done")
                break

            if not (params['accept_from'] in email.get_all('From')[0]):
                logging.info(
                    "Email is not from the 'accept_from' address (<%s>) but from <%s>. "
                    "The email is ignored" % (params['accept_from'], email.get_all('From')[0])
                )
                continue

            logging.info("Parsing the content of the email...")

            for part in email.get_payload():
                if (part.get_filename() is None):
                    continue

                if (('accept_filename' in params) and (part.get_filename() != params['accept_filename'])):
                    logging.info(
                        "Email attachment is not the name that is accepted but '%s'. "
                        "The attachment is ignored" % (part.get_filename())
                    )
                    continue
                elif (('accept_re_filename' in params) and (re.match(params['accept_re_filename'], part.get_filename())) is None):
                    logging.info(
                        "Email attachment is not accepted by RE: '%s'. "
                        "The attachment is ignored" % (part.get_filename())
                    )
                    continue

                logging.info(
                    "Valid email attachment found, downloading..."
                )

                output_filename = None
                if ('accept_filename' in params):
                    output_filename = '%s/out/files/%s' % (
                        os.getenv('KBC_DATADIR', '.'),
                        self.cfg_params['accept_filename']
                    )
                elif ('accept_re_filename' in params):
                    output_filename = '%s/out/files/%s' % (
                        os.getenv('KBC_DATADIR', '.'),
                        part.get_filename()
                    )

                if (output_filename is None):
                    logging.info(
                        "Unable to determine the name of the output file"
                    )

                fp = open(output_filename, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

        logging.info('Logging out...')
        mailbox.quit()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_arg = sys.argv[1]
    else:
        debug_arg = False
    try:
        comp = Component()
        comp.run()
    except (RuntimeError, Exception) as err:
        logging.error(str(err))
        exit(1)
    except Exception as exc:
        logging.error("Job Error")
        exit(1)
