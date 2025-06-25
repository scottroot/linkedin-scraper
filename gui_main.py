import sys
import os
import threading
import queue


from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QGroupBox, QFrame,
    QSpinBox, QCheckBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

import pandas as pd

# Import the main processing functions
from app.check_company import process_contacts_batch


class MessageProcessor(QThread):
    """Thread for processing messages from background processing"""
    log_signal = Signal(str)
    success_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, message_queue):
        super().__init__()
        self.message_queue = message_queue
        self.running = True

    def run(self):
        while self.running:
            try:
                message_type, data = self.message_queue.get(timeout=0.1)

                if message_type == "log":
                    self.log_signal.emit(data)
                elif message_type == "success":
                    self.success_signal.emit(data)
                elif message_type == "error":
                    self.error_signal.emit(data)
                elif message_type == "finished":
                    self.finished_signal.emit()

            except queue.Empty:
                # This is expected - no messages in queue, continue checking
                continue
            except Exception as e:
                print(f"Error processing messages: {e}")

    def stop(self):
        self.running = False

class LinkedInScraperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Contact Validator")
        self.setGeometry(100, 100, 700, 800)
        self.setMinimumSize(600, 700)

        # Variables
        self.input_file_path = os.path.join(os.getcwd(), "contacts.csv")
        self.output_folder_path = os.getcwd()
        self.batch_size = 5
        self.delay = 30
        self.start_row = 0
        self.limit = 0
        self.show_advanced = False

        # Data
        self.contacts_df = None
        self.processing_thread = None
        self.stop_processing_flag = False
        self.stop_event = threading.Event()

        # Thread-safe communication queue
        self.message_queue = queue.Queue()
        self.message_processor = MessageProcessor(self.message_queue)
        self.message_processor.log_signal.connect(self.append_log)
        self.message_processor.success_signal.connect(self.show_success)
        self.message_processor.error_signal.connect(self.show_error)
        self.message_processor.finished_signal.connect(self.finish_processing)
        self.message_processor.start()

        self.setup_ui()

    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("LinkedIn Contact Validator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Input file selection
        input_group = QGroupBox("Input File")
        input_layout = QHBoxLayout(input_group)

        input_label = QLabel("Input CSV File:")
        self.input_file_edit = QLineEdit(self.input_file_path)
        input_browse_btn = QPushButton("Browse")
        input_browse_btn.clicked.connect(self.browse_input_file)

        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_file_edit)
        input_layout.addWidget(input_browse_btn)
        main_layout.addWidget(input_group)

        # Output folder selection
        output_group = QGroupBox("Output Folder")
        output_layout = QHBoxLayout(output_group)

        output_label = QLabel("Output Folder:")
        self.output_folder_edit = QLineEdit(self.output_folder_path)
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.clicked.connect(self.browse_output_folder)

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_folder_edit)
        output_layout.addWidget(output_browse_btn)
        main_layout.addWidget(output_group)

        # Load and validate button
        self.load_button = QPushButton("Load & Validate CSV")
        self.load_button.clicked.connect(self.load_and_validate_csv)
        main_layout.addWidget(self.load_button)

        # File info group
        self.file_info_group = QGroupBox("File Information")
        file_info_layout = QVBoxLayout(self.file_info_group)

        self.file_info_text = QTextEdit()
        self.file_info_text.setMaximumHeight(200)
        self.file_info_text.setReadOnly(True)
        file_info_layout.addWidget(self.file_info_text)
        main_layout.addWidget(self.file_info_group)

        # Advanced options
        self.advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QGridLayout(self.advanced_group)

        # Start Row
        start_row_label = QLabel("Start Row:")
        self.start_row_spin = QSpinBox()
        self.start_row_spin.setMinimum(0)
        self.start_row_spin.setMaximum(999999)
        self.start_row_spin.setValue(0)
        start_row_help = QLabel("(0-indexed, 0 = first row)")
        advanced_layout.addWidget(start_row_label, 0, 0)
        advanced_layout.addWidget(self.start_row_spin, 0, 1)
        advanced_layout.addWidget(start_row_help, 0, 2)

        # Limit
        limit_label = QLabel("Limit:")
        self.limit_spin = QSpinBox()
        self.limit_spin.setMinimum(0)
        self.limit_spin.setMaximum(999999)
        self.limit_spin.setValue(0)
        limit_help = QLabel("(0 = no limit)")
        advanced_layout.addWidget(limit_label, 1, 0)
        advanced_layout.addWidget(self.limit_spin, 1, 1)
        advanced_layout.addWidget(limit_help, 1, 2)

        # Batch Size
        batch_size_label = QLabel("Batch Size:")
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(100)
        self.batch_size_spin.setValue(5)
        batch_size_help = QLabel("(contacts per batch)")
        advanced_layout.addWidget(batch_size_label, 2, 0)
        advanced_layout.addWidget(self.batch_size_spin, 2, 1)
        advanced_layout.addWidget(batch_size_help, 2, 2)

        # Delay
        delay_label = QLabel("Delay (seconds):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(300)
        self.delay_spin.setValue(30)
        delay_help = QLabel("(between batches)")
        advanced_layout.addWidget(delay_label, 3, 0)
        advanced_layout.addWidget(self.delay_spin, 3, 1)
        advanced_layout.addWidget(delay_help, 3, 2)

        # Advanced toggle button
        self.advanced_toggle_btn = QPushButton("Show Advanced Options")
        self.advanced_toggle_btn.clicked.connect(self.toggle_advanced)
        main_layout.addWidget(self.advanced_toggle_btn)

        # Hide advanced group initially
        self.advanced_group.hide()
        main_layout.addWidget(self.advanced_group)

        # Process button
        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setEnabled(False)
        main_layout.addWidget(self.process_button)

        # Stop button (initially hidden)
        self.stop_button = QPushButton("Stop Processing")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        self.stop_button.hide()
        main_layout.addWidget(self.stop_button)

        # Progress group
        self.progress_group = QGroupBox("Processing Progress")
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_layout.addWidget(self.progress_bar)

        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(150)
        self.progress_text.setReadOnly(True)
        progress_layout.addWidget(self.progress_text)

        # Hide progress group initially
        self.progress_group.hide()
        main_layout.addWidget(self.progress_group)

    def browse_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            os.getcwd(),
            "CSV files (*.csv);;All files (*.*)"
        )
        if filename:
            self.input_file_edit.setText(filename)
            self.input_file_path = filename

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            os.getcwd()
        )
        if folder:
            self.output_folder_edit.setText(folder)
            self.output_folder_path = folder

    def toggle_advanced(self):
        if self.show_advanced:
            self.advanced_group.hide()
            self.advanced_toggle_btn.setText("Show Advanced Options")
        else:
            self.advanced_group.show()
            self.advanced_toggle_btn.setText("Hide Advanced Options")
        self.show_advanced = not self.show_advanced

    def load_and_validate_csv(self):
        input_file = self.input_file_edit.text()
        if not input_file:
            QMessageBox.critical(self, "Error", "Please select an input CSV file.")
            return

        if not os.path.exists(input_file):
            QMessageBox.critical(self, "Error", "Selected file does not exist.")
            return

        try:
            # Load CSV
            self.contacts_df = pd.read_csv(input_file)

            # Validate structure
            validation_result = self.validate_csv_structure()

            # Display file info
            self.display_file_info(validation_result)

            if validation_result['is_valid']:
                self.process_button.setEnabled(True)
                QMessageBox.information(self, "Success", "CSV file loaded and validated successfully!")
            else:
                self.process_button.setEnabled(False)
                QMessageBox.warning(self, "Warning", "CSV structure has issues. Please check the file information below.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV file: {str(e)}")

    def validate_csv_structure(self):
        """Validate the CSV structure and return validation results"""
        result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'info': []
        }

        # Check required columns
        required_columns = ['First Name', 'Last Name', 'Account Name']
        missing_columns = [col for col in required_columns if col not in self.contacts_df.columns]

        if missing_columns:
            result['is_valid'] = False
            result['issues'].append(f"Missing required columns: {', '.join(missing_columns)}")

        # Check if Valid column exists
        if 'Valid' not in self.contacts_df.columns:
            result['warnings'].append("'Valid' column not found - will be created during processing")
        else:
            result['info'].append("'Valid' column found - existing values will be preserved")

        # Check for empty data
        if len(self.contacts_df) == 0:
            result['is_valid'] = False
            result['issues'].append("CSV file is empty")

        # Check for missing values in required columns
        for col in required_columns:
            if col in self.contacts_df.columns:
                missing_count = self.contacts_df[col].isna().sum()
                if missing_count > 0:
                    result['warnings'].append(f"Column '{col}' has {missing_count} missing values")

        # Add general info
        result['info'].append(f"Total rows: {len(self.contacts_df)}")
        result['info'].append(f"Total columns: {len(self.contacts_df.columns)}")
        result['info'].append(f"Columns: {', '.join(self.contacts_df.columns)}")

        return result

    def display_file_info(self, validation_result):
        """Display file information and validation results"""
        self.file_info_text.clear()

        # File info
        self.file_info_text.append("FILE INFORMATION:")
        self.file_info_text.append("=" * 50)

        for info in validation_result['info']:
            self.file_info_text.append(f"✓ {info}")

        # Warnings
        if validation_result['warnings']:
            self.file_info_text.append("\nWARNINGS:")
            self.file_info_text.append("=" * 50)
            for warning in validation_result['warnings']:
                self.file_info_text.append(f"⚠ {warning}")

        # Issues
        if validation_result['issues']:
            self.file_info_text.append("\nISSUES:")
            self.file_info_text.append("=" * 50)
            for issue in validation_result['issues']:
                self.file_info_text.append(f"✗ {issue}")

        # Sample data
        if len(self.contacts_df) > 0:
            self.file_info_text.append("\nSAMPLE DATA (first 3 rows):")
            self.file_info_text.append("=" * 50)
            sample_data = self.contacts_df.head(3).to_string(index=False)
            self.file_info_text.append(sample_data)

    def start_processing(self):
        """Start the processing in a separate thread"""
        if self.contacts_df is None:
            QMessageBox.critical(self, "Error", "Please load and validate a CSV file first.")
            return

        output_folder = self.output_folder_edit.text()
        if not output_folder:
            QMessageBox.critical(self, "Error", "Please select an output folder.")
            return

        # Show information about the login process
        QMessageBox.information(self, "Processing Info",
            "Processing will start in a separate thread.\n\n"
            "A browser window will open for LinkedIn login.\n"
            "You may need to log in manually if cookies are not available.\n\n"
            "The GUI will remain responsive during processing.\n"
            "You can monitor progress in the progress area below.")

        # Disable buttons during processing
        self.process_button.setEnabled(False)
        self.load_button.setEnabled(False)

        # Show stop button
        self.stop_button.setEnabled(True)
        self.stop_button.show()
        self.process_button.hide()

        # Reset stop flag
        self.stop_processing_flag = False
        self.stop_event.clear()

        # Show progress frame
        self.progress_group.show()
        self.progress_bar.setRange(0, 0)  # Start indeterminate progress

        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_contacts)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def process_contacts(self):
        """Process contacts in a separate thread - NO GUI CALLS HERE"""
        try:
            # Create output file path
            output_file = os.path.join(self.output_folder_edit.text(), 'contacts_validated.csv')

            # Copy the dataframe to avoid modifying the original
            working_df = self.contacts_df.copy()

            # Ensure Valid column exists
            if 'Valid' not in working_df.columns:
                working_df['Valid'] = None
            else:
                working_df['Valid'] = working_df['Valid'].astype('object')

            # Apply start row and limit
            start_row = self.start_row_spin.value()
            limit = self.limit_spin.value()

            if start_row > 0 or limit > 0:
                end_row = len(working_df)
                if limit > 0:
                    end_row = min(start_row + limit, len(working_df))
                working_df = working_df.iloc[start_row:end_row].copy()

            # Process contacts
            self.thread_safe_log("Starting LinkedIn contact validation...")
            self.thread_safe_log(f"Processing {len(working_df)} contacts")
            self.thread_safe_log(f"Batch size: {self.batch_size_spin.value()}")
            self.thread_safe_log(f"Delay between batches: {self.delay_spin.value()} seconds")
            self.thread_safe_log("=" * 50)

            # Define save callback
            def save_progress(df):
                try:
                    df.to_csv(output_file, index=False)
                    self.thread_safe_log(f"Progress saved to: {output_file}")
                except Exception as e:
                    self.thread_safe_log(f"Error saving progress: {e}")

            # Call the processing function with callbacks
            processed_df = process_contacts_batch(
                working_df,
                batch_size=self.batch_size_spin.value(),
                delay_between_batches=self.delay_spin.value(),
                log_callback=self.thread_safe_log,  # Use thread-safe logging
                save_callback=save_progress,
                stop_flag=self.stop_event
            )

            # Save the final results
            try:
                processed_df.to_csv(output_file, index=False)
            except Exception as e:
                self.thread_safe_log(f"Error saving final results: {e}")

            self.thread_safe_log("=" * 50)
            self.thread_safe_log(f"Processing completed!")
            self.thread_safe_log(f"Results saved to: {output_file}")

            # Show completion message
            self.thread_safe_success(f"Processing completed!\nResults saved to:\n{output_file}")

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.thread_safe_log(error_msg)
            self.thread_safe_error(error_msg)

        finally:
            # Signal completion
            self.thread_safe_finish()

    def thread_safe_log(self, message):
        """Thread-safe logging method"""
        try:
            self.message_queue.put(("log", message))
        except Exception as e:
            print(f"Error queuing log message: {e}")

    def thread_safe_success(self, message):
        """Thread-safe success message"""
        try:
            self.message_queue.put(("success", message))
        except Exception as e:
            print(f"Error queuing success message: {e}")

    def thread_safe_error(self, message):
        """Thread-safe error message"""
        try:
            self.message_queue.put(("error", message))
        except Exception as e:
            print(f"Error queuing error message: {e}")

    def thread_safe_finish(self):
        """Thread-safe finish signal"""
        try:
            self.message_queue.put(("finished", None))
        except Exception as e:
            print(f"Error queuing finish message: {e}")

    def append_log(self, message):
        """Append message to progress text (called from main thread)"""
        self.progress_text.append(message)
        # Auto-scroll to bottom
        cursor = self.progress_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.progress_text.setTextCursor(cursor)

    def show_success(self, message):
        """Show success message (called from main thread)"""
        QMessageBox.information(self, "Success", message)

    def show_error(self, message):
        """Show error message (called from main thread)"""
        QMessageBox.critical(self, "Error", message)

    def finish_processing(self):
        """Clean up after processing is complete"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.progress_group.hide()
        self.process_button.setEnabled(True)
        self.load_button.setEnabled(True)

        # Hide stop button and show process button
        self.stop_button.hide()
        self.process_button.show()

        # Reset stop flag
        self.stop_processing_flag = False
        self.stop_event.clear()

    def stop_processing(self):
        """Stop the processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_processing_flag = True
            self.stop_event.set()
            self.thread_safe_log("Stopping processing... Please wait for current operation to complete.")
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle application close event"""
        if self.message_processor.isRunning():
            self.message_processor.stop()
            self.message_processor.wait()
        event.accept()

def main():
    try:
        app = QApplication(sys.argv)

        # Set application style
        app.setStyle('Fusion')

        window = LinkedInScraperGUI()
        window.show()

        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error in GUI: {e}")
        # Try to show error in a simple message box if possible
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Fatal Error")
            msg_box.setText(f"The application encountered a fatal error:\n{e}")
            msg_box.exec()
        except:
            print("Could not show error dialog")

if __name__ == "__main__":
    main()