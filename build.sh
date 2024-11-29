#!/bin/bash

# Update the package list
apt-get update -y

# Install essential tools
apt-get install -y apt-transport-https curl gnupg2 software-properties-common

# Add Microsoft's repository for the ODBC driver
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update the package list again
apt-get update -y

# Install Microsoft ODBC Driver for SQL Server
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# Clean up unnecessary files to reduce image size
apt-get clean
