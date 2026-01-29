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
st.set_page_config(page_title="Detailed Work Tracker", layout="wide")
st.title("📋 이벤트별 작업자 상세 분석")

files = st.file_uploader("엑셀 파일을 업로드하세요 (다중 선택 가능)", type=["xlsx", "xls"], accept_multiple_files=True)

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

        # 1. 이벤트 + 작업자별 그룹화 (작업자별 건수 및 누적 시간)
        grouped = master_df.groupby(['Event_ID', 'Worker'])['Seconds'].agg(['count', 'sum']).reset_index()
        grouped.columns = ['이벤트', '작업자 이름', '작업자별 건수', '작업자별 초']

        # 2. 이벤트별 총계 계산 (이벤트 총 개수 및 총 누적 시간)
        event_total = master_df.groupby('Event_ID')['Seconds'].agg(['count', 'sum']).reset_index()
        event_total.columns = ['이벤트', '이벤트 총 개수', '이벤트 총 초']

        # 3. 데이터 병합 (이벤트 전체 정보 + 작업자 상세 정보)
        final_df = pd.merge(grouped, event_total, on='이벤트')

        # 4. 시간 포맷 변환 및 컬럼 순서 정리
        final_df['이벤트 총 누적시간'] = final_df['이벤트 총 초'].apply(format_seconds_to_time)
        final_df['작업자별 누적 시간'] = final_df['작업자별 초'].apply(format_seconds_to_time)

        # 최종 컬럼 순서 재배치
        result_display = final_df[[
            '이벤트', '이벤트 총 개수', '이벤트 총 누적시간', 
            '작업자 이름', '작업자별 건수', '작업자별 누적 시간'
        ]]

        # 결과 출력
        st.subheader("🚀 통합 분석 결과")
        st.dataframe(result_display, use_container_width=True) # 테이블보다 스크롤/정렬이 편한 dataframe 사용

        # 엑셀 다운로드 버튼 추가
        csv = result_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📊 결과 CSV 다운로드",
            data=csv,
            file_name="Work_Analysis_Result.csv",
            mime="text/csv",
        )
    else:
        st.warning("데이터를 읽어올 수 없습니다. 파일의 열(B, L, P) 위치를 확인해주세요.")
