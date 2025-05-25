# Haptic Feedback API

A Flask-based REST API that converts text to haptic vibration patterns using the Shappe Haptic Communication System. This API translates text into dot-dash patterns similar to Morse code, then converts them into timed vibration instructions for haptic feedback devices.

## Features

- 🔤 **Text to Haptic Translation**: Convert any text (A-Z, 0-9, basic punctuation) into haptic vibration patterns
- ⚡ **Caching System**: Built-in caching for improved performance on repeated requests
- 🎛️ **Customizable Parameters**: Adjustable speed and intensity settings
- 📊 **Comprehensive Logging**: Request tracking and detailed logging for debugging
- 🚀 **RESTful API**: Clean JSON-based API endpoints
- 🛡️ **Error Handling**: Robust error handling with proper HTTP status codes

## Quick Start

### Prerequisites

- Python 3.7+
- Flask

### Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd haptic-feedback-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Translate Text to Haptic Pattern

**POST** `/haptic_translate/`

Convert text into haptic vibration patterns.

#### Request Body:
```json
{
  "text": "Hello World",
  "preferences": {
    "speed": 1.0,
    "intensity": 0.8
  },
  "use_cache": true
}
```

#### Parameters:
- `text` (string, required): The text to convert to haptic patterns
- `preferences` (object, optional): Customization options
  - `speed` (float, 0.1-3.0): Speed multiplier (1.0 = normal, lower = slower)
  - `intensity` (float, 0.0-1.0): Vibration intensity
- `use_cache` (boolean, optional): Whether to use caching (default: true)

#### Response:
```json
{
  "pattern": [
    {
      "type": "vibrate",
      "duration": 100,
      "intensity": 0.8
    },
    {
      "type": "pause",
      "duration": 50
    }
  ],
  "totalDuration": 2500,
  "characterCount": 11,
  "text": "Hello World",
  "cached": false
}
```

#### Example Usage:
```bash
curl -X POST http://localhost:5000/haptic_translate/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello",
    "preferences": {
      "speed": 1.2,
      "intensity": 0.9
    }
  }'
```

### 2. Health Check

**GET** `/`

Check if the API is running.

#### Response:
```json
{
  "status": "healthy",
  "service": "Haptic Feedback API",
  "version": "1.0.0"
}
```

### 3. Clear Cache

**POST** `/cache/clear`

Clear all cached haptic patterns.

#### Response:
```json
{
  "message": "Cache cleared successfully. Removed 5 entries.",
  "cache_size": 0
}
```

### 4. Cache Status

**GET** `/cache/status`

Get information about the current cache state.

#### Response:
```json
{
  "cache_entries": 3,
  "cache_keys": ["haptic_pattern:abc123", "haptic_pattern:def456"]
}
```

## Haptic Pattern System

The API uses a custom haptic communication system that maps characters to dot-dash patterns:

### Character Mapping Examples:
- **A**: `•-` (short vibration + long vibration)
- **B**: `•–•–` (short + long + short + long)
- **E**: `•` (single short vibration)
- **T**: `-` (single long vibration)
- **Space**: Word pause
- **Punctuation** (.,!?): Sentence pause

### Timing Configuration:
- **Dot (•)**: 100ms vibration
- **Dash (-)**: 300ms vibration  
- **Letter space**: 200ms pause
- **Word space**: 600ms pause
- **Sentence space**: 900ms pause

All timings are adjusted by the `speed` parameter.

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (missing text, invalid parameters)
- **500**: Internal Server Error

### Error Response Format:
```json
{
  "error": "Text field is required"
}
```

## Performance & Caching

- **Caching**: Results are cached based on text content and user preferences
- **Cache Key**: MD5 hash of normalized parameters
- **Memory Usage**: In-memory caching (easily replaceable with Redis)
- **Request Tracking**: Each request gets a unique ID for log tracking

## Supported Characters

- **Letters**: A-Z (case insensitive)
- **Numbers**: 0-9
- **Punctuation**: Period (.), Exclamation (!), Question (?)
- **Special**: Space, Hash (#)

Unsupported characters are logged and skipped during translation.

## Development

### Project Structure:
```
haptic-feedback-api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

### Logging

The application provides comprehensive logging:
- Request tracking with unique IDs
- Performance timing
- Cache hit/miss statistics
- Character processing details
- Error tracking

Logs are output to console with timestamps and log levels.

### Running Tests

You can test the API manually using curl or any HTTP client:

```bash
# Basic translation
curl -X POST http://localhost:5000/haptic_translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "SOS"}'

# With custom preferences
curl -X POST http://localhost:5000/haptic_translate/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Emergency",
    "preferences": {"speed": 0.5, "intensity": 1.0},
    "use_cache": false
  }'
```

## Configuration

### Environment Variables (Optional):
- `FLASK_ENV`: Set to `development` for debug mode
- `FLASK_PORT`: Port number (default: 5000)
- `FLASK_HOST`: Host address (default: 0.0.0.0)

### Production Deployment:
For production deployment, consider:
- Using a WSGI server like Gunicorn
- Implementing Redis for caching
- Adding authentication/rate limiting
- Setting up proper logging infrastructure

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please open an issue in the GitHub repository.

---

**Built with ❤️ using Flask and Python**
