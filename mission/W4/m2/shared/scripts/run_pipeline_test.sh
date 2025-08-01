#!/bin/bash

# 스크립트가 위치한 디렉토리로 이동합니다.
cd "$(dirname "$0")"

echo "Starting the TEST data processing and visualization pipeline..."
echo "This will use 0.1% of the full dataset."

# Step 1: Spark 분석 실행 (analyze_NYC_TLC.py --test)
echo "--------------------------------------------------"
echo "Step 1: Running Spark analysis in TEST mode..."
echo "--------------------------------------------------"
spark-submit $SPARK_HOME/local/scripts/analyze_NYC_TLC.py --test

# $?는 바로 직전에 실행된 명령어의 종료 코드를 담고 있습니다. 0이 아니면 에러입니다.
if [ $? -ne 0 ]; then
    echo "Error: Spark analysis (analyze_NYC_TLC.py) failed in test mode."
    exit 1
fi
echo "Step 1: Spark analysis completed successfully."
echo ""


# Step 2: Parquet 파일을 CSV로 변환 (make_csv.py --test)
echo "--------------------------------------------------"
echo "Step 2: Converting Parquet files to CSV in TEST mode..."
echo "--------------------------------------------------"
python3 $SPARK_HOME/local/scripts/make_csv.py --test

if [ $? -ne 0 ]; then
    echo "Error: CSV conversion (make_csv.py) failed in test mode."
    exit 1
fi
echo "Step 2: CSV conversion completed successfully."
echo ""


# Step 3: 데이터 시각화 및 보고서 생성 (visualize_distance_analysis.py --test)
echo "--------------------------------------------------"
echo "Step 3: Generating visualizations and report in TEST mode..."
echo "--------------------------------------------------"
python3 $SPARK_HOME/local/scripts/visualize_distance_analysis.py --test

if [ $? -ne 0 ]; then
    echo "Error: Visualization (visualize_distance_analysis.py) failed in test mode."
    exit 1
fi
echo "Step 3: Visualization and report generation completed successfully."
echo ""

echo "--------------------------------------------------"
echo "TEST Pipeline finished successfully!"
echo "Check the 'local/test_data' directory for the generated images and report.md."
echo "--------------------------------------------------"
