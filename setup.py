"""
setuptools configuration for wagtailimporter.
"""

from setuptools import find_packages, setup

with open('README.rst') as readme, \
     open('requirements.txt') as requirements:
    setup(
        name="wagtailimporter",
        use_scm_version=True,
        description="Wagtail module to load pages from Yaml",
        long_description=readme.read(),
        url='https://github.com/squareweave/wagtailimporter',
        author='Squareweave',
        author_email='team@squareweave.com.au',
        license='BSD',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            'Framework :: Django :: 3.2',
            'Framework :: Django :: 4',
            'Framework :: Django :: 4.0',
            'Framework :: Django :: 4.1',
            'Framework :: Django :: 4.2',
            'Framework :: Django :: 5.0',
            'Framework :: Wagtail',
            'Framework :: Wagtail :: 4',
            'Framework :: Wagtail :: 5',
            'Framework :: Wagtail :: 6',
        ],
        packages=find_packages(),
        include_package_data=True,
        install_requires=requirements.readlines(),
        setup_requires=[
            'setuptools_scm',
        ],
    )
