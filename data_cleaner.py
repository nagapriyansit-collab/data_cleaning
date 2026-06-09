"""
AI-based Data Cleaning Module
"""

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

class DataCleaner:
    """AI Data Cleaning Engine"""
    
    def __init__(self):
        self.imputer = SimpleImputer(strategy='mean')
        self.scaler = StandardScaler()
    
    def load_data(self, filepath):
        """Load data from file"""
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filepath.endswith(('.xlsx', '.xls')):
            return pd.read_excel(filepath)
        else:
            raise ValueError("Unsupported file format")
    
    def analyze_data(self, filepath):
        """Analyze data and return insights"""
        df = self.load_data(filepath)
        
        analysis = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns),
            'column_types': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'duplicates': len(df[df.duplicated()]),
            'memory_usage': str(df.memory_usage(deep=True).sum() / 1024**2)[:5] + ' MB',
            'numeric_summary': df.describe().to_dict(),
            'issues': self._identify_issues(df)
        }
        
        return analysis
    
    def _identify_issues(self, df):
        """Identify data quality issues"""
        issues = []
        
        # Missing values
        missing = df.isnull().sum()
        if missing.any():
            issues.append({
                'type': 'Missing Values',
                'severity': 'high',
                'details': missing[missing > 0].to_dict()
            })
        
        # Duplicates
        if df.duplicated().any():
            issues.append({
                'type': 'Duplicate Rows',
                'severity': 'medium',
                'count': len(df[df.duplicated()])
            })
        
        # Outliers (for numeric columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = len(df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))])
            if outliers > 0:
                issues.append({
                    'type': 'Outliers',
                    'column': col,
                    'severity': 'low',
                    'count': outliers
                })
        
        return issues
    
    def clean_data(self, filepath, options):
        """Clean data based on selected options"""
        df = self.load_data(filepath)
        report = {
            'original_rows': len(df),
            'original_columns': len(df.columns),
            'cleaning_steps': []
        }
        
        # Remove duplicates
        if options.get('remove_duplicates') == 'true':
            before = len(df)
            df = df.drop_duplicates()
            report['cleaning_steps'].append({
                'action': 'Remove Duplicates',
                'removed': before - len(df),
                'remaining': len(df)
            })
        
        # Handle missing values
        if options.get('handle_missing') == 'true':
            missing_strategy = options.get('missing_strategy', 'mean')
            
            # For numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                if missing_strategy == 'mean':
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                elif missing_strategy == 'median':
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
                elif missing_strategy == 'drop':
                    df = df.dropna(subset=numeric_cols)
            
            # For categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                df[categorical_cols] = df[categorical_cols].fillna('Unknown')
            
            report['cleaning_steps'].append({
                'action': 'Handle Missing Values',
                'strategy': missing_strategy,
                'remaining_missing': df.isnull().sum().sum()
            })
        
        # Remove outliers (IQR method)
        if options.get('remove_outliers') == 'true':
            before = len(df)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[(df[col] >= (Q1 - 1.5 * IQR)) & (df[col] <= (Q3 + 1.5 * IQR))]
            
            report['cleaning_steps'].append({
                'action': 'Remove Outliers',
                'method': 'IQR',
                'removed': before - len(df),
                'remaining': len(df)
            })
        
        # Remove empty columns
        if options.get('remove_empty_columns') == 'true':
            before = len(df.columns)
            df = df.dropna(axis=1, how='all')
            report['cleaning_steps'].append({
                'action': 'Remove Empty Columns',
                'removed': before - len(df.columns),
                'remaining': len(df.columns)
            })
        
        # Standardize column names
        if options.get('standardize_columns') == 'true':
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '')
            report['cleaning_steps'].append({
                'action': 'Standardize Column Names'
            })
        
        # Final report
        report['final_rows'] = len(df)
        report['final_columns'] = len(df.columns)
        report['rows_removed'] = report['original_rows'] - report['final_rows']
        report['data_quality_score'] = round((report['final_rows'] / report['original_rows'] * 100), 2) if report['original_rows'] > 0 else 0
        
        return df, report

# Initialize cleaner
cleaner = DataCleaner()
