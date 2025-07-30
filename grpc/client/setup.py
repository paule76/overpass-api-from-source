from setuptools import setup, find_packages

setup(
    name="overpass-grpc-client",
    version="0.1.0",
    description="High-performance gRPC client for Overpass API",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "grpcio>=1.59.0",
        "protobuf>=4.24.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)