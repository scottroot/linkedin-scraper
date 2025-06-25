#!/usr/bin/env python3
"""
Test script to verify threading implementation works correctly
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

class TestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Threading Test")
        self.root.geometry("400x300")

        # Variables
        self.processing_thread = None
        self.stop_event = threading.Event()

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Threading Test", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Start button
        self.start_button = ttk.Button(main_frame, text="Start Test Processing", command=self.start_processing)
        self.start_button.grid(row=1, column=0, columnspan=2, pady=10)

        # Stop button (initially hidden)
        self.stop_button = ttk.Button(main_frame, text="Stop Processing", command=self.stop_processing, state="disabled")
        self.stop_button.grid(row=1, column=0, columnspan=2, pady=10)
        self.stop_button.grid_remove()

        # Progress text
        self.progress_text = tk.Text(main_frame, height=10, width=50)
        self.progress_text.grid(row=2, column=0, columnspan=2, pady=10)

        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)

    def log_message(self, message):
        """Add a message to the progress text area"""
        self.root.after(0, lambda: self.progress_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.progress_text.see(tk.END))

    def start_processing(self):
        """Start the test processing in a separate thread"""
        self.log_message("Starting test processing...")
        self.log_message("This simulates the LinkedIn scraping process.")

        # Disable start button and show stop button
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.stop_button.grid()
        self.start_button.grid_remove()

        # Clear stop event
        self.stop_event.clear()

        # Update status
        self.status_label.config(text="Processing...")

        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.test_process)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def test_process(self):
        """Simulate the processing in a separate thread"""
        try:
            self.log_message("Thread started successfully!")
            self.log_message("Simulating browser initialization...")
            time.sleep(2)

            # Simulate processing batches
            for batch_num in range(1, 6):
                if self.stop_event.is_set():
                    self.log_message("Stop signal received. Stopping processing.")
                    break

                self.log_message(f"Processing batch {batch_num}/5...")

                # Simulate processing individual contacts
                for contact_num in range(1, 4):
                    if self.stop_event.is_set():
                        self.log_message("Stop signal received. Stopping processing.")
                        break

                    self.log_message(f"  Processing contact {contact_num}/3 in batch {batch_num}")
                    time.sleep(1)  # Simulate work

                if not self.stop_event.is_set():
                    self.log_message(f"Batch {batch_num} completed.")
                    time.sleep(2)  # Simulate delay between batches

            if not self.stop_event.is_set():
                self.log_message("All processing completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", "Test processing completed!"))
            else:
                self.log_message("Processing stopped by user.")

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        finally:
            # Re-enable buttons
            self.root.after(0, self.finish_processing)

    def stop_processing(self):
        """Stop the processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set()
            self.log_message("Stop signal sent. Please wait for current operation to complete.")
            self.stop_button.config(state="disabled")

    def finish_processing(self):
        """Clean up after processing is complete"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.stop_button.grid_remove()
        self.start_button.grid()
        self.status_label.config(text="Ready")
        self.stop_event.clear()

def main():
    root = tk.Tk()
    app = TestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()