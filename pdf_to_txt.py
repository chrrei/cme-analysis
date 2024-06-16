import os
import sys
import glob
import argparse
import time
import threading
import pdfplumber
from colorama import Fore, init

init(autoreset=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Convert PDF files to text")
    parser.add_argument('--input', required=True, help="Input directory containing PDF files")
    return parser.parse_args()


def get_confirmation(prompt):
    while True:
        response = input(prompt + " (y/n): ").strip().lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        else:
            print("Please respond with 'y' or 'n'.")


def extract_text_from_pdf(pdf_path):
    pdf_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pdf_text += page.extract_text()
    except Exception as e:
        return None, str(e)
    return pdf_text, None


def save_text_to_file(text, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)


def list_pdf_files(input_dir):
    return glob.glob(os.path.join(input_dir, "*.pdf"))



def display_processing_message(filename, stop_event):
    dot = '.'
    idx = 0
    sys.stdout.write("\r\033[?25l")  # Hide cursor
    while not stop_event.is_set():
        sys.stdout.write(f"\rProcessing: {filename} {idx*dot}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.5)
    sys.stdout.write("\r\033[?25h")  # Show cursor


def main():
    args = parse_args()
    input_dir = args.input
    output_dir = "./data"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_files = list_pdf_files(input_dir)
    if not pdf_files:
        print("No PDF files found in the input directory.")
        return

    print("Found the following PDF files:")
    for pdf_file in pdf_files:
        print(pdf_file)

    if not get_confirmation("Is this the correct list of PDF files to process?"):
        print("Exiting.")
        return

    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        output_path = os.path.join(output_dir, filename.replace(' ', '_').replace('-', '_').replace('.pdf', '.txt'))
        stop_event = threading.Event()
        thread = threading.Thread(target=display_processing_message, args=(filename, stop_event))
        thread.start()
        try:
            text, error = extract_text_from_pdf(pdf_file)
            stop_event.set()
            thread.join()

            sys.stdout.write("\r\033[K")  # Clear line
            if text is not None:
                save_text_to_file(text, output_path)
                print(Fore.GREEN + f"\rProcessed: {filename}")
            else:
                print(Fore.RED + f"\rError: {filename} - {error}")
        except Exception as e:
            stop_event.set()
            thread.join()
            sys.stdout.write("\r\033[K")  # Clear line
            print(Fore.RED + f"\rError: {filename} - {str(e)}")


if __name__ == "__main__":
    main()
