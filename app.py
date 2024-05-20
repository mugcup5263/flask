import discord
import requests
import asyncio
from datetime import datetime

# 토큰
TOKEN = 'MTIzMjI0MTIwNzkwMDYzOTMyNA.GEz5Ab.zv5ViQXRCcg3AUOIXsX1-dCB8GZ0IwQpHSLUqI'

# 인증키
AUTH_KEY = '96bce23c5d8b4e50b54b37a3ac3801ac'

# 사용자 학교정보 저장 딕셔너리
registered_schools = {}

# 제외할 단어 목록
exclude_words = ['<br/>']

# 클라이언트 초기화
intents = discord.Intents().all()
client = discord.Client(intents=intents)

def filter_meals(meal_str):
    """특정 단어를 제외한 급식 메뉴를 반환"""
    for word in exclude_words:
        meal_str = meal_str.replace(word, '')
    return meal_str

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 사용자가 '!학교등록' 명령을 입력하면 학교를 등록
    if message.content.startswith('!학교등록'):
        # 등록할 학교명을 사용자에게 입력받음
        await message.channel.send("등록할 학교명을 입력하세요.")
        try:
            # 학교명을 입력
            school_name = await client.wait_for('message', timeout=30.0, check=lambda m: m.author == message.author)
            school_name = school_name.content
            
            # 학교 기본정보 검색
            school_info_url = f"https://open.neis.go.kr/hub/schoolInfo?KEY={AUTH_KEY}&Type=json&SCHUL_NM={school_name}"
            school_info_response = requests.get(school_info_url)
            school_info_data = school_info_response.json()
            
            if 'schoolInfo' in school_info_data:
                school_info = school_info_data['schoolInfo'][1]['row'][0]
                atpt_ofcdc_sc_code = school_info['ATPT_OFCDC_SC_CODE']
                sd_schul_code = school_info['SD_SCHUL_CODE']
                
                registered_schools[message.author.id] = {
                    'school_name': school_name,
                    'auth_key': AUTH_KEY,
                    'atpt_ofcdc_sc_code': atpt_ofcdc_sc_code,
                    'sd_schul_code': sd_schul_code
                }
                
                await message.channel.send(f"{school_name} 학교가 등록되었습니다.")
            else:
                await message.channel.send("학교 정보를 찾을 수 없습니다. 다시 시도해주세요.")
        except asyncio.TimeoutError:
            await message.channel.send("시간이 초과되었습니다. 다시 시도해주세요.")

    # 사용자가 '!급식' 명령을 입력하면 등록된 학교의 급식 정보 가져옴
    elif message.content.startswith('!급식'):
        # 등록된 학교 정보가 있는지 확인
        if message.author.id in registered_schools:
            school_info = registered_schools[message.author.id]
            # 날짜 확인
            try:
                date = message.content.split()[1]
                datetime.strptime(date, "%Y%m%d")  # 유효한 날짜 형식인지 확인
            except (IndexError, ValueError):
                date = datetime.now().strftime("%Y%m%d")

            # 학교알리미 API를 호출하여 급식 정보를 가져옴
            url = (f"https://open.neis.go.kr/hub/mealServiceDietInfo"
                   f"?KEY={school_info['auth_key']}&Type=json"
                   f"&ATPT_OFCDC_SC_CODE={school_info['atpt_ofcdc_sc_code']}"
                   f"&SD_SCHUL_CODE={school_info['sd_schul_code']}"
                   f"&MLSV_YMD={date}")
            response = requests.get(url)
            data = response.json()
            
            try:
                meal_info = data['mealServiceDietInfo'][1]['row']
                meal_message = ""
                for meal in meal_info:
                    meal_type = meal['MMEAL_SC_NM']  # 조식, 중식, 석식
                    meals = filter_meals(meal['DDISH_NM'])
                    meal_message += f"{meal_type}: {meals}\n"
                await message.channel.send(f"{school_info['school_name']}의 {date} 급식 정보:\n{meal_message}")
            except KeyError:
                await message.channel.send("오늘은 학교가는날이 아니네요!")
        else:
            await message.channel.send("등록된 학교가 없습니다. 먼저 '!학교등록' 명령을 사용하여 학교를 등록해주세요.")

client.run(TOKEN)
