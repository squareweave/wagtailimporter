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
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],
        packages=find_packages(),
        include_package_data=True,
        install_requires=requirements.readlines(),
        setup_requires=[
            'setuptools_scm',
        ],
    )
