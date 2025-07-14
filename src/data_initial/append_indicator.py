import pandas as pd
import os
from src.data_initial.calculate_kd import calculate_kd
from src.data_initial.calculate_macd import calculate_macd

def append_indicators_to_csv(input_dir='Data/kbar', output_dir='Data/kbar'):
    """
    Reads CSV files from input_dir, calculates KD and MACD, and appends them to the DataFrame,
    then saves the updated DataFrame back to the output_dir.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('_D.csv') or filename.endswith('_W.csv'): # Process daily and weekly kbar files
            file_path = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")

            try:
                df = pd.read_csv(file_path, index_col='ts', parse_dates=True)

                # Rename columns to Chinese for consistency with calculate_kd and calculate_macd
                df.rename(columns={
                    'Open': '開盤價',
                    'High': '最高價',
                    'Low': '最低價',
                    'Close': '收盤價',
                    'Volume': '成交量'
                }, inplace=True)

                # Ensure necessary columns are numeric
                for col in ['開盤價', '最高價', '最低價', '收盤價']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df.dropna(subset=['開盤價', '最高價', '最低價', '收盤價'], inplace=True)

                if df.empty:
                    print(f"Skipping {filename}: DataFrame is empty after cleaning.")
                    continue

                # Define columns to remove if they exist
                columns_to_remove = ['RSV', '%K', '%D', 'EMA_short', 'EMA_long', 'MACD', 'Signal', 'Histogram']
                df.drop(columns=[col for col in columns_to_remove if col in df.columns], inplace=True)

                # Calculate KD
                kd_df = calculate_kd(df.copy())
                # Round KD values to two decimal places
                kd_df['RSV'] = kd_df['RSV'].round(2)
                kd_df['%K'] = kd_df['%K'].round(2)
                kd_df['%D'] = kd_df['%D'].round(2)
                df = pd.concat([df, kd_df], axis=1)

                # Calculate MACD
                macd_df = calculate_macd(df.copy())
                # Round MACD values to two decimal places
                macd_df['MACD'] = macd_df['MACD'].round(2)
                macd_df['Signal'] = macd_df['Signal'].round(2)
                macd_df['Histogram'] = macd_df['Histogram'].round(2)
                df = pd.concat([df, macd_df], axis=1)

                # Save the updated DataFrame
                output_file_path = os.path.join(output_dir, filename)
                df.to_csv(output_file_path)
                print(f"Indicators appended and saved to {output_file_path}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")
        else:
            print(f"Skipping {filename}: Not a daily or weekly kbar CSV.")
    print("-" * 30)

if __name__ == "__main__":
    append_indicators_to_csv()