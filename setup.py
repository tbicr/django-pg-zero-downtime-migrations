from setuptools import find_packages, setup

setup(
    name='django-pg-zero-downtime-migrations',
    version='0.4',
    author='Paveł Tyślacki',
    author_email='pavel.tyslacki@gmail.com',
    license='MIT',
    url='https://github.com/tbicr/django-pg-zero-downtime-migrations',
    description='Django postgresql backend that apply migrations with respect to database locks',
    long_description=open('README.md').read() + '\n\n' + open('CHANGES.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
    ],
    keywords='django postgres postgresql migrations',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.5',
    install_requires=[
        'django>=2.0',
    ]
)
