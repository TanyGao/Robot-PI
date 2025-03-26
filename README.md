# Robot-PI

A multi-client robot system with voice interaction capabilities, including Raspberry Pi and Windows clients.

## Project Structure

```
├── src/
│   ├── server/         # FastAPI server
│   ├── client/         # Client implementations
│   │   ├── raspberry_pi/  # Raspberry Pi client
│   │   └── windows_voice/ # Windows voice client
│   └── common/         # Shared utilities
├── data/              # Data directory
│   └── uploads/       # Voice file uploads
└── requirements.txt   # Project dependencies
```

## Branches

- `main`: Core server and common utilities
- `windows-client`: Windows voice client implementation
- `raspberry-client`: Raspberry Pi client implementation

## Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies from the appropriate requirements.txt file
4. Copy .env.example to .env and configure as needed
5. Run the server and client

## License

MIT