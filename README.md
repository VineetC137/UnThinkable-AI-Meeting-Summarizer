# UnThinkable-AI-Meeting-Summarizer

An intelligent meeting summarization tool that transforms audio recordings into structured summaries using cutting-edge AI technology.

## 🚀 Overview

The **UnThinkable AI Meeting Summarizer** is a powerful Gradio-based web application that automatically converts meeting audio recordings into detailed transcripts and generates intelligent summaries. Built with modern AI technologies including `whisper.cpp` for speech-to-text conversion and `Ollama` for advanced text summarization, this tool revolutionizes how you handle meeting documentation.

![Meeting Summarizer Interface](https://github.com/user-attachments/assets/5b93cfed-c853-4ebb-8d90-bbda58354192)

## ✨ Features

- **🎯 Smart Audio Processing**: Advanced audio-to-text conversion using multiple Whisper models
- **📝 AI-Powered Summarization**: Intelligent summary generation using Ollama's large language models
- **🌐 Multi-Model Support**: Choose from various Whisper models (base, small, medium, large-V3)
- **🔄 Real-time Translation**: Automatic translation of non-English audio to English
- **💻 User-Friendly Interface**: Intuitive Gradio web interface for seamless operation
- **📊 Comprehensive Output**: Full transcript download + concise summary generation

## 🛠️ Technology Stack

- **Backend**: Python 3.x
- **UI Framework**: Gradio
- **Speech Recognition**: whisper.cpp (Optimized C++ implementation)
- **Text Summarization**: Ollama Server
- **Audio Processing**: FFmpeg
- **API Integration**: Requests library

## 📋 Prerequisites

Before installation, ensure you have:

- Python 3.x installed
- [FFmpeg](https://www.ffmpeg.org/) for audio processing
- [Ollama server](https://ollama.com/) running locally
- Git (for cloning the repository)

### Setting up Ollama

Install and run Ollama with a language model:

```bash
# Install Ollama (follow official documentation)
# Then download and run a model
ollama run llama3.2
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

Clone the repository and run the automated setup script:

```bash
git clone https://github.com/VineetC137/UnThinkable-AI-Meeting-Summarizer.git
cd UnThinkable-AI-Meeting-Summarizer
chmod +x run_meeting_summarizer.sh
./run_meeting_summarizer.sh
```

This script will:
- Create a Python virtual environment
- Install all required dependencies
- Build and configure whisper.cpp
- Download the necessary Whisper models
- Launch the application automatically

### Option 2: Manual Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/VineetC137/UnThinkable-AI-Meeting-Summarizer.git
   cd UnThinkable-AI-Meeting-Summarizer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup whisper.cpp**
   ```bash
   git clone https://github.com/ggerganov/whisper.cpp.git
   cd whisper.cpp
   make
   ./models/download-ggml-model.sh small
   cd ..
   ```

5. **Run the Application**
   ```bash
   python main.py
   ```

## 💡 Usage Guide

1. **Launch Application**: Access the web interface at `http://127.0.0.1:7860`
2. **Upload Audio**: Drag and drop your meeting audio file (supports .wav, .mp3, etc.)
3. **Add Context**: Optionally provide meeting context for better summarization
4. **Select Models**: 
   - Choose your preferred Whisper model for transcription
   - Select an Ollama model for summarization
5. **Process & Review**: Get your summary and download the full transcript

## ⚙️ Configuration

### Adding More Whisper Models

Download additional models as needed:

```bash
cd whisper.cpp
./models/download-ggml-model.sh base    # For base model
./models/download-ggml-model.sh medium  # For medium model
./models/download-ggml-model.sh large   # For large model
```

### Custom Ollama Server

Update the server URL in `main.py` if using a remote Ollama instance:

```python
OLLAMA_SERVER_URL = "http://your-server:11434"
```

## 🎯 Use Cases

- **Corporate Meetings**: Generate actionable meeting minutes
- **Educational Sessions**: Summarize lectures and workshops  
- **Client Calls**: Document important client discussions
- **Interviews**: Convert interviews into structured summaries
- **Research**: Process recorded focus groups and discussions

## 📁 Project Structure

```
UnThinkable-AI-Meeting-Summarizer/
├── main.py                    # Core application logic
├── requirements.txt           # Python dependencies
├── run_meeting_summarizer.sh  # Automated setup script
├── README.md                 # Project documentation
├── LICENSE                   # MIT License
└── .github/                  # GitHub configuration
```

## 🤝 Contributing

Contributions are welcome! Please feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- **whisper.cpp** by Georgi Gerganov for efficient audio processing
- **Gradio** team for the excellent web interface framework
- **Ollama** for providing accessible large language models
- **OpenAI** for the original Whisper model architecture

## 📞 Support

If you encounter any issues or have questions:

- Create an issue on GitHub
- Check the documentation for troubleshooting tips
- Ensure all prerequisites are properly installed

---

**Built with ❤️ by [VineetC137](https://github.com/VineetC137)**

*Transform your meetings into actionable insights with UnThinkable AI!*