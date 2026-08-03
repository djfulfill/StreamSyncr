from setuptools import setup, find_packages

setup(
    name="wetrakr-api",
    version="0.1.0",
    description="Unofficial WeTrakr API client (reverse-engineered)",
    packages=find_packages(),
    py_modules=["client", "mark_watched"],
    install_requires=["requests>=2.28.0"],
    python_requires=">=3.8",
    author="user",
    license="MIT",
)
