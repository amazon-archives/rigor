import os.path
import json

percepts = list()
for count in range(1, 11):
	data_filename = '{:02}.txt'.format(count)
	data_path = os.path.abspath(os.path.join('to_import', data_filename))
	repo_path = os.path.abspath(os.path.join('data_repo', data_filename))
	with open(data_path, 'w') as data_file:
		data_file.write(str(count))
	percept = {
		'source' : 'file://' + data_path,
		'locator': 'file://' + repo_path,
		'format': 'text/plain',
		'tags': [ 'tutorial', ],
		'annotations': [{
			'domain': 'tutorial',
			'confidence': 5,
			'model': str(count),
		}]
	}
	percepts.append(percept)
	with open('percepts.json', 'w') as percepts_file:
		json.dump(percepts, percepts_file)
