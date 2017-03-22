from setuptools import setup

setup(
    name='leanix-admin',
    url='https://github.com/zalando-incubator/leanix-admin',
    version='0.1.0',
    author='Team TORCH',
    author_email='team-torch@zalando.de',
    description='Command-line tool to manage LeanIX administration',
    keywords='leanix',
    license='MIT',
    packages=['leanix_admin'],
    include_package_data=True,
    install_requires=[
        'requests',
        'click'
    ],
    entry_points='''
    [console_scripts]
    leanix-admin=leanix_admin:main
    '''
)
