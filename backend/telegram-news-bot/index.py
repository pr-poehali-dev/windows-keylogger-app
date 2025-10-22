import json
import os
import requests
from typing import Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram bot для парсинга новостей, перевода на марийский и публикации
    Args: event с httpMethod, body, queryStringParameters; context с request_id
    Returns: HTTP response с результатом операции
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        body_data = json.loads(event.get('body', '{}'))
        action = body_data.get('action', 'parse')
        
        if action == 'parse':
            return parse_and_translate_news(body_data)
        elif action == 'publish':
            return publish_to_telegram(body_data)
        elif action == 'webhook':
            return handle_telegram_webhook(body_data)
    
    if method == 'GET':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                'status': 'ok',
                'message': 'Telegram News Bot API',
                'endpoints': {
                    'POST /parse': 'Парсинг и перевод новостей',
                    'POST /publish': 'Публикация в Telegram',
                    'POST /webhook': 'Webhook для Telegram'
                }
            }, ensure_ascii=False)
        }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }


def parse_and_translate_news(data: Dict[str, Any]) -> Dict[str, Any]:
    url = data.get('url', '')
    openai_api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not url:
        return error_response('URL не указан', 400)
    
    if not openai_api_key:
        return error_response('OPENAI_API_KEY не настроен', 500)
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        title = ''
        title_tag = soup.find('h1')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        article_selectors = [
            'article', '.article', '#article', '.post-content', 
            '.entry-content', '.news-content', 'main'
        ]
        
        article_text = ''
        for selector in article_selectors:
            if '.' in selector or '#' in selector:
                article = soup.select_one(selector)
            else:
                article = soup.find(selector)
            
            if article:
                paragraphs = article.find_all(['p', 'h2', 'h3'])
                article_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                break
        
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs[:10] if p.get_text(strip=True)])
        
        if not title and not article_text:
            return error_response('Не удалось извлечь текст со страницы', 400)
        
        full_text = f"{title}\n\n{article_text}" if title else article_text
        full_text = full_text[:4000]
        
        translated_title = translate_to_mari(title, openai_api_key) if title else ''
        translated_text = translate_to_mari(article_text[:3000], openai_api_key)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                'success': True,
                'original': {
                    'title': title,
                    'text': article_text[:500] + '...' if len(article_text) > 500 else article_text,
                    'url': url
                },
                'translated': {
                    'title': translated_title,
                    'text': translated_text
                },
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False)
        }
    
    except requests.RequestException as e:
        return error_response(f'Ошибка загрузки страницы: {str(e)}', 400)
    except Exception as e:
        return error_response(f'Ошибка обработки: {str(e)}', 500)


def translate_to_mari(text: str, api_key: str) -> str:
    if not text:
        return ''
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Ты профессиональный переводчик. Переводи текст с русского на марийский язык (луговой марийский). Сохраняй структуру и форматирование текста.'
                    },
                    {
                        'role': 'user',
                        'content': f'Переведи этот текст на марийский язык:\n\n{text}'
                    }
                ],
                'temperature': 0.3
            },
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        translated = result['choices'][0]['message']['content']
        return translated.strip()
    
    except Exception as e:
        return f'[Ошибка перевода: {str(e)}]'


def publish_to_telegram(data: Dict[str, Any]) -> Dict[str, Any]:
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    channel_id = data.get('channel_id', '')
    chat_id = data.get('chat_id', '')
    title = data.get('title', '')
    text = data.get('text', '')
    url = data.get('url', '')
    
    if not bot_token:
        return error_response('TELEGRAM_BOT_TOKEN не настроен', 500)
    
    if not (channel_id or chat_id):
        return error_response('Укажите channel_id или chat_id', 400)
    
    target = channel_id if channel_id else chat_id
    
    message = f"<b>{title}</b>\n\n{text}"
    if url:
        message += f'\n\n<a href="{url}">Источник</a>'
    
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            json={
                'chat_id': target,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            },
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('ok'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps({
                    'success': True,
                    'message_id': result['result']['message_id'],
                    'chat_id': result['result']['chat']['id']
                }, ensure_ascii=False)
            }
        else:
            return error_response(f"Telegram API error: {result.get('description')}", 400)
    
    except Exception as e:
        return error_response(f'Ошибка отправки в Telegram: {str(e)}', 500)


def handle_telegram_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    message = data.get('message', {})
    text = message.get('text', '')
    chat_id = message.get('chat', {}).get('id', '')
    
    if not text or not chat_id:
        return {'statusCode': 200, 'body': 'ok', 'isBase64Encoded': False}
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    
    if text.startswith('http'):
        try:
            requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={
                    'chat_id': chat_id,
                    'text': '🔄 Обрабатываю новость...'
                }
            )
            
            parse_result = parse_and_translate_news({'url': text})
            
            if parse_result['statusCode'] == 200:
                result_data = json.loads(parse_result['body'])
                translated = result_data['translated']
                
                publish_to_telegram({
                    'chat_id': chat_id,
                    'title': translated['title'],
                    'text': translated['text'],
                    'url': text
                })
            else:
                requests.post(
                    f'https://api.telegram.org/bot{bot_token}/sendMessage',
                    json={
                        'chat_id': chat_id,
                        'text': '❌ Не удалось обработать ссылку'
                    }
                )
        except:
            pass
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'ok',
        'isBase64Encoded': False
    }


def error_response(message: str, status_code: int) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'isBase64Encoded': False,
        'body': json.dumps({'error': message}, ensure_ascii=False)
    }
