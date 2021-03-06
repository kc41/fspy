import os
import setuptools


class CleanCommand(setuptools.Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    # noinspection PyMethodMayBeStatic
    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')


setuptools.setup(
    name="fspy",

    python_requires="==3.6.*",

    use_scm_version=True,

    author="Konstantin Chupin",
    author_email="kchupin41@gmail.com",
    description="File System Spy",

    setup_requires=[
        "setuptools_scm"
    ],

    install_requires=[
        "pytz",
        "tzlocal",
        "pydantic==0.13",
        "janus==0.4.0",
        "aiohttp==3.4.1",
        "SQLAlchemy==1.2.11",
    ],

    packages=setuptools.find_packages(exclude=("tests",)),

    classifiers=['Private :: Do Not Upload'],

    cmdclass={
        'clean': CleanCommand,
    }
)
