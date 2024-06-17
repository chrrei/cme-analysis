import os
import sys
import glob
import argparse
import time
import threading
import pdfplumber
from colorama import Fore, init

init(autoreset=True)
lock = threading.Lock()


def parse_args():
    parser = argparse.ArgumentParser(description="Convert PDF files to text")
    parser.add_argument('--input', required=True, help="Input directory containing PDF files")
    parser.add_argument('--batch_size', type=int, default=5, help="Number of PDF files to process in each batch")
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


def display_processing_message(filename, line_number, stop_event):
    dot = '.'
    idx = 0
    while not stop_event.is_set():
        with lock:
            sys.stdout.write(f"\033[{line_number}HProcessing: {filename} {(idx//100) * dot}\033[K")
            sys.stdout.flush()
        idx += 1
        time.sleep(0.01)


def process_pdf(pdf_file, output_path, line_number):
    filename = os.path.basename(pdf_file)
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=display_processing_message, args=(filename, line_number, stop_event))
    animation_thread.start()

    try:
        text, error = extract_text_from_pdf(pdf_file)
        stop_event.set()
        animation_thread.join()

        with lock:
            sys.stdout.write(f"\033[{line_number}H\033[K")  # Clear line
            if text is not None:
                save_text_to_file(text, output_path)
                sys.stdout.write(Fore.GREEN + f"\033[{line_number}HProcessed: {filename}\033[K\n")
            else:
                sys.stdout.write(Fore.RED + f"\033[{line_number}HError: {filename} - {error}\033[K\n")
            sys.stdout.flush()
    except Exception as e:
        stop_event.set()
        animation_thread.join()
        with lock:
            sys.stdout.write(f"\033[{line_number}H\033[K")  # Clear line
            sys.stdout.write(Fore.RED + f"\033[{line_number}HError: {filename} - {str(e)}\033[K\n")
            sys.stdout.flush()


def main():
    args = parse_args()
    input_dir = args.input
    batch_size = args.batch_size
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
    
    initial_line_number = len(pdf_files) + batch_size

    sys.stdout.write("\033[%dB" % (len(pdf_files) + 2))

    total_files = len(pdf_files)
    num_batches = (total_files + batch_size - 1) // batch_size

    for batch_index in range(num_batches):
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, total_files)
        batch_files = pdf_files[start_index:end_index]

        threads = []

        for i, pdf_file in enumerate(batch_files):
            filename = os.path.basename(pdf_file)
            output_path = os.path.join(output_dir, filename.replace(' ', '_').replace('-', '_').replace('.pdf', '.txt'))
            if os.path.exists(output_path):
                continue
            line_number = initial_line_number + start_index + i
            thread = threading.Thread(target=process_pdf, args=(pdf_file, output_path, line_number))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    print("Processing complete.")
    sys.stdout.write("\033[?25h")  # Show cursor again
    sys.stdout.flush()

if __name__ == "__main__":
    main()
