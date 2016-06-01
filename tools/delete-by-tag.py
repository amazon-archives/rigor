""""
Deletes percepts from the database that have a certain tag.
Optionally removes the percept data files too.
"""

import argparse
from rigor.database import Database
from rigor.config import RigorDefaultConfiguration
from rigor.perceptops import PerceptOps
from rigor.types import Percept, PerceptTag

def main():
	parser = argparse.ArgumentParser(description='Deletes percepts from the database by tag and deletes the percept data files.')
	parser.add_argument('database', help='Name of database to use')
	parser.add_argument('tag', help='Percepts with this tag will be deleted')
	parser.add_argument('-c', '--config', type=str, default='~/.rigor.ini', help='Path to .rigor.ini config file.  Default: ~/.rigor.ini')
	parser.add_argument('--keep-percept-data', action='store_true', default=False, help="Don't remove the percept data files")
	parser.add_argument('-n', '--dryrun', action='store_true', default=False, help="Don't actually delete anything")
	args = parser.parse_args()
	config = RigorDefaultConfiguration(args.config)

	db = Database(args.database, config)
	ops = PerceptOps(config)

	if args.dryrun:
		print('DRY RUN')

	with db.get_session() as session:
		percepts = session.query(Percept).join(PerceptTag).filter(PerceptTag.name == args.tag).all()
		if len(percepts) == 0:
			print('No percepts have the tag "{}"'.format(args.tag))
		for ii, percept in enumerate(percepts):
			print('{} of {}: deleting percept with id {}'.format(ii, len(percepts), percept.id))
			if args.dryrun:
				continue
			if args.keep_percept_data:
				# only delete database entry, not percept file
				session.delete(percept)
			else:
				# delete percept data file as well as database entries
				ops.destroy(percept, session)

	if args.dryrun:
		print('DRY RUN')

if __name__ == '__main__':
	main()
