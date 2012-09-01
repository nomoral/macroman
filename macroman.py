#!/usr/bin/python


# macroman, a build tool for HTML5 apps
#   Copyright (C) 2012  Irae Hueck Costa
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA







import sys
import os
import shlex
import subprocess
import re
import tempfile
import shutil
from pprint import pprint


try:
	target_dir = sys.argv[1]
except IndexError, exc:
	target_dir = "."
	
target_dir = os.path.realpath(target_dir)
config_file = os.path.join(target_dir, 'config.macroman')
source_dir = os.path.join(target_dir, 'source')




def error(stri):
	print stri
	sys.exit(1)

def info(stri):
	print stri


def chomp_slash(stri):
	return stri if not stri.startswith("/") else stri[1:]

def split(stri, mark, max=None):
	if max:
		spli = stri.split(mark, max)
	else:
		spli = stri.split(mark)

	return [i.strip() for i in spli]


def get_boolean(config, key, default=False):
	if not key in config['values']:
		return default
	val = config['values'][key]
	try:
		return {'yes': True, 'no': False}[val]
	except KeyError:
		error("unknown boolean for key {key}. it should be 'yes' or 'no' and not: {val}".format(key=key, val=val))



def parse_config(config_file):

	try:
		fobj = open(config_file)
	except OSError, exc:
		error("could not open config file: " + str(exc))


	parsed = {'values': {}, 'rewrites': []}
	for counter, line in enumerate(fobj.readlines()):
		counter += 1

		# its a comment
		if '#' in line:
			line = line.split('#', 1)[0]

		if not line.strip():
			continue


		if '::' in line:
			key, value = split(line, '::', 1)
			if not key:
				key = shlex.split(value)[0]
			parsed['values'][key] = value
			continue


		if not '=>' in line:
				error("syntax error: unrecognized line at line {}".format(counter))

		if line.count('=>') > 1:
			error("syntax error: found more than one '=>' at line {}".format(counter))

		left, rename_to = split(line, '=>', 1)

		#if not left.count('->'):
		#	error("syntax error: you need at least one '->' before => at line {}".format(counter))

		lefts = split(left, '->')
		target, macros = lefts[0], lefts[1:]

		target_base, target_ext = os.path.splitext(target)
		rename_to = rename_to.format(
			base=target_base,
			ext=target_ext[1:],
			file=os.path.basename(target),
			path=os.path.dirname(target))


		if target.count("*") != rename_to.count('*'):
			error("syntax error: target template and rename template do not have the same number of of '*'")

		parsed['rewrites'].append((target, macros, rename_to))

	return parsed




def transform(from_, to, value):
	if from_.count("*") != to.count('*'):
		raise ValueError("from and to do not have the same value of '*'")

	pattern = re.escape(from_).replace(re.escape("*"), '(.*)')

	replace = []
	parts = re.escape(to).split(re.escape('*'))
	c = 0
	while True:
		c += 1
		part = parts.pop(0)
		replace.append(part)
		if parts:
			replace.append('\\' + str(c))
		else:
			break
	replace = ''.join(replace)

	#print pattern, replace, value
	stri, replaces = re.subn('^'+pattern+'$', replace, value)
	if replaces:
		return stri.replace('\\', '')
	return False



def get_compile_info(web_file, config):
	for (target, macros, rewrite_to) in config['rewrites']:
		if not os.path.isabs(rewrite_to):
			rewrite_to = os.path.join(os.path.dirname(target), rewrite_to)
		rewritten = transform(target, rewrite_to, web_file)
		if rewritten:
			return rewritten, macros
	return web_file, []





def get_build_info(source, config):
	source2compiled = {}
	compiled2source = {}
	for root, dirs, files in os.walk(source, topdown=False):
		for file in files:
			abs_file = os.path.join(root, file)
			web_file = abs_file[len(source):]
			compiled_file, macros = get_compile_info(web_file, config)
			
			source2compiled[web_file] = (compiled_file, macros)
			if compiled_file in compiled2source:
				error('at least two macros have the same output file (macro1: "{0}", macro2: {1}, out: "{2}").'.format(
					compiled2source[compiled_file][0], web_file, compiled_file))
			compiled2source[compiled_file] = (web_file, macros)

	
	return source2compiled, compiled2source



def apply_macro(file_path, macro, config):
	print "applying macro {macro} for file {file}" \
		.format(macro=macro, file=file_path)


	if not get_boolean(config, macro + '.copy', True):
		build_dir = os.path.dirname(file_path)
		build_file = file_path

	else:
		build_dir = tempfile.mkdtemp()
		build_file = os.path.join(build_dir, os.path.basename(file_path))
		shutil.copy(file_path, build_dir)

	tmpdir = tempfile.mkdtemp()
	
	cmd = config['values'].get(macro)
	if cmd is None:
		error("no such macro: " + macro)
	cmd = cmd.format(
		file=build_file,
		pwd=build_dir,
		bin=os.path.join(target_dir, 'bin'),
		tmpdir=tmpdir)

	print "executing: " + cmd
	p = subprocess.Popen(shlex.split(cmd),
			cwd=build_dir,
			stdout=sys.stdout,
			stderr=sys.stderr)
	
	code = p.wait()
	print "exited with code " + str(code)
	if code == 1:
		error("exit code was 1")
	

	outfile = config['values'].get(macro + '.outfile')
	if outfile:
		outfile = outfile.format(
			file=build_file,
			base=os.path.splitext(build_file)[0],
			filebase=os.path.splitext(os.path.basename(build_file))[0],
			pwd=build_dir,
			pid=p.pid,
			tmpdir=tmpdir)
			#temp=tempfile.mkdtemp()) # do we *always* need this?
		
		if not os.path.abspath(outfile):
			outfile = os.path.join(build_dir, outfile)

	else:
		# try to find out the outfile
		files = set(os.path.join(build_dir, i) for i in os.listdir(build_dir)) - set([build_file])
		if not files:
			error("no new files on build dir ({0}) after command".format(build_dir))
		if len(files) > 1:
			error("there were more than one files generated on the build dir {0}. dunno which one to take".format(build_dir))
		outfile = next(iter(files))
	
	if not os.path.exists(outfile):
		raise ValueError("specified output could not be found ({0})".format(outfile))

	return outfile


def apply_macros(file_path, macros, config):

	for macro in macros:

		if not macro in config['values']:
			info("no macro defined: {macro}".format(macro=macro))
			start_response('503 no such macro found', []) # hier werte die sinn machen eintragen
			return ["no such macro: " + macro]

		file_path = apply_macro(file_path, macro, config)

	return file_path



class Cache:
	def __init__(self):
		self._cache = {}

	def set(self, src_file, dst_file):
		self._cache[src_file] = (dst_file, os.path.getmtime(src_file))

	def get(self, src_file):
		entry = self._cache.get(src_file)
		if not entry:
			return None
		dst_file, mtime = entry
		if os.path.getmtime(src_file) > mtime:
			return None
		return dst_file
cache = Cache()




def wsgi(env, start_response):
	
	default_headers = [("Cache-Control", "no-cache")]
	
	config = parse_config(config_file)
	source2compiled, compiled2source = get_build_info(source_dir, config)
	
	#print config
	#
	#print
	#print
	#print
	
	#pprint(compiled2source)

	request_path = env["PATH_INFO"]

	info('')

	try:
		macro_file, macros = compiled2source[request_path]
	except KeyError:
		start_response('404 Not Found', default_headers)
		return ["file not found in compiled2source"]

	abs_macro_file = os.path.join(source_dir, chomp_slash(macro_file))

	compiled_file = cache.get(abs_macro_file)
	if not compiled_file:
		info("got request (*not* serving from cache): " + request_path)
		compiled_file = apply_macros(abs_macro_file, macros, config)
		cache.set(abs_macro_file, compiled_file)
	else:
		info("got request (serving from cache): " + request_path)




	start_response("200 OK", default_headers)
	return open(compiled_file)


#from pprint import pprint
#config = parse_config(config_file)
#pprint (get_build_info(source_dir, config))


def main():
	from wsgiref.simple_server import make_server
	httpd = make_server('', 1337, wsgi)
	print "Serving on port 1337..."
	httpd.serve_forever()




if __name__ == '__main__':
	main()
































