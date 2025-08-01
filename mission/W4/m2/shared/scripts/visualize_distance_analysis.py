import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import sys

def visualize_distance_analysis(file_path, output_dir):
    """Generates and saves visualization for distance_analysis.csv."""
    df = pd.read_csv(file_path)
    distance_order = [
        '0-1 miles', '1-2 miles', '2-3 miles', '3-4 miles', '4-5 miles',
        '5-10 miles', '10-15 miles', '15-20 miles', '20-25 miles',
        '25-30 miles', '30+ miles'
    ]
    df['distance_category'] = pd.Categorical(df['distance_category'], categories=distance_order, ordered=True)
    df = df.sort_values('distance_category')

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(14, 18))
    fig.suptitle('Distance-based Analysis of Taxi Trips', fontsize=16)

    # 1. Number of Users by Distance Category
    sns.barplot(ax=axes[0], x='distance_category', y='num_users', data=df, palette='viridis')
    axes[0].set_title('Number of Users by Distance Category')
    axes[0].set_xlabel('Distance Category')
    axes[0].set_ylabel('Number of Users')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # 2. Average Base Passenger Fare by Distance Category
    sns.barplot(ax=axes[1], x='distance_category', y='avg_base_passenger_fare', data=df, palette='plasma')
    axes[1].set_title('Average Base Passenger Fare by Distance Category')
    axes[1].set_xlabel('Distance Category')
    axes[1].set_ylabel('Average Fare ($)')
    axes[1].tick_params(axis='x', rotation=45)

    # 3. Average Tips by Distance Category
    sns.barplot(ax=axes[2], x='distance_category', y='avg_tips', data=df, palette='magma')
    axes[2].set_title('Average Tips by Distance Category')
    axes[2].set_xlabel('Distance Category')
    axes[2].set_ylabel('Average Tips ($)')
    axes[2].tick_params(axis='x', rotation=45)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    output_filename = os.path.splitext(os.path.basename(file_path))[0] + '.png'
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path)
    plt.close(fig)
    print(f"Graph for {os.path.basename(file_path)} saved to {output_path}")
    return output_path

def visualize_scorecard(file_path, output_dir, df):
    """Generates and saves a scorecard visualization for single-row data."""
    numeric_cols = df.select_dtypes(include='number').columns
    num_metrics = len(numeric_cols)
    
    if num_metrics == 0:
        print(f"Skipping scorecard for {os.path.basename(file_path)}: No numeric data.")
        return None

    fig, axes = plt.subplots(1, num_metrics, figsize=(5 * num_metrics, 4), squeeze=False)
    fig.suptitle(f'Key Metrics for {os.path.basename(file_path)}', fontsize=20, y=1.05)

    for i, col in enumerate(numeric_cols):
        ax = axes[0, i]
        value = df[col].iloc[0]
        ax.text(0.5, 0.6, col, ha='center', va='center', fontsize=15, weight='bold')
        ax.text(0.5, 0.3, f'{value:,.2f}', ha='center', va='center', fontsize=24, color='darkblue')
        ax.axis('off')
        ax.set_facecolor('#f0f0f0')
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.tight_layout()
    
    output_filename = os.path.splitext(os.path.basename(file_path))[0] + '.png'
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Scorecard for {os.path.basename(file_path)} saved to {output_path}")
    return output_path

def visualize_generic_csv(file_path, output_dir):
    """Generates and saves a generic visualization for a CSV file."""
    try:
        df = pd.read_csv(file_path)
        
        if df.shape[0] == 1:
            return visualize_scorecard(file_path, output_dir, df)

        if df.shape[1] < 2:
            print(f"Skipping {os.path.basename(file_path)}: not enough columns for visualization.")
            return

        x_col = df.columns[0]
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        
        if not numeric_cols:
             print(f"Skipping {os.path.basename(file_path)}: no numeric columns to plot.")
             return

        y_cols = [col for col in numeric_cols if col != x_col]
        if not y_cols:
            # If the first column is the only numeric one, use value counts for it.
            if pd.api.types.is_numeric_dtype(df[x_col]):
                 y_cols = [x_col] # Plot itself
            else:
                 print(f"Skipping {os.path.basename(file_path)}: no numeric Y-axis columns to plot against X-axis '{x_col}'.")
                 return

        num_plots = len(y_cols)
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 6 * num_plots), squeeze=False)
        fig.suptitle(f'Visualization for {os.path.basename(file_path)}', fontsize=16)

        for i, y_col in enumerate(y_cols):
            sns.barplot(ax=axes[i, 0], x=x_col, y=y_col, data=df)
            axes[i, 0].set_title(f'{y_col} by {x_col}')
            axes[i, 0].set_xlabel(x_col)
            axes[i, 0].set_ylabel(y_col)
            axes[i, 0].tick_params(axis='x', rotation=45)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + '.png'
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path)
        plt.close(fig)
        print(f"Graph for {os.path.basename(file_path)} saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"Could not process {os.path.basename(file_path)}: {e}")
    return None


def main():
    """Main function to find and visualize all CSV files."""
    # Check for test mode
    is_test_mode = '--test' in sys.argv

    script_dir = os.path.dirname(__file__)
    # 스크립트 위치가 'scripts' 폴더이므로, 상위 'local' 폴더로 이동하여 경로를 설정합니다.
    local_dir = os.path.abspath(os.path.join(script_dir, '..', 'local'))

    if is_test_mode:
        print("Running in TEST MODE: Using 'test_data' directory.")
        data_dir = os.path.join(local_dir, 'test_data')
        output_dir = data_dir # 보고서와 이미지를 'test_data' 폴더에 저장
    else:
        data_dir = os.path.join(local_dir, 'data')
        output_dir = local_dir # 보고서와 이미지를 'local' 폴더에 저장

    csv_dir = os.path.join(data_dir, 'csv')
    
    if not os.path.isdir(csv_dir):
        print(f"Error: Directory not found at {csv_dir}")
        return

    csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))

    if not csv_files:
        print(f"No CSV files found in {csv_dir}")
        return

    report_content = ["# Data Visualization Report\n\n"]
    image_paths = []

    for file_path in csv_files:
        filename = os.path.basename(file_path)
        image_path = None
        if filename == 'distance_analysis.csv':
            image_path = visualize_distance_analysis(file_path, output_dir)
        else:
            image_path = visualize_generic_csv(file_path, output_dir)
        
        if image_path:
            image_paths.append(image_path)

    # Generate Markdown report
    for image_path in image_paths:
        csv_filename = os.path.splitext(os.path.basename(image_path))[0] + '.csv'
        report_content.append(f"## {csv_filename}\n\n")
        # Markdown 파일과 이미지가 같은 폴더에 생성되므로, 상대경로를 사용합니다.
        report_content.append(f"![{csv_filename} visualization](./{os.path.basename(image_path)})\n\n")

    report_path = os.path.join(output_dir, 'report.md')
    with open(report_path, 'w') as f:
        f.write("".join(report_content))
    
    print(f"\nVisualization report generated at: {report_path}")


if __name__ == '__main__':
    main()
