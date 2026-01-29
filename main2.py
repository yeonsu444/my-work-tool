import streamlit as st
import pandas as pd
import re

# 시간 변환 함수
def convert_to_seconds(time_val):
    if pd.isna(time_val) or time_val == "":
        return 0
    try:
        if isinstance(time_val, (int, float)):
            return time_val * 86400
        time_str = str(time_val).strip()
        parts = list(map(int, re.split('[:.]', time_str)))
        if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2: return parts[0] * 60 + parts[1]
    except:
        return 0
    return 0

# 초 단위를 [HH:MM:SS] 포맷으로 변경
def format_seconds_to_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# UI 설정
st.set_page_config(page_title="Grouped Work Tracker", layout="wide")
st.title("📊 이벤트별 작업자 분석 (병합 효과 적용)")

files = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx", "xls"], accept_multiple_files=True)

if files:
    all_data_list = []
    
    for f in files:
        try:
            df = pd.read_excel(f)
            temp_df = pd.DataFrame({
                'Event_ID': df.iloc[:, 1].astype(str).str.strip(), # B열
                'Worker': df.iloc[:, 11].astype(str).str.strip(),   # L열
                'Seconds': df.iloc[:, 15].apply(convert_to_seconds) # P열
            })
            temp_df = temp_df[temp_df['Seconds'] > 0]
            all_data_list.append(temp_df)
        except Exception as e:
            st.error(f"Error in {f.name}: {e}")

    if all_data_list:
        master_df = pd.concat(all_data_list, ignore_index=True)

        # 1. 그룹화 데이터 생성
        grouped = master_df.groupby(['Event_ID', 'Worker'])['Seconds'].agg(['count', 'sum']).reset_index()
        event_total = master_df.groupby('Event_ID')['Seconds'].agg(['count', 'sum']).reset_index()
        
        final_df = pd.merge(grouped, event_total, on='Event_ID', suffixes=('_worker', '_event'))

        # 2. 포맷 정리
        final_df['이벤트 총 누적시간'] = final_df['sum_event'].apply(format_seconds_to_time)
        final_df['작업자별 누적 시간'] = final_df['sum_worker'].apply(format_seconds_to_time)
        
        result = final_df[[
            'Event_ID', 'count_event', '이벤트 총 누적시간', 
            'Worker', 'count_worker', '작업자별 누적 시간'
        ]].copy()
        
        result.columns = ['이벤트', '이벤트 총 개수', '이벤트 총 누적시간', '작업자 이름', '작업자별 건수', '작업자별 누적 시간']

        # 3. 시각적 병합 처리 (중복값 제거)
        # 같은 이벤트 내에서 첫 번째 행이 아니면 값을 비움
        result.loc[result['이벤트'].duplicated(), ['이벤트', '이벤트 총 개수', '이벤트 총 누적시간']] = ""

        st.subheader("🚀 분석 결과 (중복 정보 생략)")
        # 표 형식으로 출력
        st.table(result)

        # 다운로드용 데이터는 병합 처리 전의 원본(final_df 기반)을 추천
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 전체 데이터 다운로드(CSV)", data=csv, file_name="total_data.csv")
    else:
        st.warning("분석할 데이터가 없습니다.")
