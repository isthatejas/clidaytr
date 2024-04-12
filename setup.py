from setuptools import setup
import os

setup(
    name="clidaytr",
    version='0.0.0',
    description="Simple CLI-based Kanban Board",
    py_modules=['clidaytr'],
    install_requires=[
        'click',
        'click-default-group',
        'pyyaml',
        'rich'
    ],
    entry_points='''
        [console_scripts]
        clidaytr=clidaytr:clidaytr
        dayt=clidaytr:clidaytr
        dt=clidaytr:clidaytr
    '''
    #call using clikanban = from clikanban package and is function supercli
)