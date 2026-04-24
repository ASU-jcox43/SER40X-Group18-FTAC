# MongoDB

## About
The MongoDB module provides access to different collections within the CapstoneDB database.
Each file in this module is responsible for interacting with a specific collection, allowing the application to store, retrieve, and update structured data.
## Supported Filetype

-JSON

## Requirements

- A running MongoDB database instance
- Libraries
  - pymongo (MongoDB client)

Run pip install for each library for use

```
pip install pymongo
```

### Optional Installations
Install MongoDB Compass for easy database management.

1. Install MongoDB Compass

2. Connect to local database server

```
mongodb://localhost:27017
```

## Usage

No direct user interaction is required.
The MongoDB collections are accessed automatically by other modules in the system as needed.

Ensure that:

- The MongoDB service is running
- Connection settings (URI, database name) are correctly configured in your project