from setuptools import find_packages, setup

VERSION = __import__('django_zero_downtime_migrations').__version__


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
    name='django-pg-zero-downtime-migrations',
    version=VERSION,
    author='Paveł Tyślacki',
    author_email='pavel.tyslacki@gmail.com',
    license='MIT',
    url='https://github.com/tbicr/django-pg-zero-downtime-migrations',
    description='Django postgresql backend that apply migrations with respect to database locks',
    long_description=_get_long_description(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
    ],
    keywords='django postgres postgresql migrations',
    packages=find_packages(exclude=['manage*', 'tests*']),
    python_requires='>=3.6',
    install_requires=[
        'django>=3.2',
    ]
)
