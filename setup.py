# -*- coding: utf-8 -*-
#!/usr/bin/env python
#

from setuptools import setup, find_packages
import pathlib

try:
	from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
	class bdist_wheel(_bdist_wheel):
		def finalize_options(self):
			_bdist_wheel.finalize_options(self)
			self.root_is_pure = False
except ImportError:
	bdist_wheel = None

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
	name="arch14cz_backend",
	version="1.0.1",
	description="Backend interface for Arch14CZ - the database of archaeological radiocarbon dates of the Czech Republic",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/demjanp/arch14cz_backend",
	author="Peter Demján",
	author_email="peter.demjan@gmail.com",
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Science/Research",
		"Topic :: Database",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Programming Language :: Python :: 3.10",
		"Operating System :: Microsoft :: Windows :: Windows 10",
	],
	keywords="database, archaeology, radiocarbon, chronology, Czech",
	package_dir={"": "src"},
	packages=find_packages(where="src"),
	python_requires=">=3.10, <4",
	install_requires=[
		'deposit_gui>=1.4.38, <1.5',
		'numpy>=1.24.1',
		'scipy>=1.10.0, <2',
		'matplotlib>=3.7.0, <4',
	],
	cmdclass={'bdist_wheel': bdist_wheel},
)
