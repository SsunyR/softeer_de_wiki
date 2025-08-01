#!/bin/bash

# 스크립트가 위치한 디렉토리로 이동합니다.
cd "$(dirname "$0")"

echo "Starting the data processing and visualization pipeline..."

# Step 1: Spark 분석 실행 (analyze_NYC_TLC.py)
echo "--------------------------------------------------"
echo "Step 1: Running Spark analysis..."
echo "--------------------------------------------------"
spark-submit $SPARK_HOME/local/scripts/analyze_NYC_TLC.py

# $?는 바로 직전에 실행된 명령어의 종료 코드를 담고 있습니다. 0이 아니면 에러입니다.
if [ $? -ne 0 ]; then
    echo "Error: Spark analysis (analyze_NYC_TLC.py) failed."
    exit 1
fi
echo "Step 1: Spark analysis completed successfully."
echo ""


# Step 2: Parquet 파일을 CSV로 변환 (make_csv.py)
echo "--------------------------------------------------"
echo "Step 2: Converting Parquet files to CSV..."
echo "--------------------------------------------------"
python3 $SPARK_HOME/local/scripts/make_csv.py

if [ $? -ne 0 ]; then
    echo "Error: CSV conversion (make_csv.py) failed."
    exit 1
fi
echo "Step 2: CSV conversion completed successfully."
echo ""


# Step 3: 데이터 시각화 및 보고서 생성 (visualize_distance_analysis.py)
echo "--------------------------------------------------"
echo "Step 3: Generating visualizations and report..."
echo "--------------------------------------------------"
python3 $SPARK_HOME/local/scripts/visualize_distance_analysis.py

if [ $? -ne 0 ]; then
    echo "Error: Visualization (visualize_distance_analysis.py) failed."
    exit 1
fi
echo "Step 3: Visualization and report generation completed successfully."
echo ""

echo "--------------------------------------------------"
echo "Pipeline finished successfully!"
echo "Check the 'local' directory for the generated images and report.md."
echo "--------------------------------------------------"
