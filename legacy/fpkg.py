#!/usr/bin/env python3
# flake8: noqa E302,E501,W291
# fpkg, a linux package manager with proper dependency tracking and file tracking, and async downloading.
#    Copyright (C) 2023  Ohio2
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import shutil
import json
import asyncio
import threading
import multiprocessing
from hashlib import file_digest as hl_fdgst
from urllib.request import urlopen as urll_open
from urllib.request import urlretrieve as urll_down
from urllib.error import HTTPError as urll_HTTPErr
from urllib.error import URLError as urll_URLErr
from tarfile import open as tar_open
from subprocess import Popen as subp_open
from subprocess import DEVNULL as subp_null
from bisect import bisect_left as bs_left

# Variables:
sources = [["felis_core", "https://iohio.xyz/data/pub/felis/core"]]

class Colors:
	blue = u"\u001b[38;5;44m"
	green = u"\u001b[38;5;40m"
	red = u"\u001b[38;5;160m"
	yellow = u"\u001b[38;5;226m"
	purple = u"\u001b[38;5;62m"
	lightsteelblue = u"\u001b[38;5;189m"
	reset = u"\u001b[0m"
col = Colors()

try:
	if os.path.isfile(f"{wd}/etc/fpkg/config.json") and not os.getenv("FPKG_IGNORE_CONFIG") == "n" or not os.getenv("FPKG_IGNORE_CONFIG") == "N":
		with open(f"{wd}/etc/fpkg/config.json", "r") as f:
			config_file = json.load(f)
		wd = config_file["root"]
		sources = config_file["sources"]
except:
	print(f'[{col.yellow}w{col.reset}] Config file not used.')

if os.getenv("FPKG_ROOT"):
	wd = os.getenv("FPKG_ROOT")
elif "wd" not in dict(globals()):
	wd = "/"
if wd != "/":
	print(f'[{col.yellow}w{col.reset}] Working directory is "{wd}" and not "/".')

# Lockfile function that can:
#  a, create lockfile
#  b, check for it, and if it exists exit
#  c, remove the lockfile
def lockfile(arg):
	if arg == "create":
		if not os.path.exists(f"{wd}/var/fpkg/lockfile"):
			open(f"{wd}/var/fpkg/lockfile", "a").close()
		else:
			print(f"[{col.red}e{col.reset}] Lockfile exists, make sure you aren't running a 2nd fpkg instance and if not, remove it.")
			sys.exit(249)
	elif arg == "cleanup":
		if os.path.exists(f"{wd}/var/fpkg/lockfile"):
			os.remove(f"{wd}/var/fpkg/lockfile")

# Check if user is root, used for some operations
def usercheck():
	from pwd import getpwuid
	login = getpwuid(os.getuid())[0]
	if login != "root":
		print(f"[{col.red}e{col.reset}] Login as root, or use sudo.")
		lockfile("cleanup")
		sys.exit(256)

# Used for things that require a summary  eg. i and r, not u though.
# you should pass an array to this.
def summary(contents):
	for content in contents:
		print(f"[{col.lightsteelblue}>{col.reset}] {content}")

# Ask the user if they are sure that they are sure they want to do a operation
# used for *some* operations
def ask(what, prompt=None):
	print(f"[{col.purple}?{col.reset}] {what}")
	if not prompt:
		conf = input("[y/N] ")
		if not conf == "Y" and not conf == "y":
			print(f"[{col.red}e{col.reset}] You are not sure.")
			lockfile("cleanup")
			sys.exit(257)
	else:
		inp = input(f"[{prompt}] ")
		return inp

# Download from {url} to {dest}
def download(url, dest, bar=False):
	try:
		os.makedirs(os.path.dirname(dest), exist_ok=True)
		if bar:
			url_size = int(urll_open(url).info().get('Content-Length', 0))
			open(dest, "wb").close()  # Open in binary write mode
			def report_progress(blocks, block_size, total_size):
				f_size = blocks * block_size
				percent_f = int((f_size / url_size) * 100)
				term_size = shutil.get_terminal_size().columns - 40 if shutil.get_terminal_size().columns < 40 else shutil.get_terminal_size().columns
				progress = int((term_size - 10) * (percent_f / 100))
				if percent_f < 100:
					print(f"[{percent_f} %] [{'#' * progress}{' ' * (term_size - 10 - progress)}]", sep='\r', end='\r', flush=False)
				else:
					print(f"[100 %] [{'#' * (term_size - 10)}]", sep='\r', end='\n', flush=True)
			
			download_thread = threading.Thread(target=urll_down, args=(url, dest, report_progress))
			download_thread.start()
			download_thread.join()
		else:
			urll_down(url, dest)
		return True
	except urll_HTTPErr:
		return False
	except urll_URLErr:
		print(f"[{col.red}e{col.reset}] A url error has occured, you might not be connected to the internet or you might not have SSL certificates installed.")
		lockfile("cleanup")
		cleanup_tmp()

# A class for file operations.
class fileOp:
	# A function that parses a json. 
	def parse_json(path):
		with open(path, "r") as f:
			loaded_json = json.load(f)
		return loaded_json
	
	# A function that sorts, and searches \
	# you may ask why searchign in fileOp? \
	# this because the contents of a file may be sorted, and thus, that counts as a fileOp. 
	def bs_and_sort(needle, haystack):
		haystack = [i.strip() for i in haystack]
		haystack.sort()
		index = bs_left(haystack, needle)
		if index < len(haystack) and haystack[index] == needle:
			return True
		else:
			return False

	# Decompress from {file} to {dest}
	def decompress(file, dest):
		if not os.path.exists(dest):
			os.makedirs(f"{dest}", exist_ok=True)
		tar = tar_open(name=file, mode='r:xz')
		tar.extractall(path=dest)
		tar.close()

class checksums:
# Compare sha256 sums of file and of provided shasums, used for install
	def sha256(file1, file2, f2open="Yes"):
		try:
			with open(file1, "rb", buffering=0) as f:
				sha256_1 = hl_fdgst(f, 'sha256').hexdigest()
			if f2open == "yes":
				with open(file2, "rb", buffering=0) as f:
					sha256_2 = hl_fdgst(f, 'sha256').hexdigest()
				sha256_2 = f"{sha256_2}\n"
			else:
				sha256_2 = file2
			# file digest does not insert a newline, thus we do it ourselves.
			sha256_1 = f"{sha256_1}\n"
			if sha256_1 != sha256_2:
				return False
			else:
				return True
		except FileNotFoundError:
			return False
# Compare blake2b sums and of provided blake2bsums
	def blake2b(file1, b2_2):
		with open(file1, "rb", buffering=0) as f:
			b2_1 = hl_fdgst(f, 'blake2b').hexdigest()
		# file digest does not insert a newline, thus we do it ourselves.
		b2_1 = f"{b2_1}\n"
		if b2_1 != b2_2:
			return False
		else:
			return True

# execute arguments in sh
def script(arguments):
	try:
		subp_open(arguments, stdin=subp_null)
	except FileNotFoundError as e:
		print(f"[{col.yellow}w{col.reset}] {' '.join(arguments)} failed: {e}.")
		print(f"[{col.yellow}w{col.reset}] Do note that this is not a critical part of fpkg, so most likely you don't have to worry.")
class delta:
# Compare v1 file and v2 file, and write that to deltatarget if diffrence has been, indeed, found.
	def check(v1f, v1sha, deltanew):
		# we have to do this in order to check if file is binary, we won't run a delta
		is_binary_string = lambda bytes: bool(bytes.translate(None, bytearray([7,8,9,10,12,13,27]) + bytearray(range(0x20, 0x7f)) + bytearray(range(0x80, 0x100))))
		try:

			if not is_binary_string(open(v1f, "rb").read(1024)):
				with open(file, "rb", buffering=0) as f:
					delta_checksum_chk = hl_fdgst(f, 'sha256').hexdigest()
				if not sha256(v1f, delta_checksum_chk, "No"):
					print(f"[{col.yellow}w{col.reset}] A custom configuration has been found, writing to {deltanew} instead of {v1f}")
					return False
				else:
					return True
		except:
			return True

# Write delta sums
	def save(file, target):
		is_binary_string = lambda bytes: bool(bytes.translate(None, bytearray([7,8,9,10,12,13,27]) + bytearray(range(0x20, 0x7f)) + bytearray(range(0x80, 0x100))))
		try:
			if not is_binary_string(open(file, "rb").read(1024)):
				with open(file, "rb", buffering=0) as f:
					delta_checksum_save = hl_fdgst(f, 'sha256').hexdigest()
					delta_checksum_save = f"{delta_checksum_save}\n"
				with open(target, "w") as f:
					f.write(delta_checksum_save)
		except:
			pass
class pkgFiles:
	# Copy from {vfrom}/{package} to {wd}
	# also from {vfrom}/package.json to {wd}/var/fpkg/pkg/{package}
	def copy_files(vfrom, package, package_format):
		print(f"[{col.blue}:{col.reset}] Installing {package}...")

		with open(f"{wd}/var/fpkg/pkg/{package}/package.json") as f:
			open_file = f.read()
		files_from_file = json.loads(open_file)["files"]
		for file in files_from_file:
			if os.path.exists(file) and delta.check(f"{wd}/var/fpkg/pkg/{package}/{file}", file, f"{file}.new"):
				os.remove(file)

		# Why is dirs_exist_ok=True being ignored anyway?
		try:
			shutil.copytree(f"{vfrom}/{package_format}", f"{wd}/", dirs_exist_ok=True, symlinks=True)
		except:
			subp_open(["cp", "-r", f"{vfrom}/{package_format}/*", f"{wd}/"], stdin=subp_null, stdout=subp_null)
		for file in files_from_file:
			if not os.path.exists(os.path.dirname(f"{wd}/var/fpkg/pkg/{package}/{file}")):
				os.makedirs(os.path.dirname(f"{wd}/var/fpkg/pkg/{package}/{file}"), exist_ok=True)
				os.chmod(os.path.dirname(f"{wd}/var/fpkg/pkg/{package}/{file}"), 0o1204)
		for file in files_from_file:
			delta.save(file, f"{wd}/var/fpkg/pkg/{package}/{file}")
	# create a symlink (and if previous symlink exists, remove it)
	def copy_json(package):
		status, url, repo = db.lookup(package)
		os.makedirs(f"{wd}/var/fpkg/pkg/{package}", exist_ok=True)
		os.chmod(f"{wd}/var/fpkg/pkg/{package}", 0o1204)
		try:
			os.remove(f"{wd}/var/fpkg/pkg/{package}/package.json")
		except FileNotFoundError:
			pass
		shutil.copy2(f"{wd}/var/fpkg/repos/{repo}/packages/{package}/package.json", f"{wd}/var/fpkg/pkg/{package}/package.json")
# List files tracked by fpkg from {wd}/var/fpkg/pkg/{package}/package.json
# used for e.g. remove!
def listpackagefiles(package):
	with open(f"{wd}/var/fpkg/pkg/{package}/package.json", "r") as f:
		open_file = json.load(f)
	files_from_file = open_file["files"]
	return [os.path.join(wd, file) for file in files_from_file]

# List package info
def listpackageinfo(packages):
	for package in packages:
		try:
			with open(f"{wd}/var/fpkg/pkg/{package}/package.json", "r") as f:
				open_file = json.load(f)
			package = open_file["package"]
			package_version = open_file["version"]
			package_files = open_file["files"]
			try:
				package_deps = open_file["dependencies"]
			except KeyError:
				pass
			try:
				package_confs = open_file["conflicts"]
			except KeyError:
				pass

			print(f"package: {package}\nversion: {package_version}")
			# the reason for this for loop is,
			# be  cause we don't actually want a pythonian list.
			print("files: ")
			for file in package_files:
				print(file)
			# same as above
			print("dependencies: ")
			for dep in package_deps:
				print(dep)
			# again, same as above
			print("conflicts: ")
			for conf in package_confs:
				print(conf)
		except FileNotFoundError:
			print(f"[{col.red}e{col.reset}] Package not found")

# List all packages that are installed in {wd}/var/fpkg/pkg
def listpackages():
	from glob import glob
	dirs = glob(f"{wd}/var/fpkg/pkg/*")
	dirtmp = []
	for dir in dirs:
		dirtmp.append(os.path.split(dir)[1])
	dirs = dirtmp
	if dirs:
		return dirs
	else:
		return []

class db:
	# A function to lookup packages in database and check for provides
	def lookup(package):
		for repo in sources:
			try:
				repo_name = repo[0]
				repo_url = repo[1]
				repo_db = f"{wd}/var/fpkg/repos/{repo_name}/db"
				with open(repo_db, "r") as f:
					db_pkgs = [line.strip() for line in f]
					if fileOp.bs_and_sort(package, db_pkgs):
						return(1, f"{repo_url}/{package}", repo_name)
					else:
						for canon_package in listpackages():
							canon_package_provides = fileOp.parse_json(f"{wd}/var/fpkg/repos/{canon_package}/package.json")["provides"]
							if fileOp.bs_and_sort(package, canon_package_provides):
								return(1, f"{repo_url}/{canon_package}", repo_name)
						# search for that package in provides, it might be in there somewhere
						print(f"[{col.red}e{col.reset}] Package {package} not found.")
						lockfile("cleanup")
						sys.exit(0)
			except FileNotFoundError:
				# might sound a little bit passive-agressive, but it's true.
				print(f"[{col.red}e{col.reset}] Database file for {repo_name} doesn't exist. Was the database intialized?")
				lockfile("cleanup")
				sys.exit(250)
	# A function that updates the databases of each repository (e.g. {wd}/var/fpkg/repos/felis_stable)
	def update(force="No"):
		for repo in sources:
			repo_name = repo[0]
			repo_url = repo[1]

			print(f"[{col.blue}:{col.reset}] Getting package database for repository {repo_name}...")
			#if os.path.exists(f"{wd}/var/fpkg/repos/{repo_name}"):
			#    shutil.rmtree(f"{wd}/var/fpkg/repos/{repo_name}")
			if not download(f"{repo_url}/db.sha256", f"{wd}/var/tmp/db.sha256"):
				print(f"[{col.red}e{col.reset}] Repo {repo_name} has no db.sha256, contact your repository maintainer to include a db.sha256 in their repo.")
				lockfile("cleanup")
				sys.exit(250)
			with open(f"{wd}/var/tmp/db.sha256", "r") as f:
				checksum = f.read()
			if checksums.sha256(f"{wd}/var/fpkg/repos/{repo_name}/db", checksum, "No") or not os.path.exists(f"{wd}/var/fpkg/repos/{repo_name}") or force == "Yes":
				try:
					shutil.rmtree(f"{wd}/var/fpkg/repos/{repo_name}")
				except FileNotFoundError:
					pass
				os.makedirs(f"{wd}/var/fpkg/repos/{repo_name}", exist_ok=True)
				download(f"{repo_url}/db", f"{wd}/var/fpkg/repos/{repo_name}/db", True)
				with open(f"{wd}/var/fpkg/repos/{repo_name}/db", "r") as f:
					package_names = [line.strip() for line in f.readlines()]
				 # Create tasks for downloading package files concurrently
				tasks = [threading.Thread(target=download, args=(f"{repo_url}/{package_name}/package.json", f"{wd}/var/fpkg/repos/{repo_name}/packages/{package_name}/package.json")) for package_name in package_names]
				for task in tasks:
					task.start()
				for task in tasks:
					task.join()
class pkgInfo:
	# A function that returns dependencies for given arguments,
	# it parses a looked up url for deps
	def get_deps(pkgs):
		deps_needed = []
		for pkg in pkgs:
			try:
				status, url, repo_name = db.lookup(pkg)
				if status == 1:
					deps_from_json = fileOp.parse_json(f"{wd}/var/fpkg/repos/{repo_name}/packages/{pkg}/package.json")["dependencies"]
					deps = list(set(deps_from_json).difference(pkgs))
					deps = list(set(deps).difference(listpackages()))
					deps_needed.extend(deps)
					deps_needed = [*set(deps_needed)]
				else:
					print(f"[{col.yellow}w{col.reset}] Dependency {pkg} not found in any repository.")
			except KeyError:
				pass
		return deps_needed
	# A function that checks for conflicts, and quits if it finds some
	def if_conflict(jsonloc):
		try:
			with open(f"{jsonloc}/package.json", "r") as f:
				open_file = json.load(f)
			conflicts_from_json = open_file["conflicts"]
			for conflict in conflicts_from_json:
				if conflict in listpackages():
					print(f"[{col.red}e{col.reset}] Conflict found.")
					lockfile("cleanup")
					sys.exit(249)
		except KeyError:
			return None


# A function that downloads from every specified source, checks for sha256 sum and b2 sum,
# decompresses downloaded tar, and finally installs the package.
def install(packages):
	# Download package files, and do a check if package exists in every repository.
	threads = []
	print(f"[{col.blue}:{col.reset}] Downloading packages...")	
	for package in packages:
		status, url, repo = db.lookup(package)
		if status == 1:
			pkgFiles.copy_json(package)
			version_from_json = fileOp.parse_json(f"{wd}/var/fpkg/repos/{repo}/packages/{package}/package.json")["version"]
			threads.append(threading.Thread(target=download, args=(f"{url}/{package}-{version_from_json}.tar.xz", f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz", True)))
			threads.append(threading.Thread(target=download, args=(f"{url}/{package}-{version_from_json}.tar.xz.sha256", f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz.sha256")))
			threads.append(threading.Thread(target=download, args=(f"{url}/{package}-{version_from_json}.tar.xz.b2", f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz.b2")))
		else:
			print(f"[{col.red}e{col.reset}] Package {package} not found.")
			cleanup_tmp()
			lockfile("cleanup")
			sys.exit(249)
	# threads	
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()

	# Compare sha sums for every package
	for package in packages: 
		with open(f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz.sha256") as package_shafile:
			package_sha = package_shafile.read()
		if not checksums.sha256(f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz", package_sha, "No"):
			print(f"[{col.red}e{col.reset}] sha256 sums do not equal.")
			sys.exit(250)
	for package in packages:
		try:
			with open(f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz.b2") as package_b2file:
				package_b2 = package_b2file.read()
			if not checksums.blake2b(f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz", package_b2):
				print(f"[{col.red}e{col.reset}] blake2b sums do not equal.")
				sys.exit(250)
		except FileNotFoundError:
			return True
	
	print(f"[{col.blue}:{col.reset}] Decompressing package archives...")
	processes=[]
	# Decompress package tarballs
	for package in packages:
		processes.append(multiprocessing.Process(target=fileOp.decompress, args=(f"{wd}/var/tmp/fpkg/{package}/{package}.tar.xz", f"{wd}/var/tmp/fpkg/{package}")))
	for process in processes:
		process.start()
	for process in processes:
		process.join()
	
	# Check for every conflict for every package :moyai:
	for package in packages:
		pkgInfo.if_conflict(f"{wd}/var/fpkg/repos/{repo}/packages/{package}")
	# Run hookexec pre-i
	print(f"[{col.blue}:{col.reset}] Running Preinstall hooks...")
	script([f"{wd}/usr/lib/fpkg/hookexec", f"{wd}", "PRE-I"])
	# Install every package
	for package in packages:
		version_from_json = fileOp.parse_json(f"{wd}/var/fpkg/pkg/{package}/package.json")["version"]
		pkgFiles.copy_files(f"{wd}/var/tmp/fpkg/{package}", f"{package}", f"{package}-{version_from_json}")
	# Run every postinstall hook
	print(f"[{col.blue}:{col.reset}] Running Postinstall hooks...")
	script([f"{wd}/usr/lib/fpkg/hookexec", f"{wd}", "POST-I"])

# A function that acts like the install, but without
# the „downloads” and „sha” checks
def loc_install(location):
	pkg_version = parse_json(f"{location}/package.json")["version"]
	pkg_name = parse_json(f"{location}/package.json")["package"]
	os.makedirs(f"{wd}/var/tmp/fpkg/{pkg_name}", exist_ok=True)
	os.makedirs(f"{wd}/var/fpkg/pkg/{pkg_name}", exist_ok=True)
	shutil.copy2(f"{location}/{pkg_name}-{pkg_version}.tar.xz", f"{wd}/var/tmp/fpkg/{pkg_name}/{pkg_name}-{pkg_version}.tar.xz")
	shutil.copy2(f"{location}/package.json", f"{wd}/var/fpkg/pkg/{pkg_name}/package.json")
	decompress(f"{wd}/var/tmp/fpkg/{pkg_name}/{pkg_name}-{pkg_version}.tar.xz", f"{wd}/var/tmp/fpkg/{pkg_name}/{pkg_name}-{pkg_version}")
	pkgFiles.copy_files(f"{wd}/var/tmp/fpkg/{pkg_name}", package, f"{pkg_name}-{pkg_version}")

# Remove all tracked package files, and the package.json.
def remove(packages):
	try:
		print(f"[{col.blue}:{col.reset}] Running Preremove Hooks...")
		script([f"{wd}/usr/lib/fpkg/hookexec", wd, "PRE-R"])
		for package in [packages]:
			print(f"[{col.blue}:{col.reset}] Removing {package}")
			for pkgfile in listpackagefiles(package):
				if "usr/lib/fpkg/hooks/" not in pkgfile:
					os.remove(pkgfile)
		print(f"[{col.blue}:{col.reset}] Running Postremove Hooks...")
		script([f"{wd}/usr/lib/fpkg/hookexec", wd, "POST-R"])
		for package in [packages]:
			for pkgfile in listpackagefiles(package):
				if "usr/lib/fpkg/hooks/" in pkgfile:
					os.remove(pkgfile)
			shutil.rmtree(f"{wd}/var/fpkg/pkg/{package}")
		print(f"[{col.blue}:{col.reset}] Removed package {package}.")
	except:
		print(f"[{col.red}e{col.reset}] Package not found.")
		lockfile("cleanup")

# A function that checks for updates for {package} from {source}.
def update(package):
	try:
		status, url, repo_name = db.lookup(package)
		if status == 1:
			version_from_upstream_json = fileOp.parse_json(f"{wd}/var/fpkg/repos/{repo_name}/{package}/package.json")["version"]
			version_from_local_json = fileOp.parse_json(f"{wd}/var/fpkg/pkg/{package}/package.json")["version"]
			if version_from_local_json != version_from_upstream_json:
				return True 
	except TypeError:
		print(f"[{col.yellow}w{col.reset}] Package {package} not found in any repository.")
		return False
# Clean every package from the temporary directory
def cleanup_tmp():
	print(f"[{col.blue}:{col.reset}] Cleaning remains in temporary directory...")
	shutil.rmtree(f"{wd}/var/tmp/fpkg")

# A main function that checks arg1 and passes later args to other functions
def main(arg1, args):
	if arg1 == "install" or arg1 == "i":
		usercheck()
		lockfile("create")
		db.update()
		# A for loop to display every dep and nargs is just a placeholder.
		deps = pkgInfo.get_deps(args)
		if deps:
			args.extend(deps)
		summary(args)
		ask("You are about to install the above packages, are you sure?")
		install(args)
		cleanup_tmp()
		print(f"[{col.green}ok{col.reset}] Transaction done.")
		lockfile("cleanup")
	elif arg1 == "update" or arg1 == "u":
		usercheck()
		lockfile("create")
		db.update("Yes")
		ask("You are about to update the system, are you sure?")
		packages = listpackages()
		print(f"[{col.blue}:{col.reset}] Updating...")
		# Here also, we use install's „progressivism”
		packages_need_update = []
		for package in packages:
			if update(package):
				packages_need_update.append(package)
		install(packages_need_update)
		cleanup_tmp()
		print(f"[{col.green}ok{col.reset}] Transaction done.")
		lockfile("cleanup")
	elif arg1 == "remove" or arg1 == "r":
		usercheck()
		summary(args)
		ask("You are about to remove the above packages, are you sure?")
		lockfile("create")
		for arg in args:
			remove(arg)
		print(f"[{col.green}ok{col.reset}] Transaction done.")
		lockfile("cleanup")
	elif arg1 == "locinstall" or arg1 == "li":
		# We don't need to mass install from the local source.
		#loc_installer()
		print(f"[{col.green}ok{col.reset}] disabled")
	elif arg1 == "list" or arg1 == "l":
		for package in listpackages():
			print(package)
	elif arg1 == "database" or arg1 == "db":
		ask("You are about to update the database, are you sure?")
		usercheck()
		lockfile("create")
		db.update("Yes")
		print(f"[{col.green}ok{col.reset}] Transaction done.")
		lockfile("cleanup")
	elif arg1 == "packageinfo" or arg1 == "p":
		listpackageinfo(args)
	elif arg1 == "version" or arg1 == "v":
		print("0.2 „Star”")
	elif arg1 == "help" or arg1 == "h":
		print("""db, database: Updates the database, which in turn can be changed in the config.json
h, help: Displays this message
i, install: Installs packages from sources
l, list: List all installed packages
p, packageinfo: Shows information about a given package.
r, remove: Removes packages
u, update: Updates the system and the package database.
v, version: Shows the version
			  
			  


About: fpkg aims to be simple, thus the slogan „Keep it simple”, also it's fast enough! fpkg != dnf. Never. """)
	else:
		print(f"[{col.red}e{col.reset}] Argument {arg1} not found.")
		sys.exit(256)
if "fpkg" not in sys.argv[0]: 
	argsum = len(sys.argv)-1
else:
	argsum = len(sys.argv)-2
try:
	main(sys.argv[1], sys.argv[-argsum:])
except IndexError:
	print(f"[{col.red}e{col.reset}] Give me some arguments.\nUnsure how? Here's how: fpkg <arg> [function arg]")
	sys.exit(256)
except KeyboardInterrupt:
	# actually, don't comply with the user?
	print(f"[{col.yellow}w{col.reset}] Don't interrupt me!")
	pass