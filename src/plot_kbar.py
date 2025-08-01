import pandas as pd
import mplfinance as mpf
import os
from data_initial.calculate_kd import calculate_kd
from data_initial.calculate_macd import calculate_macd

def plot_k_charts(stock_id):
    # Define paths
    daily_data_path = os.path.join('Data', 'kbar', f'{stock_id}_D.csv')
    chart_output_dir = os.path.join('Data', 'chart')
    
    # Ensure output directory exists
    os.makedirs(chart_output_dir, exist_ok=True)

    # Read daily data
    try:
        df_daily = pd.read_csv(daily_data_path, parse_dates=['ts'], index_col='ts')
        df_daily.sort_index(inplace=True)
        df_daily.index.name = 'Date'
        df_daily.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'RSV', 'K', 'D', 'MACD', 'Signal', 'Histogram', 'MA_5', 'MA_10', 'MA_20', 'MA_60', 'MA_120']
    except FileNotFoundError:
        print(f"Daily data file not found for {stock_id}: {daily_data_path}")
        return

    # Plot daily K-line chart
    daily_chart_path = os.path.join(chart_output_dir, f'{stock_id}_Daily_K_Chart.png')
    # Calculate symmetrical Y-axis limits for MACD
    # Calculate symmetrical Y-axis limits for MACD, Signal, and Histogram individually
    macd_panel_abs_max_daily = max(
        abs(df_daily['MACD'].min()), abs(df_daily['MACD'].max()),
        abs(df_daily['Signal'].min()), abs(df_daily['Signal'].max()),
        abs(df_daily['Histogram'].min()), abs(df_daily['Histogram'].max())
    )
    macd_ylim_daily = (-macd_panel_abs_max_daily * 1.1, macd_panel_abs_max_daily * 1.1)

    signal_abs_max_daily = max(abs(df_daily['Signal'].min()), abs(df_daily['Signal'].max()))
    signal_ylim_daily = (-signal_abs_max_daily * 1.1, signal_abs_max_daily * 1.1)

    histogram_abs_max_daily = max(abs(df_daily['Histogram'].min()), abs(df_daily['Histogram'].max()))
    histogram_ylim_daily = (-histogram_abs_max_daily * 1.1, histogram_abs_max_daily * 1.1)

    apds_daily = [
        mpf.make_addplot(df_daily[['K', 'D']], panel=2, ylabel='KD'),
        mpf.make_addplot(df_daily['MACD'], panel=3, color='red', ylabel='MACD', ylim=macd_ylim_daily),
        mpf.make_addplot(df_daily['Signal'], panel=3, color='blue'),
        mpf.make_addplot(df_daily['Histogram'], type='bar', panel=3, color='gray', width=0.7, alpha=0.5)
    ]
    mpf.plot(df_daily, type='candle', style='yahoo', title=f'{stock_id} Daily K-Line Chart',
             ylabel='Price', ylabel_lower='Volume', savefig=daily_chart_path, mav=(5, 10, 20, 60, 120),
             volume=True, addplot=apds_daily)
    print(f"Daily K-line chart saved to {daily_chart_path}")

    # Convert daily data to weekly data
    df_weekly = df_daily.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    df_weekly.sort_index(inplace=True)
    df_weekly.index.name = 'Date'

    # Recalculate KD and MACD for weekly data
    df_weekly_kd = calculate_kd(df_weekly)
    df_weekly = df_weekly.join(df_weekly_kd[['RSV', '%K', '%D']])

    df_weekly_macd = calculate_macd(df_weekly)
    df_weekly = df_weekly.join(df_weekly_macd[['MACD', 'Signal', 'Histogram']])

    # Plot weekly K-line chart
    weekly_chart_path = os.path.join(chart_output_dir, f'{stock_id}_Weekly_K_Chart.png')
    # Calculate symmetrical Y-axis limits for MACD
    # Calculate symmetrical Y-axis limits for MACD, Signal, and Histogram individually
    macd_panel_abs_max_weekly = max(
        abs(df_weekly['MACD'].min()), abs(df_weekly['MACD'].max()),
        abs(df_weekly['Signal'].min()), abs(df_weekly['Signal'].max()),
        abs(df_weekly['Histogram'].min()), abs(df_weekly['Histogram'].max())
    )
    macd_ylim_weekly = (-macd_panel_abs_max_weekly * 1.1, macd_panel_abs_max_weekly * 1.1)

    signal_abs_max_weekly = max(abs(df_weekly['Signal'].min()), abs(df_weekly['Signal'].max()))
    signal_ylim_weekly = (-signal_abs_max_weekly * 1.1, signal_abs_max_weekly * 1.1)

    histogram_abs_max_weekly = max(abs(df_weekly['Histogram'].min()), abs(df_weekly['Histogram'].max()))
    histogram_ylim_weekly = (-histogram_abs_max_weekly * 1.1, histogram_abs_max_weekly * 1.1)

    apds_weekly = [
        mpf.make_addplot(df_weekly[['%K', '%D']], panel=2, ylabel='KD'),
        mpf.make_addplot(df_weekly['MACD'], panel=3, color='red', ylabel='MACD', ylim=macd_ylim_weekly),
        mpf.make_addplot(df_weekly['Signal'], panel=3, color='blue'),
        mpf.make_addplot(df_weekly['Histogram'], type='bar', panel=3, color='gray', width=0.7, alpha=0.5)
    ]
    mpf.plot(df_weekly, type='candle', style='yahoo', title=f'{stock_id} Weekly K-Line Chart',
             ylabel='Price', ylabel_lower='Volume', savefig=weekly_chart_path, mav=(5, 10, 20, 60, 120),
             volume=True, addplot=apds_weekly)
    print(f"Weekly K-line chart saved to {weekly_chart_path}")

if __name__ == "__main__":
    plot_k_charts('00894')