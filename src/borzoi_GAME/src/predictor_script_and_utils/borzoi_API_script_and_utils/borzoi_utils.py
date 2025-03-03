# borzoi_utils.py

request_error_msg = "Request Error: No requested assay type and cell type found."

# Function to handle Evaluator request
# Fed into the model by Predictor

def filter_evaluator_request(simplified_targets_df, request_type, cell_type, molecule=None):
    
    """
    Filters evaluator request based on assay type, cell type, and molecule.
    
    Args:
        simplified_targets_df (pd.DataFrame): DataFrame containing simplified target data
        request_type (str): Requested type of prediction (accessibility -- ATAC and DNASE;
                                                          expression -- RNA and CAGE;
                                                          binding_{molecule} -- CHIP).
        cell_type (str): Requested cell type for prediction.
        molecule (str, optional): TF binding/ histone modification molecule for ChIP-Seq requests.
        
    Returns:
        filtered tracks (list): Indices in targets_df corresponding to the filtered tracks
    """
    print(f"Received evaluator request from Predictor to filter desired tracks\
           \n Type Requested: {request_type},\
           \n Cell Type: {cell_type}")
    # Normalize inputs to lowercase for case-insensitive handling
    request_type = request_type.lower() if request_type else None
    cell_type = cell_type.lower() if cell_type else None
    
    # Define TF binding/ histone modification molecule for ChIP-Seq
    molecule = request_type.split("_")[1] if request_type.startswith("binding_") else None
    molecule = molecule.lower() if molecule else None
    print(f"TF Binding/ Histone Modification (if any, else None): {molecule}")
    
    # 1. Accessibility (Parse ATAC with DNASE as fallback)
    if request_type == "accessibility":
        atac_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'ATAC') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        if not atac_tracks.empty:
            return atac_tracks
        
        # Fallback to DNASE if no ATAC tracks for requested cell_type
        print("No matching cell types in ATAC assay type. Falling back to DNASE assay.")
        dnase_tracks = simplified_targets_df[
            (simplified_targets_df['Assay'] == 'DNASE') &
            (simplified_targets_df['Cell Type'].str.contains(cell_type, case=False, na=False))
        ]
        return dnase_tracks if not dnase_tracks.empty else request_error_msg
    
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