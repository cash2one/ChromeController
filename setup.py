
import setuptools
from distutils.core import setup
import sys
import time
setup(
	# Application name:
	name="ChromeController",

	# Version number (initial):
	version="0.0.2",

	# Application author details:
	author="Connor Wolf	",
	author_email="github@imaginaryindustries.com",

	# Packages
	packages=["ChromeController"],
	package_dir = {'ChromeController': 'ChromeController'},
	package_data={'ChromeController': ['protocols/*.json']},

	# Details
	url="https://github.com/fake-name/ChromeController",

	#
	# license="LICENSE.txt",
	description="Chrome Remote Debugger interface.",

	long_description=open("README.md").read(),
	dependency_links=[
		'https://github.com/berkerpeksag/astor/tarball/master#egg=lol_%s_wat' % int(time.time()),
	],
	# Dependent packages (distributions)
	install_requires=[
		'websocket-client',
		'requests',
	],
)
