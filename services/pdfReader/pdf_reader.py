import os
import fitz  # PyMuPDF
import logging
import pytesseract
from PIL import Image

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PDFReader:
    def __init__(self, file_path="GrowHire\\resume\\Resume.pdf"):
        """Initializes the PDFReader with the correct absolute file path."""
        script_dir = os.path.dirname(os.path.abspath(__file__))  # ✅ Get script directory
        
        # ✅ Ensure file_path is appended correctly
        self.file_path = os.path.abspath(os.path.join(script_dir, "Resume.pdf"))

        self.text = None  # Placeholder for extracted text

    def read_pdf(self):
        """Extracts text from the given PDF, starting from 'ABOUT ME' onwards."""
        if not os.path.exists(self.file_path):
            logger.error(f"❌ PDF file not found: {self.file_path}")
            return None

        try:
            logger.info(f"📄 Reading PDF file: {self.file_path}")
            extracted_text = []

            with fitz.open(self.file_path) as doc:
                full_text = ""  # Store all extracted text
                for page in doc:
                    text = page.get_text("text").strip()

                    # If no text found, try extracting from blocks
                    if not text:
                        blocks = page.get_text("blocks")
                        text = "\n".join([t[4] for t in blocks if t[4].strip()]) if blocks else ""

                    # If still empty, use OCR as a fallback
                    if not text:
                        text = self.extract_text_via_ocr(page)

                    full_text += f"\n{text}"

                # **Trim text to start from "ABOUT ME"**
                if "ABOUT ME" in full_text:
                    full_text = full_text.split("ABOUT ME", 1)[1].strip()
                else:
                    logger.warning("⚠️ 'ABOUT ME' section not found in the document.")

            if not full_text:
                logger.warning("⚠️ PDF extracted text is empty after trimming.")
                return None

            self.text = full_text
            logger.info("✅ Successfully extracted text from 'ABOUT ME' onwards.")
            return self.text

        except Exception as e:
            logger.error(f"❌ Failed to read PDF: {e}")
            return None

    def extract_text_via_ocr(self, page):
        """Extracts text from a PDF page using OCR (Tesseract) for scanned PDFs."""
        try:
            img = page.get_pixmap()  # Convert PDF page to image
            image = Image.frombytes("RGB", [img.width, img.height], img.samples)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"❌ OCR extraction failed: {e}")
            return ""

    def get_text(self):
        """Returns the extracted text from 'ABOUT ME' onwards."""
        if self.text is None:
            return self.read_pdf()
        return self.text


# Example Usage
if __name__ == "__main__":
    pdf_reader = PDFReader("GrowHire/resume/Resume.pdf")
    text = pdf_reader.get_text()

    if text:
        print("\nExtracted PDF Text from 'ABOUT ME' Onwards:\n")
        print(text[:2000])  # Print the first 2000 characters for preview
    else:
        print("❌ No relevant text extracted.")
