import os
import json
import ollama
import time

import fitz  # PyMuPDF for PDF parsing
import docx
import subprocess

# Paths
RESUME_FOLDER = "resumeDownloads"  # Folder containing PDF/DOC files
OUTPUT_FOLDER = "parsed_resumes"  # Folder to save JSONs
FAILED_LOG = "failed_resumes.txt"  # Log failed resumes

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        return text.strip()
    except Exception as e:
        print(f"❌ Error extracting text from PDF {pdf_path}: {e}")
        return None

def extract_text_from_docx(docx_path):
    """Extract text from a DOCX file using python-docx."""
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()
    except Exception as e:
        print(f"❌ Error extracting text from DOCX {docx_path}: {e}")
        return None

def extract_text_from_doc(doc_path):
    """Convert and extract text from old DOC format using unoconv."""
    try:
        temp_txt = doc_path.replace(".doc", ".txt")
        subprocess.run(["unoconv", "-f", "txt", "-o", temp_txt, doc_path], check=True)
        with open(temp_txt, "r", encoding="utf-8") as file:
            text = file.read()
        os.remove(temp_txt)  # Clean up
        return text.strip()
    except Exception as e:
        print(f"❌ Error converting DOC {doc_path}: {e}")
        return None

import os
import json
import ollama
import re

def clean_json_string(json_str):
    # Remove newlines and excessive spaces
    cleaned_str = re.sub(r'\s*\n\s*', '', json_str)  # Removes newlines and surrounding spaces
    return cleaned_str

def extract_json(response):
    """Extracts JSON content from a string using regex."""
    response_str = str(response)  # Ensure response.content is a string
    print("🔍 Checking response content for JSON block...\n")
    
    # Debugging: Print a snippet of the response to check format
    # print(response_str[:500])  # Print first 500 characters to verify JSON exists

    # Adjusted regex to allow variations (e.g., extra spaces, no newline after ```json)
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response_str)

    if match:
        json_str = match.group(1).strip()  # Remove extra spaces/newlines
        try:
            parsed_json = json.loads(json_str)  # Convert to dictionary
            print("\n✅ Successfully extracted JSON!\n")
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"\n❌ Error decoding JSON: {e}")
            print("🔍 Extracted JSON String:\n", json_str)
            return None
    else:
        print("\n❌ No JSON block found in response.")
        return None


LOG_FILE = "resume_parsing_errors.log"

def extract_resume_data(resume_text):
    """Send resume text to DeepSeek model for JSON extraction."""
    prompt = f"""
    You are an expert resume parser. Extract the following details from the provided resume and return ONLY a well-formatted JSON with NO extra text, NO explanations, and NO reasoning.

    **Strict JSON Structure:**  
    {{
        "Name": "Full Name",
        "Skills": ["Skill1", "Skill2"],
        "Experience": [
            {{
                "Company": "Company Name",
                "Months": Number,
                "Description": "Short summary"
            }}
        ],
        "Education": [
            {{
                "Degree": "Degree Name",
                "CGPA": "8.5/10",
                "Institution": "University Name"
            }}
        ],
        "Certifications": ["Certification 1"],
        "Projects": [
            {{
                "Title": "Project Name",
                "Description": "One-line summary"
            }}
        ],
        "Everything Else": "Additional details"
    }}

    **Rules:**
    - Extract ACCURATE data from the resume.
    - NO explanations, NO extra formatting.
    - Output ONLY JSON, without any markdown formatting.
    - Infer skills based on the project work, experience, or education.
    - Include any additional details under "Everything Else".

    **Resume Content:**  
    {resume_text}

    **Expected JSON Output:**
    """

    try:
        response = ollama.chat(
            model='deepseek-r1:1.5b-qwen-distill-fp16',
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON content
        response_content = response["message"]["content"]

        # Find first occurrence of '{' and last occurrence of '}'
        start_index = response_content.find('{')
        end_index = response_content.rfind('}')

        if start_index != -1 and end_index != -1:
            json_str = response_content[start_index:end_index + 1]  # Extract JSON substring
            parsed_json = json.loads(json_str)  # Convert to dictionary
            return parsed_json
        else:
            print("⚠ Model response does not contain valid JSON.")
            return None

    except json.JSONDecodeError as e:
        print(f"❌ JSON decoding error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def sanitize_filename(name):
    """Sanitize name for a valid filename."""
    name = name.replace(" ", "_").replace(".", "").replace(",", "")
    return "".join(c for c in name if c.isalnum() or c in "_-")

def get_unique_filename(base_name):
    """Ensure unique filenames by adding suffix if needed."""
    count = 1
    file_name = f"{base_name}.json"
    while os.path.exists(os.path.join(OUTPUT_FOLDER, file_name)):
        file_name = f"{base_name}_{count}.json"
        count += 1
    return file_name

def process_resumes():
    """Iterate through all resumes, extract text, and fetch structured JSON."""
    failed_resumes = []

    for filename in os.listdir(RESUME_FOLDER):
        file_path = os.path.join(RESUME_FOLDER, filename)
        resume_text = None
        error_message = ""

        # Handle different file formats
        try:
            if filename.lower().endswith(".pdf"):
                resume_text = extract_text_from_pdf(file_path)
            elif filename.lower().endswith(".docx"):
                resume_text = extract_text_from_docx(file_path)
            elif filename.lower().endswith(".doc"):
                resume_text = extract_text_from_doc(file_path)

            if not resume_text:
                error_message = f"⚠ No text extracted from {filename}."
                raise ValueError(error_message)

            print(f"🔍 Processing: {filename}")

            # Extract structured JSON from resume
            structured_data = extract_resume_data(resume_text)

            if structured_data:
                # Get candidate's full name for renaming
                full_name = structured_data.get("Name", "").strip()
                if not full_name:
                    print(f"⚠ No full name found in {filename}, using original filename.")
                    base_name = os.path.splitext(filename)[0]
                else:
                    base_name = sanitize_filename(full_name)

                # Ensure filename is unique
                output_file = get_unique_filename(base_name)
                output_path = os.path.join(OUTPUT_FOLDER, output_file)

                # Save JSON output
                with open(output_path, "w", encoding="utf-8") as json_file:
                    json.dump(structured_data, json_file, indent=4)
                print(f"✅ Saved as: {output_file}")

            else:
                error_message = f"❌ Failed JSON extraction for {filename}."
                raise ValueError(error_message)

        except Exception as e:
            error_message = f"{error_message or 'Unknown error'} | Error: {str(e)}"
            print(error_message)
            failed_resumes.append(f"{filename} - {error_message}")

        # Avoid rate-limiting, add delay if needed
        time.sleep(2)

    # Log failed resumes with errors
    if failed_resumes:
        with open(FAILED_LOG, "a", encoding="utf-8") as log_file:  # Append mode
            log_file.write("\n".join(failed_resumes) + "\n")
        print(f"⚠ Some resumes failed. Check {FAILED_LOG} for details.")

if __name__ == "__main__":
    process_resumes()
