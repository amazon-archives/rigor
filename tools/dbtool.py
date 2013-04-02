#!/usr/bin/env python

""" Utility for applying database patches """

import re
import sys
import os
import argparse

from rigor.config import config
from rigor.database import Database
from rigor.dbmapper import DatabaseMapper

_kPatchPattern = re.compile(r'^(\d+)-(.+)\.sql')
_kDefaultPatchDir = os.path.join(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0], 'sql')
_kTemplateDatabase = 'template1'

def patch(mapper, patch_dir, start_level, stop_level, dry_run, quiet):
	if not os.path.exists(patch_dir):
		sys.stderr.write("Error: can't find patch directory at {0}\n".format(patch_dir))
		sys.exit(1)
	patch_files = os.listdir(patch_dir)
	patch_files = sorted(patch for patch in patch_files if _kPatchPattern.match(patch))
	for patch_file in patch_files:
		matches = _kPatchPattern.match(patch_file)
		patch_name = matches.group(2)
		patch_number = int(matches.group(1))
		if patch_number >= start_level:
			if stop_level and patch_number > stop_level:
				break
			if not quiet:
				print("Applying patch {0:0>6} - {1}".format(patch_number, patch_name))
			if not dry_run:
				with open(os.path.join(patch_dir, patch_file)) as patch:
					mapper.patch(patch, patch_number)

def cmd_patch(args):
	database = Database(args.database)
	mapper = DatabaseMapper(database)
	start_level = mapper.get_patch_level() + 1
	stop_level = None
	if args.level:
		stop_level = args.level
	patch(mapper, args.patch_dir, start_level, stop_level, args.dry_run, args.quiet)

def cmd_create(args):
	if not args.quiet:
		print("Creating database {0}".format(args.database))
	if not args.dry_run:
		Database.create(args.database)
	stop_level = None
	if args.level:
		stop_level = args.level
	try:
		database = Database(args.database)
		mapper = DatabaseMapper(database)
		patch(mapper, args.patch_dir, 0, stop_level, args.dry_run, True)
	except:
		try:
			Database.drop(args.database)
		except:
			pass
		raise

def cmd_clone(args):
	if not args.quiet:
		print("Cloning database {0} to {1}".format(args.source, args.destination))
	if not args.dry_run:
		Database.clone(args.source, args.destination)
		database = Database(args.destination)
		mapper = DatabaseMapper(database)
		mapper.set_destroy_lock(False) # new databases are always unlocked

def cmd_destroy(args):
	if not args.quiet:
		print("Destroying database {0}".format(args.database))
	database = Database(args.database)
	mapper = DatabaseMapper(database)
	if mapper.get_destroy_lock():
		sys.stderr.write("Error: database is locked\n")
		sys.exit(2)
	mapper = None
	database = None
	if not args.dry_run:
		Database.drop(args.database)

def cmd_lock(args):
	if not args.quiet:
		print("Locking database {0}".format(args.database))
	if not args.dry_run:
		database = Database(args.database)
		mapper = DatabaseMapper(database)
		mapper.set_destroy_lock(True)

def cmd_unlock(args):
	if not args.quiet:
		print("Unlocking database {0}".format(args.database))
	if not args.dry_run:
		database = Database(args.database)
		mapper = DatabaseMapper(database)
		mapper.set_destroy_lock(False)

parser = argparse.ArgumentParser(description="Tool for working with Rigor databases")
dry_run_quiet = parser.add_mutually_exclusive_group()
dry_run_quiet.add_argument("-n, --dry-run", dest="dry_run", action="store_true", default=False, help="Print out proposed changes, without modifying the database")
dry_run_quiet.add_argument("-q, --quiet", dest="quiet", action="store_true", default=False, help="Execute without printing anything on the screen")
subparsers = parser.add_subparsers()

# Create
parser_create = subparsers.add_parser("create", help="Create a database")
parser_create.add_argument("database", help="Name of the new database")
parser_create.add_argument("-d, --patch-dir", dest="patch_dir", default=_kDefaultPatchDir, help="Directory containing patch files")
parser_create.add_argument("-l, --level", dest="level", type=int, help="Stop patching at the given level")
parser_create.set_defaults(func=cmd_create)

# Clone
parser_clone = subparsers.add_parser("clone", help="Copy a database")
parser_clone.add_argument("source", help="Name of the database to copy")
parser_clone.add_argument("destination", help="Name of the duplicate database")
parser_clone.set_defaults(func=cmd_clone)

# Patch
parser_patch = subparsers.add_parser("patch", help="Patch a database")
parser_patch.add_argument("-d, --patch-dir", dest="patch_dir", default=_kDefaultPatchDir, help="Directory containing patch files")
parser_patch.add_argument("-l, --level", dest="level", type=int, help="Stop patching at the given level")
parser_patch.add_argument("database", help="Name of the database to patch")
parser_patch.set_defaults(func=cmd_patch)

# Destroy
parser_destroy = subparsers.add_parser("destroy", help="Delete a database")
parser_destroy.add_argument("database", help="Name of the database to delete")
parser_destroy.set_defaults(func=cmd_destroy)

# Lock
parser_lock = subparsers.add_parser("lock", help="Lock a database to prevent deletion")
parser_lock.add_argument("database", help="Name of the database to lock")
parser_lock.set_defaults(func=cmd_lock)

# Unlock
parser_unlock = subparsers.add_parser("unlock", help="Unlocks a delete-locked database")
parser_unlock.add_argument("database", help="Name of the database to unlock")
parser_unlock.set_defaults(func=cmd_unlock)

args = parser.parse_args()
args.func(args)
