import pandas as pd
import httplib2
import os
from googleapiclient import discovery
from oauth2client import file
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.service_account import ServiceAccountCredentials

def get_credentials():

	home_dir = os.path.expanduser('~')
	scopes = 'https://www.googleapis.com/auth/spreadsheets'
	client_secret_file = home_dir + '/Documents/google_docs_creds/client_secret.json'
	app_name = 'Google Sheets API Python Test'

	credential_path = os.path.join(home_dir, 'Documents/google_docs_creds/gdoc_api_creds.json')

	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(client_secret_file, scopes)
		flow.user_agent = app_name
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def full_gsheet_to_df(workbook, sheet):
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
	service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

	result = service.spreadsheets().values().get(
		spreadsheetId=workbook,
		range=sheet
	).execute()

	result = pd.DataFrame(result['values'])

	result.columns = result.iloc[0,:]

	result = result.drop(0).reset_index(drop=True)
	result.columns.name = None

	return result

def df_to_gsheet(workbook, sheet, df, with_col_names=True, clear_range=None):
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
	service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

	df_as_list = df.values.tolist()

	if with_col_names:
		df_as_list.insert( 0, list(df.columns) )

	if clear_range==None:
	    service.spreadsheets().values().update(
			spreadsheetId=workbook,
			range=sheet,
			body={'values': df_as_list },
			valueInputOption='RAW'
	    ).execute()

	else:
		clear_range = sheet + '!' + clear_range
		print "Clearing cells %s"%clear_range

		service.spreadsheets().values().clear(
	        spreadsheetId=workbook,
	        range=clear_range,
	        body={}
	    ).execute()

		service.spreadsheets().values().update(
	        spreadsheetId=workbook,
	        range=sheet,
	        body={'values': df_as_list },
	        valueInputOption='RAW'
	    ).execute()

	return None

def fb_master_preprocess(df):
	print('Cleaning FB data from supermetrics...')

	df['Date'] = pd.to_datetime(df['Date'])
	str_columns = df.iloc[:,:7]
	num_columns = df.iloc[:,7:]
	num_columns.replace({'':0}, regex=False, inplace=True)
	df = pd.concat([str_columns, num_columns], axis=1, join_axes=[str_columns.index])

	for col in df.columns:
		if col not in ['Account', 'Date', 'Campaign', 'Ad set']:
			df[col] = pd.to_numeric(df[col])
			df[col] = df[col].astype(float)
			df[col] = df[col].fillna(0)

	return df
