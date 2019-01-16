import pandas as pd
from datetime import datetime, date
import smtplib
import numpy as np
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from os.path import expanduser
import email_config
import sys
sys.path.insert(0, "%s/projects/NBA_Jam/"%expanduser("~"))
from utilities.db_connection_manager import establish_db_connection
import re


class DailyPicksEmail():

    def __init__(self):
        # self.creds = email_config._get_email_creds()
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.today = datetime.now().date().strftime("%m/%d/%Y")
        self.subject = "NBA Rundown for %s"%self.today
        self.degenerates = list(email_config.degenerates.values())

        self._fetch_picks()

    def _fetch_picks(self):
        picks_sql = "SELECT rank AS Rank, away_team AS Away, home_team AS Home, vegas_spread AS Spread, pred_spread_str AS `Predicted Spread`, pick_str AS Pick, best_bet AS `Best Bet` FROM daily_picks"
        self.picks = pd.read_sql(picks_sql, con = self.conn)
        self._clean_picks()

    def _clean_picks(self):
        self.picks.sort_values(['Rank'], inplace = True)
        self.picks['Rank'] = self.picks['Rank'].astype(np.int64)
        self.picks['Spread'] = np.where(self.picks['Spread'] > 0,
                                        self.picks['Away'] + " (+" + self.picks['Spread'].astype(str) + ")",
                                        self.picks['Away'] + " (" + self.picks['Spread'].astype(str) + ")")

        self.picks['Best Bet'] = np.where(self.picks['Best Bet'] == "Y", "Yes", "No")
        self._build_email()

    def _build_email(self):
        body_html = """\
        <html>
            <head>
            </head>
            <body>
                <p>Free money, the {td} edition ;)</p>
                <br></br>
                <p>
                    {picks}
                </p>
                <br></br>
            </body>
        </html>
        """
        html_picks = self.picks.to_html(justify = 'center', index = False)
        html_picks = re.sub("<th>", "<th width = '100px'; color = black, bgcolor = lightgray>", html_picks)
        html_picks = re.sub("<td>", "<td align = 'center'>", html_picks)
        self.body_html = body_html.format(picks = html_picks, td = self.today)
        self._send_email()

    def _send_email(self):

        fromaddr = "joecass93@gmail.com"
        toaddr = self.degenerates
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = ", ".join(self.degenerates)
        msg['Subject'] = self.subject
        msg.attach(MIMEText(self.body_html, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromaddr, "Steelers93!")
        text = msg.as_string()
        try:
            server.sendmail(fromaddr, toaddr, text)
            print "Daily picks email for %s successfully sent to: %s"%(self.today, msg['To'])
            print ""
        except Exception as e:
            print "Warning! Email alert did not send because: %s"%e
        server.quit()

if __name__ == "__main__":
    DailyPicksEmail()
