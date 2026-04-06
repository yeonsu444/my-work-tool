import streamlit as st
import pandas as pd
import re

# 시간 변환 함수 (안정성 강화)
def convert_to_seconds(time_val):
    if pd.isna(time_val) or str(time_val).strip() == "":
        return 0
    try:
        # 엑셀 숫자 형식 (1 = 24시간인 경우)
        if isinstance(time_val, (int, float)):
            return float(time_val) * 86400
        
        time_str = str(time_val).strip()
        # 숫자와 구분자(: .) 외의 문자가 있으면 제거
        time_str = re.sub(r'[^0-9:.]', '', time_str)
        
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
    seconds = max(0, int(seconds)) # 음수 방지
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

st.set_page_config(page_title="Grouped Work Tracker", layout="wide")
st.title("📊 이벤트별 작업자 분석")

files = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx", "xls"], accept_multiple_files=True)

if files:
    all_data_list = []
    
    for f in files:
        try:
            # 엔진 지정(openpyxl) 및 데이터 로드
            df = pd.read_excel(f, engine='openpyxl')
            
            # 열 개수 체크 (최소 16개 열이 필요한 상황)
            if df.shape[1] < 16:
                st.error(f"⚠️ '{f.name}' 파일의 열 개수가 부족합니다. (현재 {df.shape[1]}개, 최소 16개 필요)")
                continue

            temp_df = pd.DataFrame({
                'Event_ID': df.iloc[:, 1].astype(str).str.strip(),
                'Worker': df.iloc[:, 11].astype(str).str.strip(),
                'Seconds': df.iloc[:, 15].apply(convert_to_seconds)
            })
            
            # 유효 데이터만 필터링
            temp_df = temp_df[temp_df['Event_ID'] != "nan"]
            all_data_list.append(temp_df)
            
        except Exception as e:
            st.error(f"❌ {f.name} 처리 중 오류 발생: {e}")

    if all_data_list:
        master_df = pd.concat(all_data_list, ignore_index=True)

        # 그룹화 계산
        grouped = master_df.groupby(['Event_ID', 'Worker'])['Seconds'].agg(['count', 'sum']).reset_index()
        event_total = master_df.groupby('Event_ID')['Seconds'].agg(['count', 'sum']).reset_index()
        
        final_df = pd.merge(grouped, event_total, on='Event_ID', suffixes=('_worker', '_event'))

        # 포맷 정리
        final_df['이벤트 총 누적시간'] = final_df['sum_event'].apply(format_seconds_to_time)
        final_df['작업자별 누적 시간'] = final_df['sum_worker'].apply(format_seconds_to_time)
        
        result = final_df[[
            'Event_ID', 'count_event', '이벤트 총 누적시간', 
            'Worker', 'count_worker', '작업자별 누적 시간'
        ]].copy()
        
        result.columns = ['이벤트', '이벤트 총 개수', '이벤트 총 누적시간', '작업자 이름', '작업자별 건수', '작업자별 누적 시간']

        # 시각적 병합 처리
        result = result.sort_values(by=['이벤트', '작업자 이름'])
        result.loc[result['이벤트'].duplicated(), ['이벤트', '이벤트 총 개수', '이벤트 총 누적시간']] = ""

        st.subheader("🚀 분석 결과")
        st.dataframe(result, use_container_width=True) # st.table보다 대용량에 적합한 st.dataframe 추천

        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 전체 데이터 다운로드(CSV)", data=csv, file_name="total_data.csv")
    else:
        st.warning("분석할 수 있는 유효한 데이터가 없습니다.")
