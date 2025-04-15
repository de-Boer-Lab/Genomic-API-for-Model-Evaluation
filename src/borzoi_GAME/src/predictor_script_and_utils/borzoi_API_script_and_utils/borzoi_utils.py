# borzoi_utils.py
import pandas as pd

# Function to handle Evaluator request
# Fed into the model by Predictor

def filter_evaluator_request(simplified_targets_df, request_type, cell_type, molecule=None):
    
    """
    Filters evaluator request based on assay type, cell type, and molecule.
    
    Args:
        simplified_targets_df (pd.DataFrame): DataFrame containing simplified target data.
        request_type (str): Requested type of prediction:
            - "accessibility": Uses ATAC and DNASE (concatenated)
            - "expression", "expression_mrna", "expression_pol1", "expression_pol3": Uses RNA
            - "expression_pol2": Uses CAGE (with RNA fallback)
            - "binding_{molecule}": Uses CHIP assay with specified molecule.
            - ("all_tracks": Return all available tracks. Overrides the provided cell type.)
        cell_type (str): Requested cell type for prediction.
        molecule (str, optional): TF binding/ histone modification molecule for ChIP-Seq requests.
        
    Returns:
        DataFrame: Filtered tracks from simplified_targets_df or an error message string if no tracks are found.
    """
    request_error_msg = f"Request Error: No requested tracks in the requested type {request_type}\
                        \n and cell type {cell_type} found."
    
    print(f"Received evaluator request from Predictor to filter desired tracks\
           \n Type Requested: {request_type},\
           \n Cell Type: {cell_type}")
    
    # Normalize inputs to lowercase for case-insensitive handling
    request_type = request_type.lower() if request_type else None
    cell_type = cell_type.lower() if cell_type else None
    
    # Special case: if request_type is "all_tracks", return all available tracks, no matter the cell type
    if request_type == "all_tracks":
        print("All tracks request detected: returning all available tracks for prediction.")
        return simplified_targets_df
    
    # Define TF binding/ histone modification molecule for ChIP-Seq
    molecule = request_type.split("_")[1] if request_type.startswith("binding_") else None
    molecule = molecule.lower() if molecule else None
    print(f"TF Binding/ Histone Modification (if any, else None): {molecule}")
    
    # 1. Accessibility (Parse both, ATAC and DNASE, tracks and concatenate)
    if request_type == "accessibility":
        print(f"Parsing both, ATAC and DNASE, tracks for cell type provided: {cell_type}")
        atac_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'ATAC') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        if atac_tracks.empty:
            # return atac_tracks
            print(f"No matching cell types in ATAC-seq assay for cell type: {cell_type}; checking DNASE...")
            
        dnase_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'DNASE') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ] 
        if dnase_tracks.empty:
            print(f"No matching cell types in DNase assay for cell type: {cell_type}.")
        
        # Now concatenate the ATAC and DNASE tracks for the same cell_type
        combined_tracks = pd.concat([atac_tracks, dnase_tracks])
        return combined_tracks if not combined_tracks.empty else request_error_msg
    
    # 2. Expression (RNA for all request_type, except "expression_pol2")
    elif request_type in ["expression", "expression_mrna", "expression_pol1", "expression_pol3"]:
        rna_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'RNA') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        return rna_tracks if not rna_tracks.empty else request_error_msg
        
    # 3. Expression Pol2 (Parse CAGE with RNA as fallback)
    elif request_type == "expression_pol2":
        cage_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'CAGE') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        if not cage_tracks.empty:
            return cage_tracks
        
        # Fallback to RNA if no CAGE tracks for requested cell_type
        print("No matching cell types in CAGE assay type. Falling back to RNA assay.")
        rna_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'RNA') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        return rna_tracks if not rna_tracks.empty else request_error_msg
            
    # 4. Binding -- binding_{molecule} 
    # (Parse CHIP assays, filter out TF binding/ histone modification molecule and cell_type)
    elif request_type.startswith("binding_"):
        chip_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'CHIP') &
            (simplified_targets_df['Molecule'].str.lower() == molecule) &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        return chip_tracks if not chip_tracks.empty else request_error_msg
    
    # Invalid request type
    else:
        raise ValueError(f"Invalid request type {request_type}")