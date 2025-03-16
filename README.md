# Insurance Web Scraper

A web scraping system designed to extract dental insurance guidelines from various carriers including Aetna, Cigna, MetLife, and UnitedHealthcare.

## System Requirements

- Python 3.11+
- Docker (optional for containerized deployment)
- Docker Compose (optional for containerized deployment)
- At least 4GB RAM available
- At least 10GB disk space

## Project Structure

```
.
├── src/                    # Source code
│   ├── spiders/           # Spider implementations for each carrier
│   ├── scrapers/          # Base scraping functionality
│   ├── models/            # Data models and validation
│   ├── middlewares/       # Request middleware (rate limiting, etc.)
│   ├── utils/             # Utility functions and helpers
│   ├── main.py           # Main entry point
│   ├── exceptions.py     # Custom exceptions
│   └── pdf_processor.py  # PDF processing functionality
├── tests/                 # Test suite
│   └── spiders/          # Spider-specific tests
├── config/               # Configuration files
│   └── requirements.txt  # Project dependencies
├── data/                 # Data storage
│   ├── raw/             # Raw downloaded PDFs
│   └── processed/       # Processed data files
├── logs/                 # Application logs
└── cache/               # Cache storage
```

## Local Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r config/requirements.txt
   ```

## Docker Deployment

The system uses the following services when deployed with Docker:

- **Scraper Service**: Python 3.11-based web scraper
- **MongoDB**: Document storage for structured data
- **Qdrant**: Vector database for semantic search
- **Rotating Proxy**: TOR-based proxy rotation system

### Environment Variables

- `MONGO_URI`: MongoDB connection string
- `QDRANT_HOST`: Qdrant service hostname
- `QDRANT_PORT`: Qdrant service port
- `TOR_PROXY`: TOR proxy connection string

### Docker Setup

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. Monitor the logs:
   ```bash
   docker-compose logs -f scraper
   ```

## Usage

### Local Development
```bash
python src/main.py
```

### Testing

Run tests with pytest:
```bash
pytest tests/
```

## Resource Management

### Docker Resource Limits
- Scraper Service: 2GB RAM, 2 CPU cores
- MongoDB: Uses default resource allocation
- Qdrant: Uses default resource allocation
- TOR Proxy: Uses default resource allocation

### Network Configuration
- Custom DNS servers: 8.8.8.8, 8.8.4.4
- Bridge network mode for service isolation
- TOR proxy with 5 instances and 60-second rotation

## Maintenance

- Logs are stored in the `logs` directory
- PDFs are stored in the `data/raw` directory
- Extracted data is stored in the `data/processed` directory
- Cache is stored in the `cache` directory

## Troubleshooting

1. If the scraper service fails to start:
   - Check if all required directories exist
   - Verify MongoDB and Qdrant services are running (if using Docker)
   - Check the logs for specific error messages

2. If proxy rotation isn't working:
   - Verify TOR service is running
   - Check TOR logs for connection issues
   - Ensure proxy settings are correctly configured

3. For memory issues:
   - Monitor container resource usage
   - Adjust memory limits in docker-compose.yml
   - Clear cache directory if needed

## Contributing

1. Create a new branch for your feature
2. Write tests for new functionality
3. Submit a pull request

## License

MIT License

Copyright (c) 2024 AojdevStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
