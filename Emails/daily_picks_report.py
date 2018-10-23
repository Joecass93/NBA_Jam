import pandas as pd
from datetime import datetime, date
import smtplib
import numpy as np
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from os.path import expanduser
import email_config
home_dir = expanduser("~")
import sys
sys.path.insert(0, "%s/projects/NBA_Jam/"%home_dir)
from utilities.db_connection_manager import establish_db_connection
import re


def main():

    ## get today's date
    today = datetime.now().date().strftime("%m/%d/%Y")

    conn = establish_db_connection('sqlalchemy').connect()
    picks_df = pd.read_sql("SELECT rank, away_team, home_team, vegas_spread, pred_spread_str, pick_str, best_bet FROM daily_picks", con = conn)

    ## clean up the table
    cols_clean = ["Rank", "Away", "Home", "Spread", "Predicted Spread", "Pick", "Best Bet"]
    picks_df.columns = cols_clean

    picks_df = picks_df.sort_values(['Rank'])
    picks_df['Rank']  = picks_df['Rank'].astype(np.int64)
    picks_df['Spread'] = np.where(picks_df['Spread'] > 0,
                                  picks_df['Away'] + " (+" + picks_df['Spread'].astype(str) + ")",
                                  picks_df['Away'] + " (" + picks_df['Spread'].astype(str) + ")")
    picks_df['Best Bet'] = np.where(picks_df['Best Bet'] == "Y", "Yes", "No")

    # report_cols = {'rank':'Rank', 'away_team':'Away', 'home_team':'Home',
    #                'vegas_spread':'Spread', 'pred_spread_str':'Predicted Away Spread',
    #                'pick_str':'Pick', 'best_bet':'Best Bet'
    #                }

    ## get list of fields to include in the email
    #report_df = picks_df[list(report_cols.keys())]
    print picks_df

    ## get list of email recepients
    degenerates = list(email_config.degenerates.values())

	## build email in html
    body_html = """\
    <html>
        <head>
        <style>
        </style>
        </head>
        <body>
            <p>Free money for {td} ;)</p>
            <br></br>
            <p>
                {acct_table}
            </p>
            <br></br>
        </body>
    </html>
    """

    report_df_html = picks_df.to_html(justify = 'center', index = False)
    report_df_html = re.sub("<th>", "<th width = '100px'; color = black, bgcolor = lightgray>", report_df_html)
    report_df_html = re.sub("<td>", "<td align = 'center'>", report_df_html)

    body_html = body_html.format(acct_table = report_df_html, td = today)

    ## build subject line based on date range
    subject = "NBA Rundown for %s"%today
    print subject

    ## details
    fromaddr = "joecass93@gmail.com"
    toaddr = degenerates
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(degenerates)
    msg['Subject'] = subject

    ##
    msg.attach(MIMEText(body_html, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "Cassidy93")
    text = msg.as_string()

	## send da email!
    try:
        server.sendmail(fromaddr, toaddr, text)
        print "Daily picks email for %s successfully sent to: %s"%(today, msg['To'])
        print ""
    except Exception as e:
        print "Warning! Email alert did not send because: %s"%e

    server.quit()

    return None


if __name__ == "__main__":
    main()
