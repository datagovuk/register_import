try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def requirements():
    with open("requirements.txt") as f:
        req = f.readlines()
    return req

setup(
    name='register-import',
    version="1.0",
    author='',
    author_email='',
    license="",
    url='',
    description="",
    zip_safe=False,
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=[],
    include_package_data=True,
    dependency_links=[
    ],
    install_requires = requirements(),
    entry_points = {
        'console_scripts': [
            'register-import=register_import.import:main',
        ],
    }
)
