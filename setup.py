from setuptools import setup

readme = open('README.rst').read()


setup_params = dict(
    name='MgoQuery',
    version='0.5.5',
    url='https://bitbucket.org/elarson/mgoquery',
    author='Eric Larson',
    author_email='eric@ionrock.org',
    py_modules=['mgoquery'],
    description='A concise language parser for creating MongoDB queries',
    long_description=readme,
    install_requires=[
        'pyparsing>=2.0.2'
    ],
)


if __name__ == '__main__':
    setup(**setup_params)
