import pandas as pd
import glob
import os

def format_duration(total_seconds):
    """초 단위의 시간을 [HH]:MM:SS 형식으로 변환합니다."""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def to_seconds(val):
    """다양한 형식의 시간 데이터를 초 단위로 변환합니다."""
    if pd.isna(val):
        return 0
    if isinstance(val, (int, float)):
        # 엑셀 날짜/시간 포맷은 1일이 1.0이므로 86400초를 곱함
        return val * 86400
    elif isinstance(val, str):
        try:
            parts = list(map(int, val.split(':')))
            if len(parts) == 3: # HH:MM:SS
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2: # MM:SS
                return parts[0] * 60 + parts[1]
        except:
            return 0
    elif hasattr(val, 'hour'): # datetime.time 객체인 경우
        return val.hour * 3600 + val.minute * 60 + val.second
    return 0

# 1. 모든 엑셀 파일(.xlsx) 목록 가져오기
files = glob.glob("*.xlsx")
all_data = []

print(f"총 {len(files)}개의 파일을 찾았습니다. 분석을 시작합니다...")

for file in files:
    try:
        # B열(1), L열(11), P열(15)만 읽어오기 (0부터 시작하는 인덱스 기준)
        # header=0은 첫 번째 행을 컬럼명으로 사용한다는 뜻입니다.
        df = pd.read_excel(file, usecols=[1, 11, 15], header=0)
        df.columns = ['Event_ID', 'User_Name', 'Duration']
        
        # P열(Duration)이 비어있는 행은 제외
        df = df.dropna(subset=['Duration'])
        
        # 시간을 초 단위 숫자로 변환
        df['Duration_Sec'] = df['Duration'].apply(to_seconds)
        all_data.append(df)
        print(f"성공: {file}")
    except Exception as e:
        print(f"오류 발생 ({file}): {e}")

if not all_data:
    print("분석할 데이터가 없습니다.")
else:
    # 모든 데이터를 하나로 합치기
    master_df = pd.concat(all_data, ignore_index=True)

    # 2. 이벤트별 요약 (수량 및 누적 시간)
    event_summary = master_df.groupby('Event_ID').agg(
        Total_Count=('Duration_Sec', 'count'),
        Total_Seconds=('Duration_Sec', 'sum')
    ).reset_index()
    event_summary['Total_Duration'] = event_summary['Total_Seconds'].apply(format_duration)
    
    # 3. 작업자별 요약 (수량 및 누적 시간)
    user_summary = master_df.groupby('User_Name').agg(
        Total_Count=('Duration_Sec', 'count'),
        Total_Seconds=('Duration_Sec', 'sum')
    ).reset_index()
    user_summary['Total_Duration'] = user_summary['Total_Seconds'].apply(format_duration)

    # 결과 출력 및 저장
    print("\n" + "="*50)
    print("1. 이벤트별 요약 리스트")
    print(event_summary[['Event_ID', 'Total_Count', 'Total_Duration']])
    
    print("\n" + "="*50)
    print("2. 작업자별 요약 리스트")
    print(user_summary[['User_Name', 'Total_Count', 'Total_Duration']])

    # 엑셀 파일 하나에 두 개의 시트로 저장
    with pd.ExcelWriter("Total_Analysis_Result.xlsx") as writer:
        event_summary[['Event_ID', 'Total_Count', 'Total_Duration']].to_excel(writer, sheet_name='By_Event', index=False)
        user_summary[['User_Name', 'Total_Count', 'Total_Duration']].to_excel(writer, sheet_name='By_User', index=False)
    
    print("\n" + "="*50)
    print("분석 완료! 'Total_Analysis_Result.xlsx' 파일이 생성되었습니다.")
