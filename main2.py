import streamlit as st
import pandas as pd
import re

# 시간 변환 함수: 엑셀 숫자 포맷 및 HH:MM:SS 문자열 지원
def convert_to_seconds(time_val):
    if pd.isna(time_val) or time_val == "":
        return 0
    try:
        # 엑셀 숫자 포맷 (1.0 = 24시간)
        if isinstance(time_val, (int, float)):
            return time_val * 86400
        
        # 문자열 포맷 (HH:MM:SS)
        time_str = str(time_val).strip()
        parts = list(map(int, re.split('[:.]', time_str)))
        if len(parts) == 3: # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2: # MM:SS
            return parts[0] * 60 + parts[1]
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
st.set_page_config(page_title="Total Work Tracker", layout="wide")
st.title("📊 통합 작업량 분석기")
st.markdown("B열(이벤트), L열(작업자), P열(시간) 데이터를 기반으로 합계를 산출합니다.")

# 파일 업로더
files = st.file_uploader("엑셀 파일을 모두 선택하세요", type=["xlsx", "xls"], accept_multiple_files=True)

if files:
    all_data_list = []
    
    for f in files:
        try:
            # B(1), L(11), P(15) 열 추출 (header는 0번 행)
            df = pd.read_excel(f)
            
            # 필요한 데이터만 추출하여 정리
            temp_df = pd.DataFrame({
                'Event_ID': df.iloc[:, 1].astype(str).str.strip(), # B열
                'Worker': df.iloc[:, 11].astype(str).str.strip(),   # L열
                'Seconds': df.iloc[:, 15].apply(convert_to_seconds) # P열
            })
            
            # 시간 데이터가 없는 행(공백 전까지라는 조건 반영)은 필터링
            temp_df = temp_df[temp_df['Seconds'] > 0]
            all_data_list.append(temp_df)
            
        except Exception as e:
            st.error(f"'{f.name}' 파일 처리 중 오류 발생: {e}")

    if all_data_list:
        # 모든 파일 데이터 통합
        master_df = pd.concat(all_data_list, ignore_index=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("1️⃣ 이벤트별 총합 (B열 기준)")
            event_summary = master_df.groupby("Event_ID")["Seconds"].agg(['count', 'sum']).reset_index()
            event_summary.columns = ['Event ID', 'Count (건)', 'Total Seconds']
            event_summary["Total Duration"] = event_summary["Total Seconds"].apply(format_seconds_to_time)
            st.table(event_summary[['Event ID', 'Count (건)', 'Total Duration']])

        with col2:
            st.subheader("2️⃣ 작업자별 총합 (L열 기준)")
            worker_summary = master_df.groupby("Worker")["Seconds"].agg(['count', 'sum']).reset_index()
            worker_summary.columns = ['Worker Name', 'Count (건)', 'Total Seconds']
            worker_summary["Total Duration"] = worker_summary["Total Seconds"].apply(format_seconds_to_time)
            st.table(worker_summary[['Worker Name', 'Count (건)', 'Total Duration']])

        # 엑셀 다운로드 기능 (선택 사항)
        st.success("모든 파일 합산이 완료되었습니다!")
    else:
        st.warning("유효한 데이터가 포함된 파일을 업로드해주세요.")
