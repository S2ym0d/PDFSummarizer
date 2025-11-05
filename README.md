# 🧾 PDF Summarizer

Simple Python script that summarizes PDF files into 1-2 page summaries using a local Ollama model.

## 🚀 Features
- Extracts text from PDFs (up to 50 pages)
- Summarizes using locally installed LLM via Ollama (https://github.com/ollama/ollama)
- Outputs a PDF summary
- Configurable used model name

## ⚙️ Requirements
- Python 3.11+
- Ollama installed and running locally
- installed libraries from requirements.txt 

## 🧰 Usage
### Installing
git clone https://github.com/S2ym0d/PDFSummarizer.git

cd PDFSummarizer

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

### Summarizing
python summarizePDF.py &lt;path to pdf file&gt; --model &lt;optional model name&gt;
