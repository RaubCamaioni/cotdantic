import nox


@nox.session(python=['3.8', '3.9', '3.10', '3.11'])
def tests(session):
	"""Run the test suite."""
	session.install('.')
	session.install('pytest')
	session.run('pytest')
