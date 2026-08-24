import re

from setuptools import setup


def _read_version():
    with open('django_zero_downtime_migrations/__init__.py') as init_handle:
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)', init_handle.read(), re.MULTILINE)
    if not match:
        raise RuntimeError('Could not find __version__ in django_zero_downtime_migrations/__init__.py')
    return match.group(1)


VERSION = _read_version()


def _replace_internal_images_with_external(text):
    return text.replace(
        '(images/',
        '(https://raw.githubusercontent.com/tbicr/django-pg-zero-downtime-migrations/'
        '{VERSION}/images/'.format(VERSION=VERSION),
    )


def _get_long_description():
    with open('README.md') as readme_handle:
        readme = readme_handle.read()
    with open('CHANGES.md') as changes_handle:
        changes = changes_handle.read()
    return _replace_internal_images_with_external(readme) + '\n\n' + changes


setup(
    long_description=_get_long_description(),
    long_description_content_type='text/markdown',
)
