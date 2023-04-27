import openai
import requests
from bs4 import BeautifulSoup
import pandas as pd

SECRETE_KEY = 'MY_SECRET_KEY'
openai.api_key = SECRETE_KEY

def get_content(url):
    '''
    요약이 필요한 콘텐츠 본문을 크롤링
    '''
    headers={'User-Agent': 'MyUserAgent/1.0'}
    res = requests.get(url, headers=headers).text
    soup = BeautifulSoup(res, 'html.parser')
    select = soup.select('div#content div.board-content > div > span')
    content = []
    
    for select_one in select:
        block = select_one.text
        if len(block) >= 10:
            content.append(block)
    return content

def get_recap(text_list: list, 
              ton='tone: humorous, writing style: conversational'):
    '''
    주어진 텍스트의 문단 리스트들로 짧게 요약 후, 후킹 메시지와 주요 키워드를 추출
    '''
    content_renewal = ''
    
    # 본문 내용을 문단별로 요약
    for text in text_list:
        response = openai.Completion.create(
            model='text-davinci-003',
            prompt=f'다음 콘텐츠를 한 줄로 요약해줘: {text}',
            temperature=0.3,
            max_tokens = 300
        )
        content_renewal = content_renewal + ' ' + response.choices[0].text
    
    # 역할 설정 및 질문 작성
    messages = [
        [
                {'role': 'system', 'content': '주어진 내용을 짧은 후킹 메시지로 요약해주는 어시스턴트'},
                {'role': 'user', 'content': f'아래 콘텐츠로 20자 이내의 후킹 메시지를 만들어줘. {ton} \n{content_renewal}'}
        ],
        [
            {'role': 'system', 'content': '주어진 내용에서 주요 키워드를 추출해주는 어시스턴트'},
            {'role': 'user', 'content': f'다음 콘텐츠에 중요한 키워드 5개만 콤마로 구분해서 추출해줘: {content_renewal}'}
        ]
    ]
    
    # 요약(후킹) 문구 작성
    msg = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages[0],
            max_tokens=100,
            n=3
        ).choices
    msg = '\n'.join(list(map(lambda x: x.message.content, msg)))
    
    # 키워드 추출
    keywords = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages[1],
            max_tokens=100
        ).choices[0].message.content
    
    return content_renewal, msg, keywords


if __name__ == '__main__':
    # 요약할 콘텐츠 URL
    # url = 'https://cafe.bithumb.com/view/board-contents/1643752'
    url = 'https://cafe.bithumb.com/view/board-contents/1643696'
    content = get_content(url)

    content_renewal, msg, keywords = get_recap(content)
    
    export = pd.DataFrame({'index': ['summary', 'messages', 'keyword'], 'result': [content_renewal, msg, keywords]})
    export.to_excel('./result.xlsx', index=False)