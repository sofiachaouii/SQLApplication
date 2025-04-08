# Chat-Based Spreadsheet Tool

A command-line tool that allows users to interact with spreadsheet data using natural language queries. This tool combines the power of SQLite databases with natural language processing to provide an intuitive interface for data analysis.

## Features

- Load CSV files into SQLite database
- Natural language querying of data
- Automatic schema inference
- Interactive command-line interface
- OpenAI-powered SQL query generation

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Run the main script:
   ```bash
   python main.py
   ```

2. Available commands:
   - `load <csv_file>`: Load a CSV file into the database
   - `tables`: List all tables in the database
   - `query <sql>`: Execute a raw SQL query
   - `ask <question>`: Ask a question in natural language
   - `exit`: Exit the program

## Example

```
> load sales.csv
> ask "Show me the top 5 products by revenue"
```

## Requirements

- Python 3.8+
- SQLite3
- OpenAI API key
- Required Python packages (see requirements.txt) 