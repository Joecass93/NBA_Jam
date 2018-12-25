degenerates = {'TJ Wilson':'wilsontj28@gmail.com',
               'Me':'joecassidy93@yahoo.com',
               'Jamie Webb':'Jamesarthurwebb@gmail.com',
               'Jake Grossman':'jgrossman94@gmail.com',
               'Ethan Klausner':'Ethan.klausner1@gmail.com',
               'Josh Schaperow':'jschape32@gmail.com',
               'Dan Gibson':'dfgibson95@gmail.com',
               'Silas Beyman':'smbeyman@gmail.com',
               'Brendon Anderson':'brendonanderson4@aol.com',
               'Sam Slater':'Sfslater12@gmail.com',
               'Max Feigenbaum':'Maxfeig@gmail.com',
               'Louis Beck':'louis.beck12@gmail.com',
               'anuemman': 'aneumann23@gmail.com',
               'Cody Sharib': 'cody.sharib@gmail.com'
               }
def _get_email_creds():
    creds = {}
    with open('/Users/joe/Documents/picks_email_login.txt') as f:
        for line in f:
            k = line.split(' ')[0]
            v = line.split(' ')[1].rstrip()
            creds[k] = v
    return creds
