import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from typing import Optional,List,Dict
import os
from dotenv import load_dotenv
load_dotenv()
SCOPES=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive']
CREDENTIALS_PATH=os.getenv('GOOGLE_CREDENTIALS_PATH','credentials.json') 
SHEET_NAME=os.getenv('SHEET_NAME','Recruitment_Pipeline')
class SheetsConnector:
    """
    A class to handle all Google Sheets operations.
    
    Why a class and not just functions?
    - We only want to connect ONCE, not every time we read/write
    - The class "remembers" the connection (stores it in self.client)
    """
    
    def __init__(self):                                    
        """
        Constructor - runs when you create: connector = SheetsConnector()
        """
        self.client = None          
        self.sheet = None           
        self.worksheet = None       
        self._connect()             

    def _connect(self):                                       # Line 18
        """
        Establishes connection to Google Sheets.
        Private method (underscore prefix) - called internally.
        """
        try:                                                  # Line 19
            # Step 1: Create credentials object from JSON file
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                CREDENTIALS_PATH, 
                SCOPES
            )                                                 # Line 20
            
            # Step 2: Authorize gspread with these credentials
            self.client = gspread.authorize(credentials)      # Line 21
            
            # Step 3: Open the specific spreadsheet by name
            self.sheet = self.client.open(SHEET_NAME)         # Line 22
            
            # Step 4: Get the first worksheet (tab) - index 0
            self.worksheet = self.sheet.get_worksheet(0)      # Line 23
            
            print(f"✅ Connected to: {SHEET_NAME}")           # Line 24
            
        except FileNotFoundError:                             # Line 25
            raise Exception(
                f"❌ Credentials file not found at: {CREDENTIALS_PATH}\n"
                "Please download from Google Cloud Console."
            )
        except gspread.SpreadsheetNotFound:                   # Line 26
            raise Exception(
                f"❌ Spreadsheet '{SHEET_NAME}' not found.\n"
                "Make sure you shared it with the service account email!"
            )
        
    def get_all_candidates(self) -> pd.DataFrame:             
        """
        Fetches all rows from the sheet as a Pandas DataFrame.
        
        Returns:
            pd.DataFrame: All candidates with their data
        """
        # Get all data including header row
        data = self.worksheet.get_all_records()               # Line 28
        
        # Convert to DataFrame
        df = pd.DataFrame(data)                               # Line 29
        
        return df                                             
 
    def update_candidate_status(
        self, 
        email: str, 
        new_status: str,
        additional_updates: Optional[Dict[str, str]] = None   
        ) -> bool:
        """
        Updates a candidate's status (and optionally other fields) by email.
        
        Args:
            email: Candidate's email (unique identifier)
            new_status: New status value
            additional_updates: Optional dict of other columns to update
            
        Returns:
            bool: True if successful, False if candidate not found
        """
        try:
            # Find the cell containing this email
            cell = self.worksheet.find(email)                 # Line 32
            
            if cell is None:                                  # Line 33
                print(f"⚠️ Candidate with email {email} not found")
                return False
            
            row_number = cell.row                             # Line 34
            
            # Get header row to find column positions
            headers = self.worksheet.row_values(1)            # Line 35
            
            # Find the "Status" column index (1-based in gspread)
            status_col = headers.index('Status') + 1          # Line 36
            
            # Update the status cell
            self.worksheet.update_cell(row_number, status_col, new_status)  # Line 37
            
            # Handle additional updates if provided
            if additional_updates:                            # Line 38
                for column_name, value in additional_updates.items():
                    col_index = headers.index(column_name) + 1
                    self.worksheet.update_cell(row_number, col_index, value)
            
            print(f"✅ Updated {email} to status: {new_status}")
            return True
            
        except Exception as e:                                # Line 39
            print(f"❌ Error updating: {e}")
            return False
        
    def add_candidate(self, candidate_data: Dict[str, str]) -> bool:  # Line 40
        """
        Adds a new candidate row to the sheet.
        
        Args:
            candidate_data: Dict with column names as keys
                Example: {"Name": "John", "Email": "john@email.com", "Role": "Backend"}
                
        Returns:
            bool: True if successful
        """
        try:
            # Get headers to ensure correct column order
            headers = self.worksheet.row_values(1)            # Line 41
            
            # Build the row in correct order
            new_row = []                                      # Line 42
            for header in headers:
                # Get value for this column, or empty string if not provided
                value = candidate_data.get(header, '')        # Line 43
                new_row.append(value)
            
            # Append the new row at the bottom
            self.worksheet.append_row(new_row)                # Line 44
            
            print(f"✅ Added candidate: {candidate_data.get('Name', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding candidate: {e}")
            return False
        
    def get_candidates_by_status(self, status: str) -> pd.DataFrame:  # Line 45
        """
        Returns only candidates with a specific status.
        
        Args:
            status: Status to filter by (e.g., "L1_Scheduled")
            
        Returns:
            pd.DataFrame: Filtered candidates
        """
        df = self.get_all_candidates()                        # Line 46
        
        # Filter where Status column equals the requested status
        filtered_df = df[df['Status'] == status]              # Line 47
        
        return filtered_df                                    # Line 48
    
    # ============================================
    # SINGLETON INSTANCE
    # ============================================

    # Create ONE global instance to reuse across the app
    # This prevents connecting multiple times
_connector_instance: Optional[SheetsConnector] = None         # Line 49

def get_connector() -> SheetsConnector:                       # Line 50
    """
    Returns the single shared instance of SheetsConnector.
    Creates it on first call, reuses on subsequent calls.
    
    Usage:
        from utils.sheets_connector import get_connector
        connector = get_connector()
        df = connector.get_all_candidates()
    """
    global _connector_instance                                # Line 51
    
    if _connector_instance is None:                           # Line 52
        _connector_instance = SheetsConnector()               # Line 53
    
    return _connector_instance                                # Line 54