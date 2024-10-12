#!/usr/bin/env python

import toml
import os


def increment_version(pyproject_file):
	with open(pyproject_file, 'r') as f:
		data = toml.load(f)

	current_version: str = data['project']['version']
	version_parts = current_version.split('.')
	version_parts[-1] = str(int(version_parts[-1]) + 1)  # Increment build number
	new_version = '.'.join(version_parts)

	data['project']['version'] = new_version

	with open(pyproject_file, 'w') as f:
		toml.dump(data, f)

	print(f'Incremented version in pyproject.toml to: {new_version}')


if __name__ == '__main__':
	pyproject_file = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
	increment_version(pyproject_file)
