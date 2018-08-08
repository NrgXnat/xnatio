import setuptools

with open ("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(name='xnatio',
      version='0.1.0',
      description='A library for gathering data from the XNAT database',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/AidanKelley/xnatio',
      author='Aidan Kelley',
      author_email='aidankelley@wustl.edu',
      license='XNAT',
      packages=setuptools.find_packages(),
      install_requires=[
          'msgpack',
          'grequests',
          'requests',
          'python-dateutil',
          'matplotlib',
          'ipywidgets',
      ],
      zip_safe=False)