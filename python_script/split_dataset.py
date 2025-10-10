import pandas as pd
import argparse
import os
import math
from pathlib import Path


def split_dataset(dataset_path, output_folder, num_files):
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    if num_files <= 0:
        raise ValueError("Number of files must be greater than 0")
    
    
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    print(f"Reading dataset from: {dataset_path}")
    
    
    df = pd.read_csv(dataset_path)
    total_rows = len(df)
    
    print(f"Total rows in dataset: {total_rows}")
    print(f"Splitting into {num_files} files...")
    
    
    rows_per_file = math.ceil(total_rows / num_files)
    
    print(f"Approximate rows per file: {rows_per_file}")
    
    
    for i in range(num_files):
        start_idx = i * rows_per_file
        end_idx = min((i + 1) * rows_per_file, total_rows)
        
        
        df_chunk = df.iloc[start_idx:end_idx]
        
        
        if len(df_chunk) == 0:
            break
        
        
        filename = f"data_{i+1:04d}.csv"
        filepath = os.path.join(output_folder, filename)
        
        
        df_chunk.to_csv(filepath, index=False)
        
        print(f"Created {filename} with {len(df_chunk)} rows")
    
    print(f"\n Dataset split complete!")
    print(f"{num_files} files created in: {output_folder}")
    print(f"Total rows distributed: {total_rows}")


def main():
    
    parser = argparse.ArgumentParser(
        description="Split a dataset into multiple CSV files for data ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python split_dataset.py --dataset_path data/main_dataset.csv --output_folder raw-data --num_files 100
  python split_dataset.py -d data.csv -o raw-data -n 50
        """
    )
    
    parser.add_argument(
        '--dataset_path', '-d',
        type=str,
        required=True,
        help='Path to the main dataset CSV file'
    )
    
    parser.add_argument(
        '--output_folder', '-o',
        type=str,
        required=True,
        help='Path to the output folder (raw-data folder)'
    )
    
    parser.add_argument(
        '--num_files', '-n',
        type=int,
        required=True,
        help='Number of files to generate'
    )
    
    args = parser.parse_args()
    
    try:
        split_dataset(
            dataset_path=args.dataset_path,
            output_folder=args.output_folder,
            num_files=args.num_files
        )
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())