from setuptools import setup

setup(
    name="locr",
    version="1.2.0",
    py_modules=["locr", "locr_config"],
    install_requires=[],  # Add dependencies here if need to add external libs later
    entry_points={
        "console_scripts": [
            "locr=locr:main",  # Command=File:Function
        ],
    },
)
