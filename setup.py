from setuptools import setup, find_packages

setup(
    name="sequencer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],  # Add any dependencies your package needs
    author="Mahmoud Badawy",
    author_email="mahmoud1816yasser@gmail.com",
    description="GUI sequencer for controlling the hardware of the lab using the ADwin system.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Mahmoud-Yasser-18/BEC-Sequencer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
