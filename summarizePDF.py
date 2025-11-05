import os
import requests
import argparse

from tqdm import tqdm
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# ----- CONFIG -----

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"
MAX_CHUNK_TOKENS = 2000
TIMEOUT = 600
OUTPUT_TXT_SUFIX = "_summary.txt"
OUTPUT_PDF_SUFIX = "_summary.pdf"
MAX_INPUT_PDF_PAGES = 50

# --- END CONFIG ---

def read_pdf_text(path, max_pages = MAX_INPUT_PDF_PAGES):
    reader = PdfReader(path)
    pages = min(len(reader.pages), max_pages)
    texts = []

    for i in range(pages):
        page = reader.pages[i]
        text = page.extract_text() or ""
        texts.append(text)
    # end for

    return "\n\n".join(texts)
# end def

def chunk_text(text, chunk_size = MAX_CHUNK_TOKENS):
    words = text.split()
    chunks = []
    cur = []
    cur_len = 0

    for w in words:
        cur.append(w)
        cur_len += len(w) + 1

        if cur_len >= chunk_size:
            chunks.append(" ".join(cur))
            cur = []
            cur_len = 0
        # end if
    # end for

    if cur:
        chunks.append(" ".join(cur))
    # end if

    return chunks
# end def

def ollama_generate(prompt, model = MODEL, timeout = TIMEOUT):
    try:
        resp = requests.post(OLLAMA_URL, json = {"model": model, "prompt": prompt, "stream": False}, timeout = timeout)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict) and "response" in data:
            return data["response"]
        # end if

        if isinstance(data, dict) and "results" in data:
            texts = []
            for r in data["results"]:
                if isinstance(r, dict) and "contents" in r:
                    for c in r["contents"]:
                        if c.get("type") == "output_text":
                            texts.append(c.get("text", ""))
                        # end if
                    # end for
                # end if
            # end for
            return "\n".join(texts).strip()
        # end if

        return str(data)
    except Exception as exc:
        raise RuntimeError(f"Ollama request failed: {exc}")
    # end try
# end def

def summarize_chunk(chunk, model = MODEL):
    prompt = (
        "You are an assistant that summarizes texts."
        "Make short structured summary with headings, key bullet points and that is concise.\n\n"
        f"{chunk}\n\nSummary:\n"
    )
    return ollama_generate(prompt, model=model)
# end def

def combine_and_refine(summaries, model = MODEL):
    joined = "\n\n".join(summaries)
    prompt = (
        "You are an assistant, combine and refine following partial summaries."
        "Summarize to single coherent, well-structured summary. Make it 1-2 pagess summary (~600-1000 words)."
        "Use headings, short paragraphs and bullet points where helpful.\n\n"
        f"Partial summaries:\n{joined}\n\nFinal summary:\n"
    )
    return ollama_generate(prompt, model=model)
# end def

def save_text(text, path):
    with open(path, "w", encoding = "utf-8") as file:
        file.write(text)
    # end with
# end def

def save_pdf(text, path):
    doc = SimpleDocTemplate(path, pagesize = A4)
    styles = getSampleStyleSheet()
    story = []

    for line in text.split("\n\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        # end if

        if line.startswith("#"):
            story.append(Paragraph(line.lstrip("# ").strip(), styles["Heading2"]))
        else:
            story.append(Paragraph(line.replace("\n", "<br/>"), styles["BodyText"]))
        # end if

        story.append(Spacer(1, 6))
    # end for

    doc.build(story)
# end def

def main():
    parser = argparse.ArgumentParser(description = "Ollama PDF summarizer")
    parser.add_argument("pdfPath", help = "Path to input PDF")
    parser.add_argument("--model", help = f"Ollama model name, default is {MODEL}", default = None)

    args = parser.parse_args()

    model = args.model or MODEL

    print(f"Using model Ollama {model}")

    base_path = os.path.splitext(args.pdfPath)[0]

    text = read_pdf_text(args.pdfPath)
    if not text.strip():
        print("No text found in PDF!")
        return
    #end if

    chunks = chunk_text(text)
    print(f"Document splitted into {len(chunks)} chunks.")

    summaries = []
    print("Summarizing chunks.")
    for i, c in enumerate(tqdm(chunks, desc = "Chunks")):
        chunk_sum = summarize_chunk(c, model)
        summaries.append(chunk_sum)
    # end for

    print("Combining chunks summaries into final summary.")
    final_summary = combine_and_refine(summaries, model)

    output_txt_path = base_path + OUTPUT_TXT_SUFIX
    output_pdf_path = base_path + OUTPUT_PDF_SUFIX

    print(f"Saving txt to {output_txt_path}")
    save_text(final_summary, output_txt_path)

    print(f"Saving pdf to {output_pdf_path}")
    save_pdf(final_summary, output_pdf_path)
#end def

if __name__ == "__main__":
    main() 
# end if