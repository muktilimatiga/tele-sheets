import pandas as pd

# === Define your input files ===
file_a_path = "file_a.xlsx"  # Multi-sheet file
file_b_path = "file_b.xlsx"  # Reference file (1 sheet only)

# === Load File B ===
# We're assuming File B has relevant columns in position: C (index 2), D (index 3), E (index 4)
file_b = pd.read_excel(file_b_path, header=None)
file_b.columns = file_b.columns.astype(str)

# Extract matching columns from File B
file_b_match = file_b[[2, 3, 4]].copy()  # Columns C, D, E (0-based index)
file_b_match.columns = ['user', 'pass', 'note']

# === Load all sheets from File A ===
file_a = pd.read_excel(file_a_path, sheet_name=None, header=None)

output_sheets = {}

for sheet_name, df in file_a.items():
    df = df.copy()

    try:
        # Try to access column B and C (index 1 and 2)
        match_df = df[[1, 2]].copy()  # File A: columns B and C
        match_df.columns = ['user', 'pass']

        # Merge with File B based on 'user' and 'pass'
        merged = pd.merge(match_df, file_b_match, on=['user', 'pass'], how='left')

        # Add matched note to the original DataFrame
        df['Note_From_File_B'] = merged['note']
    except Exception as e:
        print(f"⚠️ Skipping sheet '{sheet_name}': {e}")
        df['Note_From_File_B'] = None  # Still include the column for consistency

    # Save this sheet's updated DataFrame
    output_sheets[sheet_name] = df

# === Write all updated sheets to a new Excel file ===
with pd.ExcelWriter("matched_output.xlsx", engine="openpyxl") as writer:
    for sheet_name, updated_df in output_sheets.items():
        updated_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

print("✅ Done! Output saved as 'matched_output.xlsx'")
