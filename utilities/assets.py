from datetime import date, timedelta, datetime

def main():
	gameday = range_all_dates(start_date, end_date)
	print gameday

## Enter dates as string of format 'YYYY-MM-DD'
def range_all_dates(start_date, end_date):
	date_range_list = []
	start_date = datetime.strptime(start_date, "%Y-%m-%d")
	end_date = datetime.strptime(end_date, "%Y-%m-%d")
	print "first %s"%start_date
	print "second %s"%end_date
	for n in range(int ((end_date - start_date).days)+1):
		d = start_date + timedelta(n)
		d = d.strftime("%Y/%m/%d")
		date_range_list.append(d)
	return date_range_list

if __name__ == "__main__":
	main(start_date, end_date)