import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='redssh',
    version='0.0.1',
    url='',
    license='GPLv2',
    author='Red_M',
    author_email='redssh_pypi@red-m.net',
    description='An SSH automation library.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    platforms='Posix',
    install_requires=[
        'paramiko_expect',
        'paramiko',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers'
    ],
)