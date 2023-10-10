# Flask YouTube Script Generator

This service provides an API to generate YouTube scripts based on a given topic. It uses `autogen` with 2 agents (script writer, editor) to generate viral youtube scripts.

## Getting Started

### Prerequisites

- Python 3.12+
- Docker (optional, for containerization)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dachkovski/flask-youtube-script-generator.git
cd flask-youtube-script-generator
```

2. (Optional) Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

### Running the Service

#### Directly:

```bash
python app.py
```

The service will start and listen on port 8080.

#### Using Docker:

1. Build the Docker image:
```bash
docker build -t flask-youtube-script-generator .
```

2. Run the Docker container:
```bash
docker run -p 5001:5001 flask-youtube-script-generator
```

## Usage

Send a POST request to the `/generate_script` endpoint with the following JSON payload:

```json
{
    "topic": "YOUR_TOPIC_HERE",    
    "form": "shortform/longform",
    "api_key": "YOUR_API_KEY_HERE"
}
```

The service will respond with a generated YouTube script based on the provided topic.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.