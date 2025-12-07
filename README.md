# GPT Wrapped - Privacy-First ChatGPT Analytics

A beautiful analytics dashboard for your ChatGPT conversation exports. Your data stays private - all processing happens in your browser's memory.

## 🌟 Features

- 🧠 **Neural Fabric**: Visualize your conversation patterns over time
- 📊 **Interest Analysis**: Automatic topic detection and classification
- 💭 **Emotional DNA**: See your mood patterns as a beautiful heatmap
- ⏰ **Temporal Rhythms**: Discover when you're most active
- 🎯 **Prompt Archetypes**: Understand how you ask questions
- 💰 **Impact Metrics**: See estimated cost, energy, and water usage

## 🚀 Try It Live

**Live Demo:** https://gpt-wrapped.streamlit.app

## 🔒 Privacy First

- ✅ All processing happens in-memory (your data never leaves your device)
- ✅ No data is stored on servers
- ✅ No tracking or analytics
- ✅ Open source - verify the code yourself

## 📦 Run Locally

### Prerequisites
- Python 3.8+
- Your ChatGPT `conversations.json` export file

### Installation

```bash
# Clone the repository
git clone [your-repo-url]
cd antigravity

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Getting Your ChatGPT Data

1. Go to [ChatGPT Settings](https://chat.openai.com/settings)
2. Click "Data Controls" → "Export Data"
3. Wait for email with download link
4. Extract `conversations.json` from the zip file
5. Upload to GPT Wrapped!

## 🛠️ Tech Stack

- **Framework**: Streamlit
- **Analytics**: Pandas, NumPy
- **Visualizations**: Plotly
- **NLP**: NLTK, TextBlob
- **Token Counting**: tiktoken

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool is for personal analytics only. It's not affiliated with OpenAI. Your ChatGPT data may contain sensitive information - use responsibly.

## 🐛 Issues?

Found a bug? [Open an issue](your-github-repo/issues)

---

Made with ❤️ for curious minds by a curious mind who want to understand their AI interactions
