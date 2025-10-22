import json
import os
import requests
import psycopg2
from typing import Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram бот для автоматического парсинга, перевода и модерации новостей
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
        
        if action == 'check_sources':
            return check_news_sources()
        elif action == 'add_source':
            return add_news_source(body_data)
        elif action == 'parse':
            return parse_and_translate_news(body_data)
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
                'message': 'Telegram News Bot with Auto-Check & Moderation',
                'endpoints': {
                    'POST /check_sources': 'Проверить источники новостей',
                    'POST /add_source': 'Добавить источник',
                    'POST /parse': 'Парсинг и перевод',
                    'POST /webhook': 'Telegram webhook'
                }
            }, ensure_ascii=False)
        }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }


def get_db_connection():
    dsn = os.environ.get('DATABASE_URL', '')
    if not dsn:
        raise Exception('DATABASE_URL не настроен')
    return psycopg2.connect(dsn)


def check_news_sources() -> Dict[str, Any]:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, url, selector_title, selector_text, selector_image, check_interval_minutes
            FROM news_sources
            WHERE is_active = true
            AND (last_checked_at IS NULL OR 
                 EXTRACT(EPOCH FROM (NOW() - last_checked_at))/60 >= check_interval_minutes)
        """)
        
        sources = cur.fetchall()
        processed_count = 0
        new_articles = []
        
        for source in sources:
            source_id, name, url, sel_title, sel_text, sel_image, interval = source
            
            try:
                articles = scrape_news_list(url, sel_title, sel_text, sel_image)
                
                for article in articles:
                    article_url = article.get('url')
                    
                    cur.execute("SELECT id FROM news_items WHERE url = %s", (article_url,))
                    existing = cur.fetchone()
                    
                    if not existing:
                        cur.execute("""
                            INSERT INTO news_items (url, title, original_text, image_url, status)
                            VALUES (%s, %s, %s, %s, 'new')
                            RETURNING id
                        """, (article_url, article.get('title'), article.get('text'), article.get('image')))
                        
                        news_id = cur.fetchone()[0]
                        conn.commit()
                        
                        send_to_moderator(news_id, article)
                        new_articles.append(article)
                        processed_count += 1
                
                cur.execute("UPDATE news_sources SET last_checked_at = NOW() WHERE id = %s", (source_id,))
                conn.commit()
            
            except Exception as e:
                print(f"Error checking source {name}: {e}")
                continue
        
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                'success': True,
                'sources_checked': len(sources),
                'new_articles': processed_count,
                'articles': new_articles
            }, ensure_ascii=False)
        }
    
    except Exception as e:
        return error_response(f'Ошибка проверки источников: {str(e)}', 500)


def scrape_news_list(url: str, sel_title: str, sel_text: str, sel_image: str) -> List[Dict[str, Any]]:
    response = requests.get(url, timeout=10, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    
    article_containers = soup.select('article, .news-item, .post, .article-item')[:5]
    
    for container in article_containers:
        try:
            link_tag = container.find('a', href=True)
            if not link_tag:
                continue
            
            article_url = urljoin(url, link_tag['href'])
            
            title_tag = container.select_one(sel_title) if sel_title else container.find(['h2', 'h3', 'h4'])
            title = title_tag.get_text(strip=True) if title_tag else ''
            
            text_tag = container.select_one(sel_text) if sel_text else container.find('p')
            text = text_tag.get_text(strip=True) if text_tag else ''
            
            image_tag = container.select_one(sel_image) if sel_image else container.find('img')
            image_url = ''
            if image_tag and image_tag.get('src'):
                image_url = urljoin(url, image_tag['src'])
            
            if title or text:
                articles.append({
                    'url': article_url,
                    'title': title,
                    'text': text,
                    'image': image_url
                })
        except:
            continue
    
    return articles


def send_to_moderator(news_id: int, article: Dict[str, Any]):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    moderator_chat_id = os.environ.get('MODERATOR_CHAT_ID', '')
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not bot_token or not moderator_chat_id or not openai_key:
        return
    
    try:
        title = article.get('title', '')
        text = article.get('text', '')[:1000]
        image_url = article.get('image', '')
        article_url = article.get('url', '')
        
        translated_title = translate_to_mari(title, openai_key) if title else ''
        translated_text = translate_to_mari(text, openai_key) if text else ''
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE news_items 
            SET translated_title = %s, translated_text = %s, status = 'pending_moderation'
            WHERE id = %s
        """, (translated_title, translated_text, news_id))
        conn.commit()
        cur.close()
        conn.close()
        
        message = f"📰 <b>Новая новость для модерации</b>\n\n"
        message += f"<b>Оригинал:</b>\n{title}\n\n"
        message += f"<b>Перевод:</b>\n{translated_title}\n\n"
        message += f"{translated_text[:300]}...\n\n"
        message += f"<a href='{article_url}'>Источник</a>"
        
        keyboard = {
            'inline_keyboard': [[
                {'text': '✅ Опубликовать', 'callback_data': f'approve_{news_id}'},
                {'text': '❌ Отклонить', 'callback_data': f'reject_{news_id}'}
            ]]
        }
        
        if image_url:
            try:
                requests.post(
                    f'https://api.telegram.org/bot{bot_token}/sendPhoto',
                    json={
                        'chat_id': moderator_chat_id,
                        'photo': image_url,
                        'caption': message,
                        'parse_mode': 'HTML',
                        'reply_markup': keyboard
                    },
                    timeout=10
                )
            except:
                requests.post(
                    f'https://api.telegram.org/bot{bot_token}/sendMessage',
                    json={
                        'chat_id': moderator_chat_id,
                        'text': message,
                        'parse_mode': 'HTML',
                        'reply_markup': keyboard,
                        'disable_web_page_preview': False
                    },
                    timeout=10
                )
        else:
            requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={
                    'chat_id': moderator_chat_id,
                    'text': message,
                    'parse_mode': 'HTML',
                    'reply_markup': keyboard,
                    'disable_web_page_preview': False
                },
                timeout=10
            )
    
    except Exception as e:
        print(f"Error sending to moderator: {e}")


def handle_telegram_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    callback_query = data.get('callback_query')
    
    if callback_query:
        callback_data = callback_query.get('data', '')
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']
        
        if callback_data.startswith('approve_'):
            news_id = int(callback_data.replace('approve_', ''))
            publish_approved_news(news_id, chat_id, message_id)
        
        elif callback_data.startswith('reject_'):
            news_id = int(callback_data.replace('reject_', ''))
            reject_news(news_id, chat_id, message_id)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'ok',
        'isBase64Encoded': False
    }


def publish_approved_news(news_id: int, moderator_chat_id: int, message_id: int):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    channel_id = os.environ.get('CHANNEL_ID', '')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT url, translated_title, translated_text, image_url
            FROM news_items WHERE id = %s
        """, (news_id,))
        
        result = cur.fetchone()
        if not result:
            return
        
        url, title, text, image_url = result
        
        message = f"<b>{title}</b>\n\n{text}\n\n<a href='{url}'>Источник</a>"
        
        if image_url and channel_id:
            requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendPhoto',
                json={
                    'chat_id': channel_id,
                    'photo': image_url,
                    'caption': message,
                    'parse_mode': 'HTML'
                }
            )
        elif channel_id:
            requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={
                    'chat_id': channel_id,
                    'text': message,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': False
                }
            )
        
        cur.execute("""
            UPDATE news_items 
            SET status = 'published', published_at = NOW()
            WHERE id = %s
        """, (news_id,))
        conn.commit()
        
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/editMessageReplyMarkup',
            json={
                'chat_id': moderator_chat_id,
                'message_id': message_id,
                'reply_markup': {'inline_keyboard': []}
            }
        )
        
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            json={
                'chat_id': moderator_chat_id,
                'text': '✅ Новость опубликована!'
            }
        )
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error publishing: {e}")


def reject_news(news_id: int, moderator_chat_id: int, message_id: int):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("UPDATE news_items SET status = 'rejected' WHERE id = %s", (news_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/editMessageReplyMarkup',
            json={
                'chat_id': moderator_chat_id,
                'message_id': message_id,
                'reply_markup': {'inline_keyboard': []}
            }
        )
        
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            json={
                'chat_id': moderator_chat_id,
                'text': '❌ Новость отклонена'
            }
        )
    
    except Exception as e:
        print(f"Error rejecting: {e}")


def add_news_source(data: Dict[str, Any]) -> Dict[str, Any]:
    name = data.get('name', '')
    url = data.get('url', '')
    interval = data.get('interval', 60)
    
    if not name or not url:
        return error_response('Укажите name и url', 400)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO news_sources (name, url, check_interval_minutes)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, url, interval))
        
        source_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({'success': True, 'source_id': source_id}, ensure_ascii=False)
        }
    
    except Exception as e:
        return error_response(f'Ошибка добавления источника: {str(e)}', 500)


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
        
        image_url = ''
        image_tag = soup.find('img')
        if image_tag and image_tag.get('src'):
            image_url = urljoin(url, image_tag['src'])
        
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
            return error_response('Не удалось извлечь текст', 400)
        
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
                    'text': article_text[:500] + '...',
                    'image': image_url,
                    'url': url
                },
                'translated': {
                    'title': translated_title,
                    'text': translated_text
                }
            }, ensure_ascii=False)
        }
    
    except Exception as e:
        return error_response(f'Ошибка: {str(e)}', 500)


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
