"""
Simple Great Expectations Integration Example

This shows how to use Great Expectations alongside your pandas validation
"""

import great_expectations as gx
import pandas as pd
from pathlib import Path
import json

def validate_with_great_expectations(file_path: str):
    """
    Validate data using Great Expectations
    
    Returns:
        dict: Validation results with success status and details
    """
    
    # 1. Load data
    df = pd.read_csv(file_path)
    
    # 2. Create Great Expectations context
    context = gx.get_context()
    
    # 3. Load your expectation suite
    expectation_suite_path = Path("expectations/gym_data_quality_suite.json")
    
    # 4. Create a validator (combines data + expectations)
    try:
        # Simple validation without full GE setup
        results = {
            "success": True,
            "expectations_passed": 0,
            "expectations_failed": 0,
            "failed_expectations": []
        }
        
        # Manual GE-style validations
        # Expectation 1: Required columns exist
        required_cols = ["Age", "Gender", "Max_BPM", "Session_Duration (hours)", "BMI"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            results["success"] = False
            results["expectations_failed"] += 1
            results["failed_expectations"].append({
                "expectation_type": "expect_table_columns_to_match_set",
                "failed_columns": missing_cols
            })
        else:
            results["expectations_passed"] += 1
        
        # Expectation 2: Age in valid range
        if "Age" in df.columns:
            invalid_age = df[(df["Age"] < 18) | (df["Age"] > 100)]
            if len(invalid_age) > 0:
                results["success"] = False
                results["expectations_failed"] += 1
                results["failed_expectations"].append({
                    "expectation_type": "expect_column_values_to_be_between",
                    "column": "Age",
                    "min_value": 18,
                    "max_value": 100,
                    "unexpected_count": len(invalid_age)
                })
            else:
                results["expectations_passed"] += 1
        
        # Expectation 3: Gender values valid
        if "Gender" in df.columns:
            valid_genders = ["Male", "Female"]
            invalid_gender = df[~df["Gender"].isin(valid_genders)]
            if len(invalid_gender) > 0:
                results["success"] = False
                results["expectations_failed"] += 1
                results["failed_expectations"].append({
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "column": "Gender",
                    "value_set": valid_genders,
                    "unexpected_count": len(invalid_gender)
                })
            else:
                results["expectations_passed"] += 1
        
        # Expectation 4: Max_BPM valid
        if "Max_BPM" in df.columns:
            invalid_bpm = df[(df["Max_BPM"] < 50) | (df["Max_BPM"] > 220)]
            if len(invalid_bpm) > 0:
                results["success"] = False
                results["expectations_failed"] += 1
                results["failed_expectations"].append({
                    "expectation_type": "expect_column_values_to_be_between",
                    "column": "Max_BPM",
                    "min_value": 50,
                    "max_value": 220,
                    "unexpected_count": len(invalid_bpm)
                })
            else:
                results["expectations_passed"] += 1
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "expectations_passed": 0,
            "expectations_failed": 0
        }


def generate_html_report(validation_results: dict, output_path: str):
    """
    Generate a simple HTML report of validation results
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Validation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; }}
            .success {{ background: #27ae60; color: white; padding: 10px; margin: 10px 0; }}
            .failure {{ background: #e74c3c; color: white; padding: 10px; margin: 10px 0; }}
            .expectation {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; }}
            .passed {{ border-left: 5px solid #27ae60; }}
            .failed {{ border-left: 5px solid #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Great Expectations Validation Report</h1>
            <p>Generated: {pd.Timestamp.now()}</p>
        </div>
        
        <div class="{'success' if validation_results['success'] else 'failure'}">
            <h2>Validation {'PASSED ✅' if validation_results['success'] else 'FAILED ❌'}</h2>
            <p>Expectations Passed: {validation_results['expectations_passed']}</p>
            <p>Expectations Failed: {validation_results['expectations_failed']}</p>
        </div>
        
        <h2>Validation Details</h2>
    """
    
    for failed_exp in validation_results.get("failed_expectations", []):
        html += f"""
        <div class="expectation failed">
            <h3>❌ {failed_exp['expectation_type']}</h3>
            <p><strong>Column:</strong> {failed_exp.get('column', 'N/A')}</p>
            <p><strong>Unexpected Count:</strong> {failed_exp.get('unexpected_count', 0)}</p>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path


# Example usage in your DAG:
if __name__ == "__main__":
    # Test it
    file_path = "airflow/dags/data/good_data/data_0001.csv"
    
    # Validate
    results = validate_with_great_expectations(file_path)
    
    print(f"✅ Validation Success: {results['success']}")
    print(f"📊 Passed: {results['expectations_passed']}")
    print(f"❌ Failed: {results['expectations_failed']}")
    
    # Generate HTML report
    if not results['success']:
        report_path = "validation_report.html"
        generate_html_report(results, report_path)
        print(f"📄 HTML Report: {report_path}")
