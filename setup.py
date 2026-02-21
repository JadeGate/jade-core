from setuptools import setup, find_packages

setup(
    name="jadegate",
    version="1.0.0",
    description="Deterministic security protocol for AI agent skills",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="JadeGate",
    url="https://github.com/JadeGate/jade-core",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "jade_core": ["../jade_schema/*.json"],
        "": ["jade_skills/**/*.json"],
    },
    entry_points={
        "console_scripts": [
            "jade=jade_cli:main",
        ],
    },
    python_requires=">=3.8",
    install_requires=[],  # Zero dependencies!
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries",
    ],
)
