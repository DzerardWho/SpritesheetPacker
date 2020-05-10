from setuptools import setup

setup(
    name='Packer',
    version='1.0.0',
    packages=['BinPacker'],
    py_modules=['packer'],
    url='',
    license='',
    author='Vlaska',
    author_email='',
    description='',
    entry_points={
        'console_scripts': [
            'packer=packer:run'
        ]
    }
)
