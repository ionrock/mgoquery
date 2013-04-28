from setuptools import setup


setup_params = dict(
    name='MgoQuery',
    author='Eric Larson',
    author_email='eric@ionrock.org',
    py_modules=['mgoquery'],
    use_hg_version=dict(increment='0.1'),
    install_requires=[
        'pyparsing==1.5.7'
    ],
    setup_requires=[
        'hgtools>=1.0',
    ],
)


if __name__ == '__main__':
    setup(**setup_params)
