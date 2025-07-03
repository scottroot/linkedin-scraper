import sys
import os
import threading
import queue
import chardet
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QGroupBox, QFrame,
    QSpinBox, QDoubleSpinBox, QCheckBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

import pandas as pd

# Import the main processing functions
from app.main import process_contacts_batch
from app.logger import get_logger




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
        self.logger = get_logger()

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
                self.logger.error(f"Error processing messages: {e}")

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
        self.batch_size = 3
        self.delay = 15
        self.start_row = 0
        self.limit = 0
        self.show_advanced = False

        # Data
        self.contacts_df = None
        self.last_file_modified_time = None
        self.processing_thread = None
        self.stop_processing_flag = False
        self.stop_event = threading.Event()

        # Login confirmation mechanism
        self.login_confirmation_event = threading.Event()
        self.waiting_for_login_confirmation = False

        # Thread-safe communication queue
        self.message_queue = queue.Queue()
        self.message_processor = MessageProcessor(self.message_queue)
        self.message_processor.log_signal.connect(self.append_log)
        self.message_processor.success_signal.connect(self.show_success)
        self.message_processor.error_signal.connect(self.show_error)
        self.message_processor.finished_signal.connect(self.finish_processing)
        self.message_processor.start()

        # Logger
        self.logger = get_logger()

        # Set up file monitoring timer
        self.file_monitor_timer = QTimer()
        self.file_monitor_timer.timeout.connect(self.check_file_changes)
        self.file_monitor_timer.start(2000)  # Check every 2 seconds

        self.setup_ui()

        # Auto-load the default file if it exists
        if os.path.exists(self.input_file_path):
            print(f"Auto-loading default file: {self.input_file_path}")
            self.load_and_validate_csv()

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

        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout(file_group)

        self.input_file_edit = QLineEdit()
        self.input_file_edit.setPlaceholderText("Select a CSV file...")
        self.input_file_edit.setReadOnly(True)
        self.input_file_edit.setText(self.input_file_path)  # Set default file path

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_input_file)

        self.refresh_button = QPushButton("Reload from disk")
        self.refresh_button.clicked.connect(self.refresh_preview)

        file_layout.addWidget(QLabel("Input CSV File:"))
        file_layout.addWidget(self.input_file_edit, 1)
        file_layout.addWidget(self.browse_button)
        file_layout.addWidget(self.refresh_button)

        main_layout.addWidget(file_group)

        # File info group
        self.file_info_group = QGroupBox("File Information")
        file_info_layout = QVBoxLayout(self.file_info_group)

        self.file_info_text = QTextEdit()
        self.file_info_text.setMaximumHeight(200)
        self.file_info_text.setReadOnly(True)

        # Set monospaced font for file info text
        monospace_font = QFont("Courier New", 11)  # Use Consolas font with size 12
        self.file_info_text.setFont(monospace_font)

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
        self.batch_size_spin.setValue(15)
        batch_size_help = QLabel("(contacts per batch)")
        advanced_layout.addWidget(batch_size_label, 2, 0)
        advanced_layout.addWidget(self.batch_size_spin, 2, 1)
        advanced_layout.addWidget(batch_size_help, 2, 2)

        # Delay
        delay_label = QLabel("Delay (seconds):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(300)
        self.delay_spin.setValue(5)
        delay_help = QLabel("(between batches)")
        advanced_layout.addWidget(delay_label, 3, 0)
        advanced_layout.addWidget(self.delay_spin, 3, 1)
        advanced_layout.addWidget(delay_help, 3, 2)

        # Debug Mode
        self.debug_checkbox = QCheckBox("Enable Debug Mode")
        self.debug_checkbox.setToolTip("Enable debug logging (sets DEBUG environment variable)")
        advanced_layout.addWidget(self.debug_checkbox, 4, 0, 1, 3)

        # Bing Search Result Timeout
        bing_timeout_label = QLabel("Bing Search Timeout (seconds):")
        self.bing_timeout_spin = QSpinBox()
        self.bing_timeout_spin.setMinimum(5)
        self.bing_timeout_spin.setMaximum(120)
        self.bing_timeout_spin.setValue(20)
        bing_timeout_help = QLabel("(timeout for Bing search results)")
        advanced_layout.addWidget(bing_timeout_label, 5, 0)
        advanced_layout.addWidget(self.bing_timeout_spin, 5, 1)
        advanced_layout.addWidget(bing_timeout_help, 5, 2)

        # Search Result Match Threshold
        search_threshold_label = QLabel("Search Match Threshold:")
        self.search_threshold_spin = QDoubleSpinBox()
        self.search_threshold_spin.setMinimum(0.1)
        self.search_threshold_spin.setMaximum(1.0)
        self.search_threshold_spin.setSingleStep(0.1)
        self.search_threshold_spin.setValue(0.75)
        search_threshold_help = QLabel("(Bing/Brave search fuzzy match threshold)")
        advanced_layout.addWidget(search_threshold_label, 6, 0)
        advanced_layout.addWidget(self.search_threshold_spin, 6, 1)
        advanced_layout.addWidget(search_threshold_help, 6, 2)

        # LinkedIn Selenium Timeout
        linkedin_timeout_label = QLabel("LinkedIn Timeout (seconds):")
        self.linkedin_timeout_spin = QSpinBox()
        self.linkedin_timeout_spin.setMinimum(5)
        self.linkedin_timeout_spin.setMaximum(120)
        self.linkedin_timeout_spin.setValue(15)
        linkedin_timeout_help = QLabel("(timeout for LinkedIn page loading)")
        advanced_layout.addWidget(linkedin_timeout_label, 7, 0)
        advanced_layout.addWidget(self.linkedin_timeout_spin, 7, 1)
        advanced_layout.addWidget(linkedin_timeout_help, 7, 2)

        # LinkedIn Match Threshold
        linkedin_threshold_label = QLabel("LinkedIn Match Threshold:")
        self.linkedin_threshold_spin = QSpinBox()
        self.linkedin_threshold_spin.setMinimum(50)
        self.linkedin_threshold_spin.setMaximum(100)
        self.linkedin_threshold_spin.setValue(75)
        linkedin_threshold_help = QLabel("(company name match threshold %)")
        advanced_layout.addWidget(linkedin_threshold_label, 8, 0)
        advanced_layout.addWidget(self.linkedin_threshold_spin, 8, 1)
        advanced_layout.addWidget(linkedin_threshold_help, 8, 2)

        # Keep LinkedIn Browser Open
        self.keep_linkedin_open_checkbox = QCheckBox("Keep LinkedIn Browser Open")
        self.keep_linkedin_open_checkbox.setToolTip("Keep LinkedIn browser window visible (even if already logged in)")
        advanced_layout.addWidget(self.keep_linkedin_open_checkbox, 9, 0, 1, 3)

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

        # Login confirmation button (initially hidden)
        self.login_confirm_button = QPushButton("Confirm Logged In")
        self.login_confirm_button.clicked.connect(self.confirm_login)
        self.login_confirm_button.setEnabled(False)
        self.login_confirm_button.hide()

        # Style the button to be very noticeable - blue background with white text
        self.login_confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #0073b1;  /* LinkedIn blue */
                color: white;
                border: 2px solid #0073b1;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #005885;  /* Darker blue on hover */
                border-color: #005885;
            }
            QPushButton:pressed {
                background-color: #004471;  /* Even darker when pressed */
                border-color: #004471;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border-color: #cccccc;
            }
        """)

        progress_layout.addWidget(self.login_confirm_button)

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

            # Automatically load and validate the CSV file
            print(f"File selected: {filename}")
            self.load_and_validate_csv()

    def toggle_advanced(self):
        if self.show_advanced:
            self.advanced_group.hide()
            self.advanced_toggle_btn.setText("Show Advanced Options")
        else:
            self.advanced_group.show()
            self.advanced_toggle_btn.setText("Hide Advanced Options")
        self.show_advanced = not self.show_advanced

    def detect_file_encoding(self, file_path):
        """Detect the encoding of a file using chardet"""
        try:
            with open(file_path, 'rb') as f:
                # Read a sample of the file for encoding detection
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']

                print(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                return encoding, confidence
        except Exception as e:
            print(f"Error detecting encoding: {e}")
            return 'utf-8', 0.0

    def load_csv_with_encoding_detection(self, file_path):
        """Load CSV file with automatic encoding detection and fallback"""
        encodings_to_try = []

        # First, try to detect the encoding
        detected_encoding, confidence = self.detect_file_encoding(file_path)

        if detected_encoding and confidence > 0.7:
            encodings_to_try.append(detected_encoding)

        # Add common encodings as fallbacks
        common_encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
        for encoding in common_encodings:
            if encoding not in encodings_to_try:
                encodings_to_try.append(encoding)

        # Try each encoding
        for encoding in encodings_to_try:
            try:
                print(f"Trying to load CSV with encoding: {encoding}")
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"Successfully loaded CSV with encoding: {encoding}")
                return df, encoding
            except UnicodeDecodeError as e:
                print(f"Failed to load with encoding {encoding}: {e}")
                continue
            except Exception as e:
                print(f"Error loading with encoding {encoding}: {e}")
                continue

        # If all encodings fail, raise an error
        raise ValueError(f"Could not load CSV file with any of the attempted encodings: {encodings_to_try}")

    def check_file_modified(self, file_path):
        """Check if the file has been modified since last load"""
        if not os.path.exists(file_path):
            return False

        current_modified_time = os.path.getmtime(file_path)

        if self.last_file_modified_time is None:
            self.last_file_modified_time = current_modified_time
            return True

        if current_modified_time > self.last_file_modified_time:
            self.last_file_modified_time = current_modified_time
            return True

        return False

    def load_and_validate_csv(self):
        input_file = self.input_file_edit.text()
        if not input_file:
            QMessageBox.critical(self, "Error", "Please select an input CSV file.")
            return

        if not os.path.exists(input_file):
            QMessageBox.critical(self, "Error", "Selected file does not exist.")
            return

        # Check if file has been modified
        file_modified = self.check_file_modified(input_file)
        if file_modified:
            print(f"File {input_file} has been modified, reloading...")
        else:
            print(f"File {input_file} has not been modified since last load")

        try:
            # Clear the file info text first
            self.file_info_text.clear()

            # Load CSV with encoding detection
            self.contacts_df, used_encoding = self.load_csv_with_encoding_detection(input_file)
            self.used_encoding = used_encoding  # Store for display

            # Add debugging information
            print(f"Loaded CSV file: {input_file}")
            # print(f"Used encoding: {used_encoding}")
            print(f"DataFrame shape: {self.contacts_df.shape}")
            print(f"DataFrame columns: {list(self.contacts_df.columns)}")
            print(f"First few rows:")
            print(self.contacts_df.head(3))

            # Validate structure
            validation_result = self.validate_csv_structure()

            # Display file info
            self.display_file_info(validation_result)

            # Force a repaint/update of the file info text widget
            self.file_info_text.repaint()
            self.file_info_text.update()

            if validation_result['is_valid']:
                self.process_button.setEnabled(True)
                # Show encoding info in a non-blocking way
                if hasattr(self, 'used_encoding') and self.used_encoding != 'utf-8':
                    print(f"CSV loaded successfully with encoding: {self.used_encoding}")
            else:
                self.process_button.setEnabled(False)
                QMessageBox.warning(self, "Warning", "CSV structure has issues. Please check the file information below.")

        except UnicodeDecodeError as e:
            error_msg = f"Failed to load CSV file due to encoding issues: {str(e)}\n\nPlease ensure your CSV file is saved with UTF-8 encoding."
            QMessageBox.critical(self, "Encoding Error", error_msg)
            print(f"Encoding error loading CSV: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            error_msg = f"Failed to load CSV file: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            print(f"Error loading CSV: {e}")
            import traceback
            traceback.print_exc()

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
        # Clear the text widget completely
        self.file_info_text.clear()

        # Add debugging information
        print(f"Displaying file info for DataFrame with shape: {self.contacts_df.shape}")
        print(f"DataFrame head:")
        print(self.contacts_df.head(3))

        # File info
        self.file_info_text.append("FILE INFORMATION:")
        self.file_info_text.append("=" * 70)

        for info in validation_result['info']:
            self.file_info_text.append(f"✓ {info}")

        # Warnings
        if validation_result['warnings']:
            self.file_info_text.append("\nWARNINGS:")
            self.file_info_text.append("=" * 70)
            for warning in validation_result['warnings']:
                self.file_info_text.append(f"⚠ {warning}")

        # Issues
        if validation_result['issues']:
            self.file_info_text.append("\nISSUES:")
            self.file_info_text.append("=" * 70)
            for issue in validation_result['issues']:
                self.file_info_text.append(f"✗ {issue}")

        # Sample data
        if len(self.contacts_df) > 0:
            self.file_info_text.append("\nSAMPLE DATA (first 3 rows):")
            self.file_info_text.append("=" * 70)

            # Get the first 3 rows
            sample_df = self.contacts_df.head(3)

            # Define column widths dynamically based on existing columns
            col_widths = {}
            for col in sample_df.columns:
                if col == "First Name":
                    col_widths[col] = 14
                elif col == "Last Name":
                    col_widths[col] = 14
                elif col == "Account Name":
                    col_widths[col] = 16
                elif col == "Valid":
                    col_widths[col] = 8
                elif col == "Note":
                    col_widths[col] = 8
                else:
                    # For any other columns, use a reasonable default width
                    col_widths[col] = max(len(col), 12)

            # Convert all to strings and pad
            padded_df = sample_df.copy()
            for col, width in col_widths.items():
                padded_df[col] = padded_df[col].astype(str).apply(lambda x: x.ljust(width))

            # Build header
            header = "  ".join(col.ljust(col_widths[col]) for col in padded_df.columns)
            self.file_info_text.append(header)

            # Build each row
            for _, row in padded_df.iterrows():
                row_str = "  ".join(row[col] for col in padded_df.columns)
                self.file_info_text.append(row_str)
        # Force the widget to update
        self.file_info_text.repaint()
        self.file_info_text.update()

        # Scroll to top
        cursor = self.file_info_text.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.file_info_text.setTextCursor(cursor)

    def start_processing(self):
        """Start the processing in a separate thread"""
        if self.contacts_df is None:
            QMessageBox.critical(self, "Error", "Please select a CSV file first.")
            return

        # Reset session log file to create a new log file for this run
        from app.logger import reset_session_log_file, get_session_log_file
        reset_session_log_file()

        # Log which file will be used for this session
        log_file = get_session_log_file()
        self.thread_safe_log(f"Logging to: {os.path.basename(log_file)}")

        # Set DEBUG environment variable if debug mode is enabled
        if self.debug_checkbox.isChecked():
            os.environ['DEBUG'] = 'true'
            self.thread_safe_log("Debug mode enabled - DEBUG environment variable set to 'true'")
            # Refresh logger levels to apply debug mode to existing loggers
            from app.logger import refresh_logger_levels
            refresh_logger_levels()
        else:
            # Remove DEBUG environment variable if it exists
            os.environ.pop('DEBUG', None)
            # Refresh logger levels to apply normal mode to existing loggers
            from app.logger import refresh_logger_levels
            refresh_logger_levels()

        # # Show information about the login process
        # QMessageBox.information(self, "Processing Info",
        #     "Processing will start in a separate thread.\n\n"
        #     "A browser window will open for LinkedIn login.\n"
        #     "If you need to log in manually, you'll see a 'Confirm Logged In' button in the progress area.\n"
        #     "Simply click that button after you've successfully logged in.\n\n"
        #     "The GUI will remain responsive during processing.\n"
        #     "You can monitor progress in the progress area below.")

        # Collapse advanced options panel
        if self.show_advanced:
            self.advanced_group.hide()
            self.advanced_toggle_btn.setText("Show Advanced Options")
            self.show_advanced = False

        # Disable buttons during processing
        self.process_button.setEnabled(False)

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
            # Use the original input file as the output file
            output_file = self.input_file_edit.text()

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

            # Log the settings being applied
            self.thread_safe_log(f"Start Row: {start_row}")
            self.thread_safe_log(f"Limit: {limit} (0 = no limit)")

            if start_row > 0 or limit > 0:
                end_row = len(working_df)
                if limit > 0:
                    end_row = min(start_row + limit, len(working_df))
                    self.thread_safe_log(f"Applying limit: processing rows {start_row+1} to {end_row} (out of {len(self.contacts_df)} total rows)")
                working_df = working_df.iloc[start_row:end_row].copy()
            else:
                self.thread_safe_log(f"No limit applied: processing all {len(working_df)} rows")

            # Process contacts
            self.thread_safe_log("Starting LinkedIn contact validation...")
            self.logger.info("Starting LinkedIn contact validation...")

                        # Log debug mode status
            if os.getenv('DEBUG'):
                self.thread_safe_log("DEBUG MODE: Debug logging is enabled")
                self.logger.debug("Debug logging is enabled")

            # Log advanced settings
            self.thread_safe_log("ADVANCED SETTINGS:")
            self.thread_safe_log(f"  Bing Search Timeout: {self.bing_timeout_spin.value()} seconds")
            self.thread_safe_log(f"  Search Match Threshold: {self.search_threshold_spin.value()}")
            self.thread_safe_log(f"  LinkedIn Timeout: {self.linkedin_timeout_spin.value()} seconds")
            self.thread_safe_log(f"  LinkedIn Match Threshold: {self.linkedin_threshold_spin.value()}%")
            self.thread_safe_log(f"  Keep LinkedIn Browser Open: {self.keep_linkedin_open_checkbox.isChecked()}")

            self.thread_safe_log(f"Processing {len(working_df)} contacts")
            self.logger.info(f"Processing {len(working_df)} contacts")
            self.thread_safe_log(f"Batch size: {self.batch_size_spin.value()}")
            self.logger.info(f"Batch size: {self.batch_size_spin.value()}")
            self.thread_safe_log(f"Delay between batches: {self.delay_spin.value()} seconds")
            self.logger.info(f"Delay between batches: {self.delay_spin.value()} seconds")
            self.thread_safe_log("=" * 50)
            self.logger.info("=" * 50)

            # Define save callback
            def save_progress(df):
                try:
                    df.to_csv(output_file, index=False, encoding='utf-8')
                    self.thread_safe_log(f"Progress saved to: {output_file}")
                    self.logger.info(f"Progress saved to: {output_file}")
                except Exception as e:
                    self.thread_safe_log(f"Error saving progress: {e}")
                    self.logger.error(f"Error saving progress: {e}")

            # Call the processing function with callbacks
            processed_df = process_contacts_batch(
                working_df,
                batch_size=self.batch_size_spin.value(),
                delay_between_batches=self.delay_spin.value(),
                log_callback=self.thread_safe_log,  # Use thread-safe logging for GUI
                save_callback=save_progress,
                stop_flag=self.stop_event,
                login_confirmation_callback=self.login_confirmation_callback,
                bing_timeout=self.bing_timeout_spin.value(),
                search_threshold=self.search_threshold_spin.value(),
                linkedin_timeout=self.linkedin_timeout_spin.value(),
                linkedin_threshold=self.linkedin_threshold_spin.value(),
                keep_linkedin_open=self.keep_linkedin_open_checkbox.isChecked()
            )

            # Save the final results
            try:
                processed_df.to_csv(output_file, index=False, encoding='utf-8')
            except Exception as e:
                self.thread_safe_log(f"Error saving final results: {e}")
                self.logger.error(f"Error saving final results: {e}")

            self.thread_safe_log("=" * 50)
            self.logger.info("=" * 50)
            self.thread_safe_log(f"Processing completed!")
            self.logger.info(f"Processing completed!")
            self.thread_safe_log(f"Results saved to: {output_file}")
            self.logger.info(f"Results saved to: {output_file}")

            # Show completion message
            self.thread_safe_success(f"Processing completed!\nResults saved to:\n{output_file}")

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.thread_safe_log(error_msg)
            self.logger.error(error_msg)
            self.thread_safe_error(error_msg)

        finally:
            # Signal completion
            self.thread_safe_finish()

    def thread_safe_log(self, message):
        """Thread-safe logging method"""
        try:
            self.message_queue.put(("log", message))
            # Also log to file if debug mode is enabled
            if os.getenv('DEBUG'):
                self.logger.debug(f"GUI Log: {message}")
        except Exception as e:
            self.logger.error(f"Error queuing log message: {e}")

    def thread_safe_success(self, message):
        """Thread-safe success message"""
        try:
            self.message_queue.put(("success", message))
        except Exception as e:
            self.logger.error(f"Error queuing success message: {e}")

    def thread_safe_error(self, message):
        """Thread-safe error message"""
        try:
            self.message_queue.put(("error", message))
        except Exception as e:
            self.logger.error(f"Error queuing error message: {e}")

    def thread_safe_finish(self):
        """Thread-safe finish signal"""
        try:
            self.message_queue.put(("finished", None))
        except Exception as e:
            self.logger.error(f"Error queuing finish message: {e}")

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

        # Hide stop button and show process button
        self.stop_button.hide()
        self.process_button.show()

        # Hide login confirmation button if it's visible
        self.login_confirm_button.hide()
        self.login_confirm_button.setEnabled(False)
        self.waiting_for_login_confirmation = False

        # Reset stop flag
        self.stop_processing_flag = False
        self.stop_event.clear()

    def stop_processing(self):
        """Stop the processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_processing_flag = True
            self.stop_event.set()
            self.thread_safe_log("Stopping processing... Please wait for current operation to complete.")
            self.logger.info("Stopping processing... Please wait for current operation to complete.")
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle application close event"""
        # Stop the file monitoring timer
        if hasattr(self, 'file_monitor_timer'):
            self.file_monitor_timer.stop()

        if self.message_processor.isRunning():
            self.message_processor.stop()
            self.message_processor.wait()
        event.accept()

    def showEvent(self, event):
        """Override showEvent to ensure window takes focus when shown"""
        super().showEvent(event)
        # Bring window to front and take focus
        self.raise_()
        self.activateWindow()
        # Set focus to the first input field
        self.input_file_edit.setFocus()

    def refresh_preview(self):
        """Refresh the CSV preview"""
        input_file = self.input_file_edit.text()
        if input_file and os.path.exists(input_file):
            # Force a complete reload by clearing the cached data
            self.contacts_df = None
            self.last_file_modified_time = None
            print("Forcing complete reload of CSV file...")
            self.load_and_validate_csv()
        else:
            print("No valid file selected for refresh")

    def check_file_changes(self):
        """Check for file changes and refresh the preview"""
        input_file = self.input_file_edit.text()
        if input_file and self.check_file_modified(input_file):
            print(f"File {input_file} has been modified, auto-refreshing preview...")
            self.refresh_preview()

    def confirm_login(self):
        """Handle login confirmation from GUI button"""
        if self.waiting_for_login_confirmation:
            self.login_confirmation_event.set()
            self.login_confirm_button.setEnabled(False)
            self.login_confirm_button.hide()
            self.waiting_for_login_confirmation = False
            self.thread_safe_log("Login confirmed, continuing with processing...")

    def login_confirmation_callback(self):
        """Callback function for login confirmation - called from processing thread"""
        self.waiting_for_login_confirmation = True
        self.login_confirmation_event.clear()

        # Show the login confirmation button in the GUI
        self.login_confirm_button.setEnabled(True)
        self.login_confirm_button.show()

        # Wait for the user to click the button
        self.login_confirmation_event.wait()

def main():
    try:
        app = QApplication(sys.argv)

        # Set application style
        app.setStyle('Fusion')

        window = LinkedInScraperGUI()
        window.show()

        # Ensure window takes focus
        window.raise_()
        window.activateWindow()

        sys.exit(app.exec())
    except Exception as e:
        logger = get_logger()
        logger.error(f"Fatal error in GUI: {e}")
        # Try to show error in a simple message box if possible
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Fatal Error")
            msg_box.setText(f"The application encountered a fatal error:\n{e}")
            msg_box.exec()
        except:
            logger.error("Could not show error dialog")

if __name__ == "__main__":
    main()
