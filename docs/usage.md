# Usage Guide

This guide provides examples and common usage scenarios for the Dental Insurance Guidelines Web Scraper.

## Basic Usage

### Running the Scraper

1. Scrape a single carrier:
   ```bash
   python -m scraper run --carrier aetna
   ```

2. Scrape multiple carriers:
   ```bash
   python -m scraper run --carrier aetna,cigna,metlife
   ```

3. Scrape all carriers:
   ```bash
   python -m scraper run --all
   ```

### Output Options

1. Change output format:
   ```bash
   python -m scraper run --carrier aetna --format json
   python -m scraper run --carrier aetna --format csv
   ```

2. Specify output directory:
   ```bash
   python -m scraper run --carrier aetna --output ./my_data
   ```

3. Enable compression:
   ```bash
   python -m scraper run --carrier aetna --compress
   ```

## Common Scenarios

### 1. Full Data Collection

Collect data from all carriers with maximum reliability:

```bash
python -m scraper run --all \
                     --retries 5 \
                     --delay 60 \
                     --validate \
                     --backup
```

### 2. Incremental Updates

Update only changed guidelines:

```bash
python -m scraper run --all \
                     --incremental \
                     --since "2024-01-01"
```

### 3. PDF Processing

Extract text from downloaded PDFs:

```bash
python -m scraper process-pdfs \
                     --input ./pdfs \
                     --output ./extracted
```

### 4. Data Validation

Validate extracted data:

```bash
python -m scraper validate \
                     --input ./data \
                     --schema ./schemas/guidelines.json
```

## Advanced Usage

### Custom Extraction Rules

1. Create a custom extraction rule:
   ```yaml
   # rules/custom.yaml
   extraction_rules:
     procedure_code:
       pattern: "D\\d{4}"
       required: true
     requirements:
       pattern: "Requirements:.*?(?=\\n\\n)"
       multiline: true
   ```

2. Apply custom rules:
   ```bash
   python -m scraper run --carrier aetna --rules rules/custom.yaml
   ```

### Proxy Configuration

1. Use rotating proxies:
   ```bash
   python -m scraper run --carrier aetna \
                        --use-proxy \
                        --proxy-rotate 60
   ```

2. Use specific proxy:
   ```bash
   python -m scraper run --carrier aetna \
                        --proxy http://proxy.example.com:8080
   ```

### Error Handling

1. Configure retry behavior:
   ```bash
   python -m scraper run --carrier aetna \
                        --max-retries 5 \
                        --retry-delay 30 \
                        --timeout 60
   ```

2. Enable error alerts:
   ```bash
   python -m scraper run --carrier aetna \
                        --alert-on-error \
                        --alert-email admin@example.com
   ```

## Batch Processing

### 1. Queue-based Processing

Process carriers in a queue:

```bash
# Start the queue worker
python -m scraper worker start

# Add jobs to the queue
python -m scraper queue add --carrier aetna
python -m scraper queue add --carrier cigna

# Monitor progress
python -m scraper queue status
```

### 2. Scheduled Runs

Set up scheduled runs using cron:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/venv/bin/python -m scraper run --all --quiet

# Run weekly on Sunday
0 0 * * 0 /path/to/venv/bin/python -m scraper run --all --backup
```

## Monitoring and Logging

### 1. Enhanced Logging

Enable detailed logging:

```bash
python -m scraper run --carrier aetna \
                     --log-level DEBUG \
                     --log-file scraper.log
```

### 2. Progress Monitoring

Monitor extraction progress:

```bash
python -m scraper run --carrier aetna --progress

# Output:
# Aetna: [====================] 100% Complete
# - Downloaded: 45 PDFs
# - Processed: 1200 procedures
# - Errors: 0
```

### 3. Performance Metrics

Collect performance metrics:

```bash
python -m scraper stats --period 24h
```

## Data Export

### 1. Export to Different Formats

```bash
# Export to CSV
python -m scraper export --format csv --output data.csv

# Export to JSON
python -m scraper export --format json --output data.json

# Export to Excel
python -m scraper export --format excel --output data.xlsx
```

### 2. Filtered Export

Export specific data:

```bash
python -m scraper export \
                     --carrier aetna \
                     --procedures D0150,D0210 \
                     --format csv
```

## Troubleshooting

### 1. Diagnostic Mode

Run in diagnostic mode:

```bash
python -m scraper diagnose --carrier aetna
```

### 2. Test Connectivity

Test carrier portal access:

```bash
python -m scraper test-connection --carrier aetna
```

### 3. Validate Setup

Verify system setup:

```bash
python -m scraper check-setup
```

## Best Practices

1. **Regular Backups**
   - Back up data before major runs
   - Keep backup rotation policy
   - Verify backup integrity

2. **Resource Management**
   - Monitor memory usage
   - Clean up temporary files
   - Archive old data

3. **Error Handling**
   - Set up error notifications
   - Monitor error rates
   - Document error patterns

4. **Performance Optimization**
   - Use appropriate rate limits
   - Enable caching
   - Schedule during off-peak hours

## Support

For usage-related issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review carrier-specific documentation
3. Contact support team 